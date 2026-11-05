"""Rohde & Schwarz ZNB vector network analyzer driver."""

from typing import Any, Dict, List, Mapping, Optional

from oil.core.instrument import Instrument
from oil.analyzers.markers import Marker
from oil.core.virtual_instrument import VirtualInstrument


class ZNB(Instrument):
    """Driver for the R&S ZNB VNA, exposing the E5071C driver interface.

    Commands address channel 1. Trace-specific operations accept a trace
    number and map it to the ZNB trace name ``Trc<n>``. The legacy properties
    continue to operate on trace 1. ZNB returns stimulus values with
    ``CALC:DATA:STIM?`` and formatted values with ``CALC:DATA? FDAT``.
    """

    _FREQ_CENT = "SENS1:FREQ:CENT"
    _FREQ_START = "SENS1:FREQ:STAR"
    _FREQ_STOP = "SENS1:FREQ:STOP"
    _FREQ_SPAN = "SENS1:FREQ:SPAN"
    _FREQ_POINTS = "SENS1:SWE:POIN"
    _SWEEP_TYPE = "SENS1:SWE:TYPE"
    _IF_BW = "SENS1:BAND"
    _AVERAGE = "SENS1:AVER"
    _AVERAGE_COUNT = "SENS1:AVER:COUN"
    _AVERAGE_CLEAR = "SENS1:AVER:CLE"
    _SMOOTHING = "CALC1:SMO"
    _SMOOTHING_APERTURE = "CALC1:SMO:APER"
    _SOURCE_POWER = "SOUR1:POW"
    _PULL_X_DATA = "CALC1:DATA:STIM"
    _PULL_Y_DATA = "CALC1:DATA"
    _SCALE_PER_DIV = "DISP:WIND1:TRAC:Y:SCAL:PDIV"
    _REF_LEVEL = "DISP:WIND1:TRAC:Y:SCAL:RLEV"
    _REF_POSITION = "DISP:WIND1:TRAC:Y:SCAL:RPOS"
    _SOURCE_ATTENUATION = "SOUR1:POW:ATT"
    _SOURCE_ATTENUATION_AUTO = "SOUR1:POW:ATT:AUTO"
    _MEASUREMENT = "CALC1:PAR:MEAS"
    _TRACE_SELECT = "CALC1:PAR:SEL"
    _TRACE_DEFINE = "CALC1:PAR:SDEF"
    _TRACE_DELETE = "CALC1:PAR:DEL"
    _TRACE_CATALOG = "CALC1:PAR:CAT"
    _NUM_MARKERS = 10

    def __init__(self, visa_string: str, config: Optional[Mapping[str, Any]] = None):
        self._active_trace_id = 1
        super().__init__(visa_string, config=config)
        self._marker = {
            i: ZNB_Marker(self, i, trace_id=self._active_trace_id)
            for i in range(1, self._NUM_MARKERS + 1)
        }

    @property
    def marker(self) -> Dict:
        """Markers for the currently selected trace, indexed from 1."""
        return self._marker

    def markers_for_trace(self, trace_id: int) -> Dict:
        """Return marker objects bound to ``trace_id``."""
        self._validate_trace_id(trace_id)
        return {
            i: ZNB_Marker(self, i, trace_id=trace_id)
            for i in range(1, self._NUM_MARKERS + 1)
        }

    @property
    def trace_id(self) -> int:
        """Currently selected channel 1 trace number."""
        return self._active_trace_id

    @trace_id.setter
    def trace_id(self, value: int) -> None:
        self.select_trace(value)

    @staticmethod
    def _validate_trace_id(trace_id: int) -> None:
        if isinstance(trace_id, bool) or not isinstance(trace_id, int) or trace_id < 1:
            raise ValueError("trace_id must be a positive integer")

    @classmethod
    def _trace_name(cls, trace_id: int) -> str:
        cls._validate_trace_id(trace_id)
        return f"Trc{trace_id}"

    def select_trace(self, trace_id: int) -> None:
        """Select an existing trace as the active trace for channel 1."""
        self._command(f"{self._TRACE_SELECT} '{self._trace_name(trace_id)}'")
        self._remember_active_trace(trace_id)

    def _remember_active_trace(self, trace_id: int) -> None:
        self._active_trace_id = trace_id
        if hasattr(self, "_marker"):
            for marker in self._marker.values():
                marker.trace_id = trace_id

    def define_trace(self, trace_id: int, measurement: str) -> None:
        """Create trace ``Trc<trace_id>`` and assign its S-parameter."""
        value = self._validate_measurement(measurement)
        self._command(
            f"{self._TRACE_DEFINE} '{self._trace_name(trace_id)}','{value}'"
        )
        self._remember_active_trace(trace_id)

    def delete_trace(self, trace_id: int) -> None:
        """Delete a trace by its conventional ``Trc<n>`` name."""
        self._command(f"{self._TRACE_DELETE} '{self._trace_name(trace_id)}'")

    @property
    def traces(self) -> Dict[str, str]:
        """Return the channel 1 trace catalog as ``{name: measurement}``."""
        response = self._query(self._TRACE_CATALOG)
        fields = [field.strip().strip("'\"") for field in response.split(",")]
        if not response.strip():
            return {}
        if len(fields) % 2:
            raise ValueError(f"Unexpected ZNB trace catalog response: {response!r}")
        return {fields[i]: fields[i + 1] for i in range(0, len(fields), 2)}

    @staticmethod
    def _validate_measurement(value: str) -> str:
        value = value.upper()
        valid = {f"S{x}{y}" for x in range(1, 5) for y in range(1, 5)}
        if value not in valid:
            raise ValueError(f"Invalid measurement '{value}'. Expected S11-S44.")
        return value

    def _get_float(self, command: str) -> float:
        return float(self._query(command))

    def _set(self, command: str, value: Any) -> None:
        self._command(f"{command} {value}")

    @property
    def frequency_center(self) -> float:
        return self._get_float(self._FREQ_CENT)

    @frequency_center.setter
    def frequency_center(self, value: float) -> None:
        self._set(self._FREQ_CENT, value)

    @property
    def frequency_start(self) -> float:
        return self._get_float(self._FREQ_START)

    @frequency_start.setter
    def frequency_start(self, value: float) -> None:
        self._set(self._FREQ_START, value)

    @property
    def frequency_stop(self) -> float:
        return self._get_float(self._FREQ_STOP)

    @frequency_stop.setter
    def frequency_stop(self, value: float) -> None:
        self._set(self._FREQ_STOP, value)

    @property
    def frequency_span(self) -> float:
        return self._get_float(self._FREQ_SPAN)

    @frequency_span.setter
    def frequency_span(self, value: float) -> None:
        self._set(self._FREQ_SPAN, value)

    @property
    def frequency_points(self) -> int:
        return int(float(self._query(self._FREQ_POINTS)))

    @frequency_points.setter
    def frequency_points(self, value: int) -> None:
        self._set(self._FREQ_POINTS, value)

    @property
    def sweep_type(self) -> str:
        return self._query(self._SWEEP_TYPE).strip().upper()

    @sweep_type.setter
    def sweep_type(self, value: str) -> None:
        value = value.upper()
        if value not in {"LIN", "LOG"}:
            raise ValueError("sweep_type must be 'LIN' or 'LOG'")
        self._set(self._SWEEP_TYPE, value)

    @property
    def if_bandwidth(self) -> float:
        return self._get_float(self._IF_BW)

    @if_bandwidth.setter
    def if_bandwidth(self, value: float) -> None:
        if value <= 0:
            raise ValueError("if_bandwidth must be positive")
        self._set(self._IF_BW, value)

    @property
    def averaging_enabled(self) -> bool:
        return bool(int(self._query(self._AVERAGE)))

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool) -> None:
        self._set(self._AVERAGE, "ON" if value else "OFF")

    @property
    def averaging_count(self) -> int:
        return int(float(self._query(self._AVERAGE_COUNT)))

    @averaging_count.setter
    def averaging_count(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 999:
            raise ValueError("averaging_count must be an integer from 1 to 999")
        self._set(self._AVERAGE_COUNT, value)

    def restart_averaging(self) -> None:
        self._command(self._AVERAGE_CLEAR)

    @property
    def smoothing_enabled(self) -> bool:
        return self.get_smoothing_enabled()

    @smoothing_enabled.setter
    def smoothing_enabled(self, value: bool) -> None:
        self.set_smoothing_enabled(value)

    def get_smoothing_enabled(self, trace_id: int = 1) -> bool:
        self.select_trace(trace_id)
        return bool(int(self._query(self._SMOOTHING)))

    def set_smoothing_enabled(self, value: bool, trace_id: int = 1) -> None:
        self.select_trace(trace_id)
        self._set(self._SMOOTHING, "ON" if value else "OFF")

    @property
    def smoothing_aperture(self) -> float:
        return self.get_smoothing_aperture()

    @smoothing_aperture.setter
    def smoothing_aperture(self, value: float) -> None:
        self.set_smoothing_aperture(value)

    def get_smoothing_aperture(self, trace_id: int = 1) -> float:
        self.select_trace(trace_id)
        return self._get_float(self._SMOOTHING_APERTURE)

    def set_smoothing_aperture(self, value: float, trace_id: int = 1) -> None:
        if not 0.05 <= value <= 25:
            raise ValueError("smoothing_aperture must be between 0.05 and 25 percent")
        self.select_trace(trace_id)
        self._set(self._SMOOTHING_APERTURE, value)

    @property
    def source_power(self) -> float:
        return self._get_float(self._SOURCE_POWER)

    @source_power.setter
    def source_power(self, value: float) -> None:
        self._set(self._SOURCE_POWER, value)

    @property
    def reference_level(self) -> float:
        return self.get_reference_level()

    @reference_level.setter
    def reference_level(self, value: float) -> None:
        self.set_reference_level(value)

    def get_reference_level(self, trace_id: int = 1) -> float:
        trace_name = self._trace_name(trace_id)
        return float(self._query(self._REF_LEVEL, parameters=f"'{trace_name}'"))

    def set_reference_level(self, value: float, trace_id: int = 1) -> None:
        trace_name = self._trace_name(trace_id)
        self._command(f"{self._REF_LEVEL} {value},'{trace_name}'")

    @property
    def scale_per_division(self) -> float:
        return self.get_scale_per_division()

    @scale_per_division.setter
    def scale_per_division(self, value: float) -> None:
        self.set_scale_per_division(value)

    def get_scale_per_division(self, trace_id: int = 1) -> float:
        trace_name = self._trace_name(trace_id)
        return float(self._query(self._SCALE_PER_DIV, parameters=f"'{trace_name}'"))

    def set_scale_per_division(self, value: float, trace_id: int = 1) -> None:
        trace_name = self._trace_name(trace_id)
        self._command(f"{self._SCALE_PER_DIV} {value},'{trace_name}'")

    @property
    def reference_position(self) -> float:
        return self.get_reference_position()

    @reference_position.setter
    def reference_position(self, value: float) -> None:
        self.set_reference_position(value)

    def get_reference_position(self, trace_id: int = 1) -> float:
        trace_name = self._trace_name(trace_id)
        return float(self._query(self._REF_POSITION, parameters=f"'{trace_name}'"))

    def set_reference_position(self, value: float, trace_id: int = 1) -> None:
        trace_name = self._trace_name(trace_id)
        self._command(f"{self._REF_POSITION} {value},'{trace_name}'")

    @property
    def source_attenuation(self) -> float:
        return self._get_float(self._SOURCE_ATTENUATION)

    @source_attenuation.setter
    def source_attenuation(self, value: float) -> None:
        self._set(self._SOURCE_ATTENUATION, value)

    @property
    def source_attenuation_auto(self) -> bool:
        return bool(int(self._query(self._SOURCE_ATTENUATION_AUTO)))

    @source_attenuation_auto.setter
    def source_attenuation_auto(self, value: bool) -> None:
        self._set(self._SOURCE_ATTENUATION_AUTO, "ON" if value else "OFF")

    @property
    def measurement(self) -> str:
        return self.get_measurement()

    @measurement.setter
    def measurement(self, value: str) -> None:
        self.set_measurement(value)

    def get_measurement(self, trace_id: int = 1) -> str:
        trace_name = self._trace_name(trace_id)
        return self._query(
            self._MEASUREMENT, parameters=f"'{trace_name}'"
        ).strip().strip("'\"").upper()

    def set_measurement(self, value: str, trace_id: int = 1) -> None:
        value = self._validate_measurement(value)
        trace_name = self._trace_name(trace_id)
        self._command(f"{self._MEASUREMENT} '{trace_name}','{value}'")

    def download_trace(self, trace_id: int = 1) -> Dict:
        """Return frequency and currently formatted trace values."""
        # Select trace by the ZNB trace selection command before reading FDAT.
        self.select_trace(trace_id)
        x_data = self._query(self._PULL_X_DATA)
        y_data = self._query(self._PULL_Y_DATA, parameters="FDAT")
        return {
            "frequency": self._parse_numeric_csv(x_data),
            "level": self._parse_numeric_csv(y_data),
        }


class ZNB_Marker(Marker):
    """Marker API matching :class:`E5071C_Marker`."""

    def __init__(self, parent: ZNB, index: int, trace_id: int = 1):
        super().__init__(parent, index)
        parent._validate_trace_id(trace_id)
        self.trace_id = trace_id

    def _select_trace(self) -> None:
        self.parent.select_trace(self.trace_id)

    @property
    def frequency(self) -> float:
        self._select_trace()
        return float(self.parent._query(f"CALC1:MARK{self.index}:X"))

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._select_trace()
        self.parent._command(f"CALC1:MARK{self.index}:X {value}")

    @property
    def power(self) -> float:
        self._select_trace()
        return float(self.parent._query(f"CALC1:MARK{self.index}:Y").split(",")[0])

    def peak_search(self) -> None:
        self._select_trace()
        self.parent._command(f"CALC1:MARK{self.index}:FUNC:TYPE MAX")
        self.parent._command(f"CALC1:MARK{self.index}:FUNC:EXEC")

    @property
    def enabled(self) -> bool:
        self._select_trace()
        return bool(int(self.parent._query(f"CALC1:MARK{self.index}:STAT")))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._select_trace()
        self.parent._command(f"CALC1:MARK{self.index}:STAT {'ON' if value else 'OFF'}")


class VirtualZNB(VirtualInstrument):
    """Stateful simulator for the ZNB commands used by :class:`ZNB`."""

    IDENTIFICATION = "Rohde&Schwarz,VirtualZNB,0,0"

    def __init__(self, initial_memory: Optional[Mapping[str, Any]] = None):
        super().__init__()
        self._set_defaults()
        if initial_memory:
            self.update_memory(initial_memory)

    def reset(self) -> None:
        super().reset()
        self._set_defaults()

    def _set_defaults(self) -> None:
        self.update_memory({
            "frequency.center.hz": 1_500_000.0,
            "frequency.start.hz": 1_000_000.0,
            "frequency.stop.hz": 2_000_000.0,
            "frequency.span.hz": 1_000_000.0,
            "frequency.points": 3,
            "sweep.type": "LIN",
            "if_bandwidth.hz": 1000.0,
            "averaging.enabled": False,
            "averaging.count": 1,
            "smoothing.trace.1.enabled": False,
            "smoothing.trace.1.aperture.percent": 5.0,
            "source.power.dbm": -10.0,
            "display.trace.1.reference_level": 0.0,
            "display.trace.1.scale_per_division": 10.0,
            "display.trace.1.reference_position": 5.0,
            "source.attenuation.db": 0.0,
            "source.attenuation.auto": True,
            "trace.1.measurement": "S21",
            "measurement.parameter": "S21",
            "selected_trace": 1,
        })
        self._ensure_trace(1)

    @staticmethod
    def _trace_key(trace_id: int, field: str) -> str:
        return f"trace.{trace_id}.{field}"

    def _ensure_trace(self, trace_id: int) -> None:
        frequency_key = self._trace_key(trace_id, "frequency_data")
        if frequency_key not in self.memory:
            self.update_memory({
                frequency_key: [1_000_000.0, 1_500_000.0, 2_000_000.0],
                self._trace_key(trace_id, "formatted_data"): [-20.0, 0.0, -10.0],
                self._trace_key(trace_id, "measurement"): "S21",
                f"smoothing.trace.{trace_id}.enabled": False,
                f"smoothing.trace.{trace_id}.aperture.percent": 5.0,
                f"display.trace.{trace_id}.reference_level": 0.0,
                f"display.trace.{trace_id}.scale_per_division": 10.0,
                f"display.trace.{trace_id}.reference_position": 5.0,
            })

    def _marker_key(self, marker: int, field: str) -> str:
        return f"trace.{self.read_memory('selected_trace')}.marker.{marker}.{field}"

    @staticmethod
    def _trace_from_name(name: str) -> int:
        name = name.strip().strip("'\"")
        if not name.casefold().startswith("trc"):
            raise ValueError(f"Unknown ZNB trace name: {name}")
        try:
            return int(name[3:])
        except ValueError as error:
            raise ValueError(f"Unknown ZNB trace name: {name}") from error

    @classmethod
    def _trace_id_from_parameter(cls, parameter: str) -> int:
        if "," in parameter:
            parameter = parameter.rsplit(",", 1)[1]
        return cls._trace_from_name(parameter)

    def _selected_trace(self) -> int:
        return self.read_memory("selected_trace")

    def handle_command(self, command: str) -> None:
        if command == "SENS1:AVER:CLE":
            return
        if command.startswith(f"{ZNB._TRACE_SELECT} "):
            trace_id = self._trace_from_name(command.partition(" ")[2])
            self.write_memory("selected_trace", trace_id)
            self._ensure_trace(trace_id)
            return
        if command.startswith(f"{ZNB._TRACE_DEFINE} "):
            fields = command.partition(" ")[2].replace("'", "").split(",")
            if len(fields) != 2:
                raise ValueError(f"Invalid ZNB trace definition: {command}")
            trace_id = self._trace_from_name(fields[0])
            self._ensure_trace(trace_id)
            self.write_memory(self._trace_key(trace_id, "measurement"), fields[1].strip().upper())
            if trace_id == 1:
                self.write_memory("measurement.parameter", fields[1].strip().upper())
            self.write_memory("selected_trace", trace_id)
            return
        if command.startswith(f"{ZNB._MEASUREMENT} "):
            fields = command.partition(" ")[2].replace("'", "").split(",")
            if len(fields) != 2:
                raise ValueError(f"Invalid ZNB measurement assignment: {command}")
            trace_id = self._trace_from_name(fields[0])
            self._ensure_trace(trace_id)
            self.write_memory(self._trace_key(trace_id, "measurement"), fields[1].strip().upper())
            if trace_id == 1:
                self.write_memory("measurement.parameter", fields[1].strip().upper())
            return
        if command.startswith(f"{ZNB._TRACE_DELETE} "):
            trace_id = self._trace_from_name(command.partition(" ")[2])
            for field in ("frequency_data", "formatted_data", "measurement"):
                self.memory.pop(self._trace_key(trace_id, field), None)
            for key in list(self.memory):
                if key.startswith(f"smoothing.trace.{trace_id}.") or key.startswith(f"display.trace.{trace_id}."):
                    self.memory.pop(key, None)
            return
        if command.startswith("CALC1:MARK"):
            self._handle_marker_command(command)
            return

        command_map = {
            ZNB._FREQ_CENT: ("frequency.center.hz", float),
            ZNB._FREQ_START: ("frequency.start.hz", float),
            ZNB._FREQ_STOP: ("frequency.stop.hz", float),
            ZNB._FREQ_SPAN: ("frequency.span.hz", float),
            ZNB._FREQ_POINTS: ("frequency.points", int),
            ZNB._IF_BW: ("if_bandwidth.hz", float),
            ZNB._AVERAGE_COUNT: ("averaging.count", int),
            ZNB._SOURCE_POWER: ("source.power.dbm", float),
            ZNB._SOURCE_ATTENUATION: ("source.attenuation.db", float),
        }
        prefix, separator, value = command.partition(" ")
        if not separator:
            raise NotImplementedError(f"Unsupported virtual ZNB command: {command}")
        if prefix in command_map:
            key, converter = command_map[prefix]
            self.write_memory(key, converter(value))
            return
        display_fields = {
            ZNB._REF_LEVEL: "reference_level",
            ZNB._SCALE_PER_DIV: "scale_per_division",
            ZNB._REF_POSITION: "reference_position",
        }
        if prefix in display_fields:
            value_text, _, trace_parameter = value.partition(",")
            trace_id = self._trace_id_from_parameter(trace_parameter)
            self._ensure_trace(trace_id)
            self.write_memory(
                f"display.trace.{trace_id}.{display_fields[prefix]}", float(value_text)
            )
            return
        bool_map = {
            ZNB._AVERAGE: "averaging.enabled",
            ZNB._SOURCE_ATTENUATION_AUTO: "source.attenuation.auto",
        }
        if prefix in bool_map and value.upper() in {"ON", "OFF", "1", "0"}:
            self.write_memory(bool_map[prefix], value.upper() in {"ON", "1"})
            return
        if prefix == ZNB._SMOOTHING and value.upper() in {"ON", "OFF", "1", "0"}:
            self.write_memory(
                f"smoothing.trace.{self._selected_trace()}.enabled",
                value.upper() in {"ON", "1"},
            )
            return
        if prefix == ZNB._SMOOTHING_APERTURE:
            self.write_memory(
                f"smoothing.trace.{self._selected_trace()}.aperture.percent",
                float(value),
            )
            return
        if prefix == ZNB._SWEEP_TYPE:
            self.write_memory("sweep.type", value.upper())
            return
        raise NotImplementedError(f"Unsupported virtual ZNB command: {command}")

    def handle_query(self, command: str) -> str:
        if command == "CALC1:DATA:STIM?":
            return self._csv(self.read_memory(self._trace_key(self.read_memory("selected_trace"), "frequency_data")))
        if command == "CALC1:DATA? FDAT":
            return self._csv(self.read_memory(self._trace_key(self.read_memory("selected_trace"), "formatted_data")))
        if command.startswith(f"{ZNB._TRACE_CATALOG}?"):
            entries = []
            for key in sorted(self.memory):
                if key.startswith("trace.") and key.endswith(".measurement"):
                    trace_id = int(key.split(".")[1])
                    entries.extend((f"'Trc{trace_id}'", f"'{self.read_memory(key)}'"))
            return ",".join(entries)
        if command.startswith(f"{ZNB._MEASUREMENT}?"):
            trace_id = self._trace_id_from_parameter(command.split("?", 1)[1])
            self._ensure_trace(trace_id)
            return self.read_memory(self._trace_key(trace_id, "measurement"))
        if command.startswith("CALC1:MARK"):
            return self._handle_marker_query(command)

        query_map = {
            f"{ZNB._FREQ_CENT}?": ("frequency.center.hz", float),
            f"{ZNB._FREQ_START}?": ("frequency.start.hz", float),
            f"{ZNB._FREQ_STOP}?": ("frequency.stop.hz", float),
            f"{ZNB._FREQ_SPAN}?": ("frequency.span.hz", float),
            f"{ZNB._FREQ_POINTS}?": ("frequency.points", int),
            f"{ZNB._SWEEP_TYPE}?": ("sweep.type", str),
            f"{ZNB._IF_BW}?": ("if_bandwidth.hz", float),
            f"{ZNB._AVERAGE}?": ("averaging.enabled", bool),
            f"{ZNB._AVERAGE_COUNT}?": ("averaging.count", int),
            f"{ZNB._SOURCE_POWER}?": ("source.power.dbm", float),
            f"{ZNB._SOURCE_ATTENUATION}?": ("source.attenuation.db", float),
        }
        if command in query_map:
            key, converter = query_map[command]
            value = self.read_memory(key)
            if converter is bool:
                return "1" if value else "0"
            return str(value)
        if command.startswith(f"{ZNB._SMOOTHING}?"):
            return "1" if self.read_memory(f"smoothing.trace.{self._selected_trace()}.enabled") else "0"
        if command.startswith(f"{ZNB._SMOOTHING_APERTURE}?"):
            return str(self.read_memory(f"smoothing.trace.{self._selected_trace()}.aperture.percent"))
        for scpi, field in (
            (ZNB._REF_LEVEL, "reference_level"),
            (ZNB._SCALE_PER_DIV, "scale_per_division"),
            (ZNB._REF_POSITION, "reference_position"),
        ):
            if command.startswith(f"{scpi}?"):
                trace_id = self._trace_id_from_parameter(command.split("?", 1)[1])
                self._ensure_trace(trace_id)
                return str(self.read_memory(f"display.trace.{trace_id}.{field}"))
        if command == f"{ZNB._SOURCE_ATTENUATION_AUTO}?":
            return "1" if self.read_memory("source.attenuation.auto") else "0"
        raise NotImplementedError(f"Unsupported virtual ZNB query: {command}")

    def _handle_marker_command(self, command: str) -> None:
        head, _, value = command.partition(" ")
        try:
            index = int(head.removeprefix("CALC1:MARK").split(":", 1)[0])
        except ValueError as error:
            raise NotImplementedError(f"Unsupported virtual ZNB marker command: {command}") from error
        if head.endswith(":X"):
            self.write_memory(self._marker_key(index, "frequency"), float(value))
        elif head.endswith(":STAT") and value.upper() in {"ON", "OFF"}:
            self.write_memory(self._marker_key(index, "enabled"), value.upper() == "ON")
        elif head.endswith(":FUNC:TYPE") and value.upper() == "MAX":
            return
        elif head.endswith(":FUNC:EXEC"):
            self._move_marker_to_peak(index)
        else:
            raise NotImplementedError(f"Unsupported virtual ZNB marker command: {command}")

    def _handle_marker_query(self, command: str) -> str:
        try:
            index = int(command.removeprefix("CALC1:MARK").split(":", 1)[0])
        except ValueError as error:
            raise NotImplementedError(f"Unsupported virtual ZNB marker query: {command}") from error
        if command.endswith(":X?"):
            return str(self.read_memory(self._marker_key(index, "frequency"), 0.0))
        if command.endswith(":Y?"):
            return str(self.read_memory(self._marker_key(index, "power"), 0.0))
        if command.endswith(":STAT?"):
            return "1" if self.read_memory(self._marker_key(index, "enabled"), False) else "0"
        raise NotImplementedError(f"Unsupported virtual ZNB marker query: {command}")

    def _move_marker_to_peak(self, marker: int) -> None:
        trace = self.read_memory("selected_trace")
        frequencies: List[float] = self.read_memory(self._trace_key(trace, "frequency_data"))
        levels: List[float] = self.read_memory(self._trace_key(trace, "formatted_data"))
        if not frequencies or len(frequencies) != len(levels):
            raise ValueError("Virtual ZNB trace data has incompatible frequency and level lengths.")
        peak = max(range(len(levels)), key=levels.__getitem__)
        self.update_memory({
            self._marker_key(marker, "frequency"): frequencies[peak],
            self._marker_key(marker, "power"): levels[peak],
        })

    @staticmethod
    def _csv(values: List[float]) -> str:
        return ",".join(str(value) for value in values)


__all__ = ["ZNB", "ZNB_Marker", "VirtualZNB"]

