
import matplotlib.pyplot as plt


def serial_port_string(com_port: int) -> str:
    return f"ASRL{com_port}::INSTR"


def ip_address_string(ip_addr: str) -> str:
    return f"TCPIP0::{ip_addr}::INSTR"


def plot_trace(trace_data: dict) -> None:
    """
    Plot trace data returned by an instrument.

    Expected format:
        {
            "frequency": [...],
            "<measurement>": [...]
        }
    """
    frequency = trace_data["frequency"]

    value_keys = [key for key in trace_data if key != "frequency"]
    if len(value_keys) != 1:
        raise ValueError("Trace data must contain frequency and exactly one measurement field")

    value_name = value_keys[0]
    values = trace_data[value_name]

    if len(frequency) != len(values):
        raise ValueError("Frequency and measurement arrays must have the same length")

    plt.figure(figsize=(10, 6))
    plt.plot(frequency, values)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel(value_name.title())
    plt.title("Instrument Trace")
    plt.grid(True)
    plt.tight_layout()
    plt.show()