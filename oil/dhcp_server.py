"""Small, fixed-address DHCPv4 service for isolated instrument networks.

Run with ``python -m oil.dhcp_server instruments.local.yaml``. The service
answers only configured MAC addresses and has no dynamic address pool.
"""

import argparse
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import struct
import sys
from typing import Dict, Mapping, Tuple

import psutil
import yaml


_COOKIE = b"\x63\x82\x53\x63"
_DHCP_DISCOVER = 1
_DHCP_OFFER = 2
_DHCP_REQUEST = 3
_DHCP_ACK = 5
_DHCP_NAK = 6
_DHCP_MESSAGE_TYPE = 53
_DHCP_SERVER_ID = 54
_DHCP_REQUESTED_IP = 50
_DHCP_LEASE_TIME = 51
_DHCP_END = 255
_INFINITE_LEASE = 0xFFFFFFFF
_BOOTP_FIXED = struct.Struct("!BBBBIHH4s4s4s4s16s64s128s")


class DHCPServiceError(RuntimeError):
    """Raised for invalid DHCP configuration or service state."""


def _normalise_mac(value: str) -> bytes:
    try:
        mac = bytes.fromhex(value.replace(":", "").replace("-", ""))
    except (AttributeError, TypeError, ValueError) as error:
        raise DHCPServiceError(f"Invalid MAC address: {value!r}") from error
    if len(mac) != 6:
        raise DHCPServiceError(f"Invalid MAC address: {value!r}")
    return mac


def _load_config(filepath: str) -> Tuple[Mapping, Path]:
    path = Path(filepath).resolve()
    with path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, Mapping) or not isinstance(config.get("dhcp_server"), Mapping):
        raise DHCPServiceError("Config file must contain a 'dhcp_server' mapping")
    settings = config["dhcp_server"]
    if not isinstance(settings.get("interface"), str) or not settings["interface"].strip():
        raise DHCPServiceError("dhcp_server.interface must name one network interface")
    reservations = settings.get("reservations")
    if not isinstance(reservations, Mapping) or not reservations:
        raise DHCPServiceError("dhcp_server.reservations must map MAC addresses to IPv4 addresses")
    normalized = {}
    for mac_text, ip_text in reservations.items():
        mac = _normalise_mac(mac_text)
        try:
            address = ipaddress.IPv4Address(ip_text)
        except (ipaddress.AddressValueError, TypeError) as error:
            raise DHCPServiceError(f"Invalid reservation IP for {mac_text}: {ip_text!r}") from error
        if mac in normalized:
            raise DHCPServiceError(f"Duplicate MAC reservation: {mac_text}")
        normalized[mac] = address
    if len(set(normalized.values())) != len(normalized):
        raise DHCPServiceError("Each reserved IP address must be unique")
    return settings, path


def is_dhcp_server_running(config_file: str) -> bool:
    """Return whether the service launched for this config has a live PID."""
    _, path = _load_config(config_file)
    pid_path = path.with_suffix(path.suffix + ".dhcp.pid")
    try:
        record = json.loads(pid_path.read_text(encoding="utf-8"))
        pid = int(record["pid"])
        if record.get("config") != str(path):
            return False
        process = psutil.Process(pid)
        if not process.is_running():
            return False
        command = process.cmdline()
        if "oil.dhcp_server" not in command:
            return False
        configured_path = next((item for item in command if item.endswith((".yaml", ".yml"))), None)
        return configured_path is not None and Path(configured_path).resolve() == path
    except (OSError, ValueError, KeyError, TypeError, psutil.Error):
        return False


def _interface_ipv4(name: str) -> Tuple[str, str, int]:
    addresses = psutil.net_if_addrs().get(name)
    if not addresses:
        raise DHCPServiceError(f"Network interface not found: {name!r}")
    status = psutil.net_if_stats().get(name)
    if status is None or not status.isup:
        raise DHCPServiceError(f"Network interface is down: {name!r}")
    for address in addresses:
        if address.family == socket.AF_INET and address.address:
            if not address.netmask:
                raise DHCPServiceError(f"Network interface has no IPv4 netmask: {name!r}")
            index = socket.if_nametoindex(name)
            return address.address, address.netmask, index
    raise DHCPServiceError(f"Network interface has no IPv4 address: {name!r}")


def _parse_options(packet: bytes) -> Dict[int, bytes]:
    if len(packet) < _BOOTP_FIXED.size or packet[236:240] != _COOKIE:
        raise DHCPServiceError("Malformed DHCP packet")
    options = {}
    offset = 240
    while offset < len(packet):
        code = packet[offset]
        offset += 1
        if code == 0:
            continue
        if code == _DHCP_END:
            break
        if offset >= len(packet):
            raise DHCPServiceError("Malformed DHCP option")
        length = packet[offset]
        offset += 1
        end = offset + length
        if end > len(packet):
            raise DHCPServiceError("Malformed DHCP option length")
        options[code] = packet[offset:end]
        offset = end
    return options


def _build_reply(packet: bytes, message_type: int, offered_ip: str,
                 server_ip: str, subnet_mask: str, options: Mapping) -> bytes:
    fields = list(_BOOTP_FIXED.unpack(packet[:_BOOTP_FIXED.size]))
    fields[0] = 2  # BOOTREPLY
    fields[8] = socket.inet_aton(offered_ip)
    fields[9] = socket.inet_aton(server_ip)
    reply = bytearray(_BOOTP_FIXED.pack(*fields))
    reply.extend(_COOKIE)
    reply.extend(bytes((_DHCP_MESSAGE_TYPE, 1, message_type)))
    reply.extend(bytes((_DHCP_SERVER_ID, 4)))
    reply.extend(socket.inet_aton(server_ip))
    if message_type in (_DHCP_OFFER, _DHCP_ACK):
        reply.extend(bytes((_DHCP_LEASE_TIME, 4)))
        reply.extend(struct.pack("!I", _INFINITE_LEASE))
        reply.extend(bytes((1, 4)))
        reply.extend(socket.inet_aton(subnet_mask))
        for code, address in options.items():
            packed = b"".join(socket.inet_aton(str(ipaddress.IPv4Address(item))) for item in address)
            reply.extend(bytes((code, len(packed))))
            reply.extend(packed)
    reply.append(_DHCP_END)
    return bytes(reply)


def _serve(config_file: str) -> None:
    settings, config_path = _load_config(config_file)
    interface = settings["interface"]
    server_ip, subnet_mask, interface_index = _interface_ipv4(interface)
    network = ipaddress.IPv4Network(f"{server_ip}/{subnet_mask}", strict=False)
    reservations = {
        _normalise_mac(mac): ipaddress.IPv4Address(address)
        for mac, address in settings["reservations"].items()
    }
    for mac, address in reservations.items():
        if address not in network or address in (network.network_address, network.broadcast_address):
            raise DHCPServiceError(f"Reserved address {address} for {mac.hex(':')} is outside {network}")

    optional_options = {}
    if settings.get("router"):
        try:
            optional_options[3] = [ipaddress.IPv4Address(settings["router"])]
        except (ipaddress.AddressValueError, TypeError) as error:
            raise DHCPServiceError("dhcp_server.router must be an IPv4 address") from error
    if settings.get("dns"):
        dns_values = settings["dns"] if isinstance(settings["dns"], list) else [settings["dns"]]
        try:
            optional_options[6] = [ipaddress.IPv4Address(address) for address in dns_values]
        except ipaddress.AddressValueError as error:
            raise DHCPServiceError("dhcp_server.dns entries must be IPv4 addresses") from error
    port = int(settings.get("port", 67))
    if not 1 <= port <= 65535:
        raise DHCPServiceError("dhcp_server.port must be between 1 and 65535")
    pid_path = config_path.with_suffix(config_path.suffix + ".dhcp.pid")

    # Binding to the selected adapter's IPv4 address scopes broadcast reception
    # on Windows; on Linux, SO_BINDTODEVICE additionally pins the socket.
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.settimeout(1.0)
    if sys.platform.startswith("linux"):
        server.setsockopt(socket.SOL_SOCKET, getattr(socket, "SO_BINDTODEVICE", 25),
                          interface.encode() + b"\0")
        server.bind(("0.0.0.0", port))
    else:
        server.bind((server_ip, port))
    if os.name == "nt":
        # Windows defines IP_UNICAST_IF=31. Its DWORD value is network byte order.
        server.setsockopt(socket.IPPROTO_IP, getattr(socket, "IP_UNICAST_IF", 31),
                          struct.pack("!I", interface_index))

    pid_path.write_text(json.dumps({"pid": os.getpid(), "config": str(config_path)}),
                        encoding="utf-8")
    stop = False

    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_stop)
    try:
        while not stop:
            try:
                packet, _peer = server.recvfrom(4096)
            except socket.timeout:
                continue
            try:
                fields = _BOOTP_FIXED.unpack(packet[:_BOOTP_FIXED.size])
                if fields[0] != 1 or fields[1] != 1 or fields[2] != 6:
                    continue
                chaddr = fields[11][:6]
                ip = reservations.get(chaddr)
                if ip is None:
                    continue
                dhcp_options = _parse_options(packet)
                message = dhcp_options.get(_DHCP_MESSAGE_TYPE, b"\0")
                if len(message) != 1:
                    continue
                message_type = message[0]
                if message_type == _DHCP_DISCOVER:
                    reply_type = _DHCP_OFFER
                elif message_type == _DHCP_REQUEST:
                    requested = dhcp_options.get(_DHCP_REQUESTED_IP)
                    if dhcp_options.get(_DHCP_SERVER_ID) not in (None, socket.inet_aton(server_ip)):
                        continue
                    elif requested and requested != socket.inet_aton(str(ip)):
                        reply_type = _DHCP_NAK
                    else:
                        reply_type = _DHCP_ACK
                else:
                    continue

                reply_ip = str(ip) if reply_type == _DHCP_OFFER else "0.0.0.0"
                reply = _build_reply(packet, reply_type, reply_ip, server_ip,
                                     str(network.netmask), optional_options)
                broadcast = bool(fields[6] & 0x8000) or fields[7] == b"\0\0\0\0"
                destination_ip = "255.255.255.255" if broadcast else (
                    str(ip) if fields[7] == b"\0\0\0\0" else socket.inet_ntoa(fields[7])
                )
                destination = (destination_ip, 68)
                server.sendto(reply, destination)
            except (DHCPServiceError, IndexError, OSError, struct.error, ValueError):
                # Ignore malformed or unsupported client packets and keep serving.
                continue
    finally:
        server.close()
        try:
            pid_path.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed-reservation DHCPv4 service")
    parser.add_argument("config", help="YAML config containing dhcp_server settings")
    parser.add_argument("--status", action="store_true", help="report whether this config's service is running")
    args = parser.parse_args()
    try:
        args.config = str(Path(args.config).resolve())
        if args.status:
            running = is_dhcp_server_running(args.config)
            print("running" if running else "stopped")
            return 0 if running else 1
        if is_dhcp_server_running(args.config):
            raise DHCPServiceError("DHCP service is already running for this config")
        _serve(args.config)
    except (DHCPServiceError, OSError, ValueError) as error:
        print(f"DHCP service error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
