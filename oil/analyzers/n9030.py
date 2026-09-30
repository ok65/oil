
# Library imports
from typing import Any, Dict, List, Mapping, Optional

# Project imports
from oil.core.instrument import Instrument
from oil.core.virtual_instrument import VirtualInstrument
from oil.analyzers.markers import Marker


class N9030(Instrument):

    # SCPI strings
    _FREQ_CENT = "FREQ:CENT"
    _FREQ_START = "FREQ:STAR"
    _FREQ_STOP = "FREQ:STOP"
    _FREQ_SPAN = "FREQ:SPAN"
    _REF_LEVEL = "DISP:WIND1:TRAC:Y:RLEV"
    _ATTEN = "POW:RF:ATT"
    _BW = "BAND:RES"
    _PULL_DATA = ":TRAC:DATA? TRACE"
    _FREQ_POINTS = "SENS:SWE:POIN"
    _PEAKS = "CALC:DATA1:PEAKS"

    # Instrument parameters
    _NUM_MARKERS = 12

    def __init__(self, visa_string:str, config: Optional[Mapping[str, Any]] = None):
        super().__init__(visa_string, config=config)
        
        # Initialise list of markers (markers are 1-indexed)
        self._marker = {}
        for x in range(1, self._NUM_MARKERS+1):
            self._marker[x] = (N9030_Marker(parent=self, index=x))

    @property
    def marker(self) -> Dict:
        """ :return: Returns a dict of marker objects, acting like a 1-indexed list. See N9030_Marker class for info """
        return self._marker

    @property
    def frequency_center(self) -> float:
        """ :return: Returns the current center frequency in Hz """
        return float(self._query(f"{self._FREQ_CENT}"))

    @frequency_center.setter
    def frequency_center(self, value: float) -> None:
        """ :param value: Sets the current center frequency in Hz """
        self._command(f"{self._FREQ_CENT} {value:.0f}")

    @property
    def frequency_start(self) -> float:
        """ :return: Returns the current start frequency (left-most reticule) in Hz """
        return float(self._query(f"{self._FREQ_START}"))

    @frequency_start.setter
    def frequency_start(self, value: float) -> None:
        """ :param value: Sets the current start frequency in Hz (left-most reticule) """
        self._command(f"{self._FREQ_START} {value}")

    @property
    def frequency_stop(self) -> float:
        """ :return: Returns the current stop frequency (right-most reticule) in Hz """
        return float(self._query(f"{self._FREQ_STOP}"))

    @frequency_stop.setter
    def frequency_stop(self, value: float) -> None:
        """ :param value: Sets the current stop frequency in Hz (right-most reticule) """
        self._command(f"{self._FREQ_STOP} {value}")

    @property
    def frequency_span(self) -> float:
        """ :return: Returns the current frequency span in Hz (range acoss entire screen) """
        return float(self._query(f"{self._FREQ_SPAN}"))

    @frequency_span.setter
    def frequency_span(self, value: float) -> None:
        """ :param value: Sets the current frequency span in Hz (range across entire screen) """
        self._command(f"{self._FREQ_SPAN} {value:.0f}")

    @property
    def frequency_points(self) -> int:
        """ :return: Returns the number of frequency data points across X axis """
        return int(self._query(f"{self._FREQ_POINTS}"))

    @property
    def ref_level(self) -> float:
        """ :return: Returns the current power reference level in dBm (top-most reticle) """
        return float(self._query(f"{self._REF_LEVEL}"))

    @ref_level.setter
    def ref_level(self, value: float) -> None:
        """ :param value: Sets the current power reference level in dBm (top-most reticle) """
        self._command(f"{self._REF_LEVEL} {value:.0f} dBm")

    @property
    def input_attenuation(self) -> float:
        """ :return: Returns the current input power attenuation in dBm """
        atten = self._query(f"{self._ATTEN}")
        return 0 if atten == "AUTO" else float(atten)

    @input_attenuation.setter
    def input_attenuation(self, value: float):
        """ :param value: Sets the current input power attenuation in dBm (refer to user docs for acceptable values) """
        self._command(f"{self._ATTEN} {value}")

    @property
    def rbw(self) -> float:
        """Return the resolution bandwidth (RBW) in Hz."""
        result = self._query(self._BW)
        parts = result.split()
        value = float(parts[0])
        if len(parts) > 1 and parts[1].lower() == "khz":
            return value * 1_000
        return value

    @rbw.setter
    def rbw(self, value: float) -> None:
        """Set the resolution bandwidth (RBW) in Hz."""
        if value <= 0:
            raise ValueError("rbw must be positive, in Hz")
        self._command(f"{self._BW} {value:g} Hz")

    def download_trace(self, trace_id: int = 1) -> Dict:
        """
        This pulls trace data from the analyser, and returns a Dict of two lists, 'frequency' and 'power'.
        :param trace_id: id of trace to extract (default to trace 1)
        :return:
        """
        data = {}
        start = self.frequency_start
        stop = self.frequency_stop
        points = self.frequency_points
        step = (stop - start) / (points - 1) if points > 1 else 0

        data["frequency"] = [round((x*step)+start, 1) for x in range(points)]

        data_str = self._query(f"{self._PULL_DATA}{trace_id}", qm=False)
        data["power"] = self._parse_numeric_csv(data_str)
        return data

    def get_peaks_table(self, threshold: float = -200.0, excursion: float = 0.0,
              order: str = "AMPLitude", max_results: Optional[int] = None) -> List[Dict[str, float]]:
        """Return the active trace's peaks as amplitude/frequency rows."""
        if max_results is not None and max_results < 0:
            raise ValueError("max_results must be non-negative or None")
        order_map = {"amplitude": "AMPLitude", "frequency": "FREQuency", "time": "TIME"}
        try:
            scpi_order = order_map[order.lower()]
        except (AttributeError, KeyError) as error:
            raise ValueError("order must be 'amplitude', 'frequency', or 'time'") from error
        values = self._parse_numeric_csv(
            self._query(self._PEAKS, parameters=f"{threshold},{excursion},{scpi_order}")
        )
        count = int(values[0])
        rows = [{"amplitude": values[index], "frequency": values[index + 1]}
                for index in range(1, min(len(values), 1 + count * 2), 2)]
        return rows if max_results is None else rows[:max_results]

    peaks = get_peaks_table


class N9030_Marker(Marker):
    """
    Class to define Marker objects for N9030
    """
    def __init__(self, parent: Instrument, index: int):
        """
        Initialiser should be called in n9030 library code only.
        :param parent: Ref to parent n9030 instance
        :param index: Marker's own index number
        """
        super().__init__(parent, index)

    @property
    def frequency(self) -> float:
        """ :return: Return frequency in Hz of the current marker position """
        return float(self.parent._query(f"CALC:MARK{self.index}:X"))

    @frequency.setter
    def frequency(self, value: float):
        """ :param value: Set the current frequency in Hz (x axis) of this marker.
                          Setting values of screen will result in unpredictable power levels (y axis) """
        self.parent._command(f":CALC:MARK{self.index}:X {int(value)}")

    @property
    def power(self) -> float:
        """ :return: Return power level in dBm of the current marker position """
        return float(self.parent._query(f"CALC:MARK{self.index}:Y"))

    def peak_search(self):
        """ Move this marker to current peak (y axis) on the graph """
        self.parent._command(f"CALC:MARK{self.index}:MAX")

    def next_peak_right(self):
        """ Move this marker to the next peak (y axis) to the right of it's current position """
        self.parent._command(f"CALC:MARK{self.index}:MAX:RIGH")

    def next_peak_left(self):
        """ Move this marker to the next peak (y axis) to the left of it's current position """
        self.parent._command(f"CALC:MARK{self.index}:MAX:LEFT")

    @property
    def enabled(self) -> bool:
        """ :return: Enable status of this marker (default is false, disabled markers do not return good values) """
        return (self.parent._query(f"CALC:MARK{self.index}:MODE")) == "POS"

    @enabled.setter
    def enabled(self, value: bool):
        """ :param value: Enables/disables this marker (default is false, disabled markers do not return good values) """
        mode = "POS" if value else "OFF"
        stat = "ON" if value else "OFF"
        self.parent._command(f"CALC:MARK{self.index}:STAT {stat}")
        self.parent._command(f"CALC:MARK{self.index}:MODE {mode}")


class VirtualN9030(VirtualInstrument):
    """Stateful simulator for the N9030 commands implemented by ``N9030``."""

    IDENTIFICATION = "Keysight,VirtualN9030,0,0"

    _FREQ_CENT = "FREQ:CENT"
    _FREQ_START = "FREQ:STAR"
    _FREQ_STOP = "FREQ:STOP"
    _FREQ_SPAN = "FREQ:SPAN"
    _REF_LEVEL = "DISP:WIND1:TRAC:Y:RLEV"
    _ATTEN = "POW:RF:ATT"
    _BW = "BAND:RES"
    _FREQ_POINTS = "SENS:SWE:POIN"

    _FREQUENCY_CENTER_KEY = "frequency.center.hz"
    _FREQUENCY_START_KEY = "frequency.start.hz"
    _FREQUENCY_STOP_KEY = "frequency.stop.hz"
    _FREQUENCY_SPAN_KEY = "frequency.span.hz"
    _FREQUENCY_POINTS_KEY = "frequency.points"
    _REFERENCE_LEVEL_KEY = "display.reference_level.dbm"
    _INPUT_ATTENUATION_KEY = "input.attenuation.db"
    _BANDWIDTH_KEY = "bandwidth.selection"

    def __init__(self):
        super().__init__()
        self._set_defaults()

    def reset(self) -> None:
        super().reset()
        self._set_defaults()

    def handle_command(self, command: str) -> None:
        prefix, separator, value = command.partition(" ")
        if not separator:
            normalized = command.lstrip(":")
            if normalized.startswith("CALC:MARK") and normalized.endswith((":MAX", ":MAX:RIGH", ":MAX:LEFT")):
                marker_index = self._marker_index(normalized)
                self.write_memory(self._marker_key(marker_index, "last_search"), normalized.rsplit(":", 1)[1])
                return
            raise NotImplementedError(f"Unsupported N9030 command: {command}")

        numeric_keys = {
            self._FREQ_CENT: self._FREQUENCY_CENTER_KEY,
            self._FREQ_START: self._FREQUENCY_START_KEY,
            self._FREQ_STOP: self._FREQUENCY_STOP_KEY,
            self._FREQ_SPAN: self._FREQUENCY_SPAN_KEY,
            self._REF_LEVEL: self._REFERENCE_LEVEL_KEY,
        }
        if prefix in numeric_keys:
            self.write_memory(numeric_keys[prefix], float(value.split()[0]))
            return
        if prefix == self._ATTEN:
            attenuation = "AUTO" if value == "AUTO" else float(value)
            self.write_memory(self._INPUT_ATTENUATION_KEY, attenuation)
            return
        if prefix == self._BW:
            parts = value.split()
            if len(parts) not in (1, 2) or (len(parts) == 2 and parts[1].lower() not in ("hz", "khz")):
                raise ValueError(f"Invalid resolution bandwidth: {value}")
            bandwidth_hz = float(parts[0])
            if len(parts) == 2 and parts[1].lower() == "khz":
                bandwidth_hz *= 1_000
            if bandwidth_hz <= 0:
                raise ValueError(f"Invalid resolution bandwidth: {value}")
            self.write_memory(self._BANDWIDTH_KEY, bandwidth_hz)
            return

        normalized = prefix.lstrip(":")
        if normalized.startswith("CALC:MARK"):
            self._handle_marker_command(normalized, value)
            return
        raise NotImplementedError(f"Unsupported N9030 command: {command}")

    def handle_query(self, command: str) -> str:
        query_keys = {
            f"{self._FREQ_CENT}?": self._FREQUENCY_CENTER_KEY,
            f"{self._FREQ_START}?": self._FREQUENCY_START_KEY,
            f"{self._FREQ_STOP}?": self._FREQUENCY_STOP_KEY,
            f"{self._FREQ_SPAN}?": self._FREQUENCY_SPAN_KEY,
            f"{self._REF_LEVEL}?": self._REFERENCE_LEVEL_KEY,
            f"{self._FREQ_POINTS}?": self._FREQUENCY_POINTS_KEY,
            f"{self._BW}?": self._BANDWIDTH_KEY,
        }
        if command in query_keys:
            value = self.read_memory(query_keys[command])
            return f"{value} Hz" if command == f"{self._BW}?" else str(value)
        if command == f"{self._ATTEN}?":
            return str(self.read_memory(self._INPUT_ATTENUATION_KEY))
        if command.startswith(":TRAC:DATA? TRACE"):
            trace_id = self._parse_trace_id(command)
            self._ensure_trace(trace_id)
            return self._csv(self.read_memory(self._trace_key(trace_id)))
        if command.startswith("CALC:DATA1:PEAKS?"):
            return self.read_memory("peaks.csv", "0")

        normalized = command.lstrip(":")
        if normalized.startswith("CALC:MARK"):
            return self._handle_marker_query(normalized)
        raise NotImplementedError(f"Unsupported N9030 query: {command}")

    def _set_defaults(self) -> None:
        self.update_memory({
            self._FREQUENCY_CENTER_KEY: 1_500_000.0,
            self._FREQUENCY_START_KEY: 1_000_000.0,
            self._FREQUENCY_STOP_KEY: 2_000_000.0,
            self._FREQUENCY_SPAN_KEY: 1_000_000.0,
            self._FREQUENCY_POINTS_KEY: 3,
            self._REFERENCE_LEVEL_KEY: 0.0,
            self._INPUT_ATTENUATION_KEY: "AUTO",
            self._BANDWIDTH_KEY: 10_000.0,
            "peaks.csv": "3,-10.0,1000000.0,-20.0,1500000.0,-15.0,2000000.0",
        })
        self._ensure_trace(1)

    def _ensure_trace(self, trace_id: int) -> None:
        key = self._trace_key(trace_id)
        if key not in self.memory:
            self.write_memory(key, [-50.0, -40.0, -45.0])

    @staticmethod
    def _trace_key(trace_id: int) -> str:
        return f"trace.{trace_id}.power_data"

    @staticmethod
    def _marker_key(marker_index: int, value_name: str) -> str:
        return f"marker.{marker_index}.{value_name}"

    @staticmethod
    def _parse_trace_id(command: str) -> int:
        try:
            return int(command.removeprefix(":TRAC:DATA? TRACE"))
        except ValueError as error:
            raise NotImplementedError(f"Unsupported N9030 trace query: {command}") from error

    @staticmethod
    def _marker_index(command: str) -> int:
        marker = command.removeprefix("CALC:MARK").split(":", 1)[0]
        try:
            return int(marker)
        except ValueError as error:
            raise NotImplementedError(f"Unsupported N9030 marker command: {command}") from error

    def _handle_marker_command(self, command: str, value: str) -> None:
        marker_index = self._marker_index(command)
        if command.endswith(":X"):
            self.write_memory(self._marker_key(marker_index, "frequency"), float(value))
            return
        if command.endswith(":STAT") and value in ("ON", "OFF"):
            self.write_memory(self._marker_key(marker_index, "enabled"), value == "ON")
            return
        if command.endswith(":MODE") and value in ("POS", "OFF"):
            self.write_memory(self._marker_key(marker_index, "enabled"), value == "POS")
            return
        raise NotImplementedError(f"Unsupported N9030 marker command: {command} {value}")

    def _handle_marker_query(self, command: str) -> str:
        marker_index = self._marker_index(command)
        if command.endswith(":X?"):
            return str(self.read_memory(self._marker_key(marker_index, "frequency"), 0.0))
        if command.endswith(":Y?"):
            return str(self.read_memory(self._marker_key(marker_index, "power"), -50.0))
        if command.endswith(":MODE?"):
            return "POS" if self.read_memory(self._marker_key(marker_index, "enabled"), False) else "OFF"
        raise NotImplementedError(f"Unsupported N9030 marker query: {command}")

    @staticmethod
    def _csv(values: List[float]) -> str:
        return ",".join(str(value) for value in values)
