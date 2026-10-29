"""NanoVNA-H serial-shell driver and virtual instrument."""

import math
import re
from typing import Any, Callable, Dict, List, Mapping, Optional

from oil.core.instrument import InstrumentSerial
from oil.core.virtual_instrument import VirtualInstrument


class TinyVNA(InstrumentSerial):
    """Driver for NanoVNA-H using its USB virtual COM text command shell.

    The sweep configuration is held locally and sent when ``download_trace``
    runs. Output power and bandwidth settings are read from and written to the
    instrument. Power is a discrete Si5351 drive code, not dBm.
    """

    _MAX_POINTS = 101
    _MAX_BANDWIDTH_INDEX = 511
    _SWEEP_POINTS_KEY = "frequency.points"
    _FREQUENCY_START_KEY = "frequency.start.hz"
    _FREQUENCY_STOP_KEY = "frequency.stop.hz"
    _S11_KEY = "trace.s11"
    _S21_KEY = "trace.s21"

    def __init__(self, port: str, baudrate: int = 115200,
                 timeout: float = 15.0,
                 log_func: Optional[Callable[[str], None]] = None,
                 config: Optional[Mapping[str, Any]] = None):
        super().__init__(port, baudrate=baudrate, timeout=timeout,
                         log_func=log_func)
        self._frequency_start, self._frequency_stop, self._frequency_points = (
            self._parse_sweep_settings(self._serial_command("sweep"))
        )
        if config is not None:
            self.apply_config(config)

    def identify(self) -> str:
        """Return the board and firmware information reported by ``info``."""
        return self._serial_command("info")

    def command(self, command: str) -> str:
        """Send one raw NanoVNA-H shell command and return its text response."""
        return self._serial_command(command)

    @property
    def frequency_start(self) -> float:
        """Start frequency in Hz; applied to the device on the next scan."""
        return self._frequency_start

    @frequency_start.setter
    def frequency_start(self, value: float) -> None:
        value = self._validate_frequency(value, "frequency_start")
        self._frequency_start = value

    @property
    def frequency_stop(self) -> float:
        """Stop frequency in Hz; applied to the device on the next scan."""
        return self._frequency_stop

    @frequency_stop.setter
    def frequency_stop(self, value: float) -> None:
        value = self._validate_frequency(value, "frequency_stop")
        self._frequency_stop = value

    @property
    def frequency_points(self) -> int:
        """Number of points in the next scan (NanoVNA-H limit: 101)."""
        return self._frequency_points

    @frequency_points.setter
    def frequency_points(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("frequency_points must be an integer")
        if not 2 <= value <= self._MAX_POINTS:
            raise ValueError(
                f"frequency_points must be between 2 and {self._MAX_POINTS}"
            )
        self._frequency_points = value

    @property
    def output_power(self) -> int:
        """Return the output drive code (0–3, or 255 for automatic)."""
        response = self._serial_command("power")
        match = re.search(r"power:\s*(\d+)", response, re.IGNORECASE)
        if not match:
            raise ValueError(f"Unexpected NanoVNA-H power response: {response!r}")
        return int(match.group(1))

    @output_power.setter
    def output_power(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("output_power must be an integer drive code")
        if value not in (0, 1, 2, 3, 255):
            raise ValueError("output_power must be 0–3 or 255 (automatic)")
        self._serial_command(f"power {value}")

    @property
    def bandwidth(self) -> int:
        """Return the firmware bandwidth selection index (0–511)."""
        response = self._serial_command("bandwidth")
        match = re.search(r"bandwidth\s+(\d+)\s+\((\d+)\s*Hz\)",
                          response, re.IGNORECASE)
        if not match:
            raise ValueError(f"Unexpected NanoVNA-H bandwidth response: {response!r}")
        return int(match.group(1))

    @bandwidth.setter
    def bandwidth(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("bandwidth must be an integer firmware selection index")
        if not 0 <= value <= self._MAX_BANDWIDTH_INDEX:
            raise ValueError(
                f"bandwidth must be between 0 and {self._MAX_BANDWIDTH_INDEX}"
            )
        self._serial_command(f"bandwidth {value}")

    @property
    def bandwidth_hz(self) -> int:
        """Return the actual measurement bandwidth reported by the firmware."""
        response = self._serial_command("bandwidth")
        match = re.search(r"bandwidth\s+\d+\s+\((\d+)\s*Hz\)",
                          response, re.IGNORECASE)
        if not match:
            raise ValueError(f"Unexpected NanoVNA-H bandwidth response: {response!r}")
        return int(match.group(1))

    def download_trace(self, trace_id: int = 1) -> Dict[str, List[Any]]:
        """Run the configured sweep and return one complex S-parameter trace.

        Trace 1 is S11 and trace 2 is S21. The returned dictionary contains
        ``frequency`` and the corresponding S-parameter array.
        """
        measurements = {1: "S11", 2: "S21"}
        if isinstance(trace_id, bool) or trace_id not in measurements:
            raise ValueError("trace_id must be 1 (S11) or 2 (S21)")
        result = self._scan()
        parameter = measurements[trace_id]
        return {"frequency": result["frequency"], parameter: result[parameter]}

    def _scan(self) -> Dict[str, List[Any]]:
        """Run a scan using locally configured range and point count."""
        if self._frequency_stop <= self._frequency_start:
            raise ValueError("frequency_stop must be greater than frequency_start")

        response = self._serial_command(
            f"scan {self._frequency_start:.0f} {self._frequency_stop:.0f} "
            f"{self._frequency_points} 7"
        )
        rows = []
        for line in response.splitlines():
            fields = line.split()
            if not fields:
                continue
            if len(fields) != 5:
                raise ValueError(f"Unexpected NanoVNA-H scan response line: {line!r}")
            try:
                frequency, s11_real, s11_imag, s21_real, s21_imag = map(float, fields)
            except ValueError as error:
                raise ValueError(f"NanoVNA-H rejected scan: {line.strip()}") from error
            rows.append((frequency, complex(s11_real, s11_imag),
                         complex(s21_real, s21_imag)))

        if len(rows) != self._frequency_points:
            raise ValueError(
                f"NanoVNA-H returned {len(rows)} scan points; "
                f"expected {self._frequency_points}"
            )
        return {
            "frequency": [row[0] for row in rows],
            "S11": [row[1] for row in rows],
            "S21": [row[2] for row in rows],
        }

    @staticmethod
    def _validate_frequency(value: float, name: str) -> float:
        try:
            frequency = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a positive frequency in Hz") from error
        if not math.isfinite(frequency) or frequency <= 0:
            raise ValueError(f"{name} must be a positive frequency in Hz")
        return frequency

    @classmethod
    def _parse_sweep_settings(cls, response: str):
        fields = response.split()
        if len(fields) != 3:
            raise ValueError(f"Unexpected NanoVNA-H sweep response: {response!r}")
        try:
            start, stop = float(fields[0]), float(fields[1])
            points = int(fields[2])
        except ValueError as error:
            raise ValueError(f"Unexpected NanoVNA-H sweep response: {response!r}") from error
        if (not math.isfinite(start) or not math.isfinite(stop) or start <= 0
                or stop <= start or not 2 <= points <= cls._MAX_POINTS):
            raise ValueError(f"Invalid NanoVNA-H sweep settings: {response!r}")
        return start, stop, points


class VirtualTinyVNA(VirtualInstrument):
    """Stateful virtual NanoVNA-H shell used by the driver tests."""

    IDENTIFICATION = "NanoVNA-H,Virtual,1,0"

    def __init__(self, initial_memory: Optional[Mapping[str, Any]] = None):
        super().__init__()
        self.update_memory({
            TinyVNA._FREQUENCY_START_KEY: 1_000_000.0,
            TinyVNA._FREQUENCY_STOP_KEY: 100_000_000.0,
            TinyVNA._SWEEP_POINTS_KEY: 101,
            "output.power.code": 255,
            "bandwidth.index": 0,
            "bandwidth.hz": 4000,
            TinyVNA._S11_KEY: complex(0.5, 0.1),
            TinyVNA._S21_KEY: complex(0.2, -0.1),
        })
        if initial_memory:
            self.update_memory(initial_memory)

    def handle_command(self, command: str) -> None:
        name, _, arguments = command.partition(" ")
        if name == "sweep":
            fields = arguments.split()
            if len(fields) == 3:
                self.write_memory(TinyVNA._FREQUENCY_START_KEY, float(fields[0]))
                self.write_memory(TinyVNA._FREQUENCY_STOP_KEY, float(fields[1]))
                self.write_memory(TinyVNA._SWEEP_POINTS_KEY, int(fields[2]))
                return
        elif name == "power":
            self.write_memory("output.power.code", int(arguments))
            return
        elif name == "bandwidth":
            self.write_memory("bandwidth.index", int(arguments))
            self.write_memory("bandwidth.hz", int(4000 / (int(arguments) + 1)))
            return
        raise NotImplementedError(f"Unsupported virtual NanoVNA-H command: {command}")

    def handle_query(self, command: str) -> str:
        if command == "info":
            return "Board: NanoVNA-H\nVersion: Virtual"
        if command == "sweep":
            return "{} {} {}".format(
                self.read_memory(TinyVNA._FREQUENCY_START_KEY),
                self.read_memory(TinyVNA._FREQUENCY_STOP_KEY),
                self.read_memory(TinyVNA._SWEEP_POINTS_KEY),
            )
        if command == "power":
            return f"power: {self.read_memory('output.power.code')}"
        if command == "bandwidth":
            return "bandwidth {} ({}Hz)".format(
                self.read_memory("bandwidth.index"),
                self.read_memory("bandwidth.hz"),
            )
        if command.startswith("scan "):
            fields = command.split()
            start, stop, points = float(fields[1]), float(fields[2]), int(fields[3])
            if points < 2 or points > TinyVNA._MAX_POINTS:
                return "sweep points exceeds range"
            s11 = self.read_memory(TinyVNA._S11_KEY)
            s21 = self.read_memory(TinyVNA._S21_KEY)
            frequencies = [start + (stop - start) * i / (points - 1)
                           for i in range(points)]
            return "\n".join(
                f"{frequency:.0f} {s11.real} {s11.imag} {s21.real} {s21.imag}"
                for frequency in frequencies
            )
        raise NotImplementedError(f"Unsupported virtual NanoVNA-H query: {command}")


__all__ = ["TinyVNA", "VirtualTinyVNA"]
