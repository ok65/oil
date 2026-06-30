

def serial_port_string(com_port: int) -> str:
    return f"ASRL{com_port}::INSTR"


def ip_address_string(ip_addr: str) -> str:
    return f"TCPIP::{ip_addr}::INSTR"