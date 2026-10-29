"""Shared fixtures for driver tests that run without physical instruments."""

import pytest

import oil.core.instrument as instrument_module
from oil.analyzers import (
    E5071C, VirtualE5071C, N9030, VirtualN9030, TinyVNA, VirtualTinyVNA,
)
from oil.sig_gens import SMR20, VirtualSMR20
from oil.switches import RFSwitchMatrix, VirtualRFSwitchMatrix


class VirtualResourceManager:
    """Minimal ResourceManager replacement that returns one virtual device."""

    def __init__(self, resource):
        self.resource = resource
        self.opened_addresses = []

    def open_resource(self, address):
        self.opened_addresses.append(address)
        return self.resource


@pytest.fixture
def virtual_rf_switch():
    return VirtualRFSwitchMatrix()


@pytest.fixture
def rf_switch_driver(monkeypatch, virtual_rf_switch):
    """Connect the real driver to its virtual device through fake PyVISA."""
    resource_manager = VirtualResourceManager(virtual_rf_switch)
    monkeypatch.setattr(
        instrument_module.pyvisa,
        "ResourceManager",
        lambda backend: resource_manager,
    )

    driver = RFSwitchMatrix("TCPIP::127.0.0.1::INSTR")
    return driver, virtual_rf_switch, resource_manager


def _connect_driver(monkeypatch, driver_type, virtual_instrument, visa_string):
    resource_manager = VirtualResourceManager(virtual_instrument)
    monkeypatch.setattr(
        instrument_module.pyvisa,
        "ResourceManager",
        lambda backend: resource_manager,
    )
    return driver_type(visa_string), resource_manager


@pytest.fixture
def smr20_driver(monkeypatch):
    virtual_instrument = VirtualSMR20()
    driver, resource_manager = _connect_driver(
        monkeypatch, SMR20, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager


@pytest.fixture
def e5071c_driver(monkeypatch):
    virtual_instrument = VirtualE5071C()
    driver, resource_manager = _connect_driver(
        monkeypatch, E5071C, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager


@pytest.fixture
def n9030_driver(monkeypatch):
    virtual_instrument = VirtualN9030()
    driver, resource_manager = _connect_driver(
        monkeypatch, N9030, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager


class VirtualSerialPort:
    """Serial-port adapter that exposes a VirtualInstrument shell as bytes."""

    def __init__(self, virtual_instrument, **_kwargs):
        self.virtual_instrument = virtual_instrument
        self.is_open = True
        self._response = bytearray()

    def reset_input_buffer(self):
        self._response.clear()

    def write(self, data):
        command = data.decode("ascii").rstrip("\r")
        if command in ("info", "sweep", "power", "bandwidth") or command.startswith("scan "):
            result = self.virtual_instrument.query(command)
        else:
            self.virtual_instrument.write(command)
            result = ""
        response = f"{command}\r\n"
        if result:
            response += f"{result}\r\n"
        self._response.extend((response + "ch> ").encode("ascii"))
        return len(data)

    def flush(self):
        pass

    def read(self, size=1):
        result = bytes(self._response[:size])
        del self._response[:size]
        return result

    def close(self):
        self.is_open = False


@pytest.fixture
def tinyvna_driver(monkeypatch):
    virtual_instrument = VirtualTinyVNA()
    serial_port = VirtualSerialPort(virtual_instrument)
    monkeypatch.setattr(
        instrument_module.serial,
        "Serial",
        lambda **kwargs: serial_port,
    )
    driver = TinyVNA("COM7")
    return driver, virtual_instrument, serial_port
