# Library imports
from typing import Dict, List

# Project imports
from oil.core.instrument import Instrument
from oil.core.virtual_instrument import VirtualInstrument
from oil.analyzers.markers import Marker


class E5071C(Instrument):
    """
    Driver for the Keysight/Agilent E5071C ENA Vector Network Analyser.

    Most commands operate on channel 1 by default. The trace download
    returns the currently formatted trace data, so the Y values correspond
    to the display format selected on the instrument.
    """

    # SCPI strings
    _FREQ_CENT = "SENS1:FREQ:CENT"
    _FREQ_START = "SENS1:FREQ:STAR"
    _FREQ_STOP = "SENS1:FREQ:STOP"
    _FREQ_SPAN = "SENS1:FREQ:SPAN"
    _FREQ_POINTS = "SENS1:SWE:POIN"

    _IF_BW = "SENS1:BAND"
    _SOURCE_POWER = "SOUR1:POW"

    _PULL_X_DATA = "CALC1:DATA:XAX"
    _PULL_Y_DATA = "CALC1:DATA:FDAT"

    _SCALE_PER_DIV = "DISP:WIND1:TRAC1:Y:SCAL:PDIV"
    _REF_LEVEL = "DISP:WIND1:TRAC1:Y:SCAL:RLEV"
    _REF_POSITION = "DISP:WIND1:TRAC1:Y:SCAL:RPOS"

    _SOURCE_ATTENUATION = "SOUR1:POW:ATT"
    _SOURCE_ATTENUATION_AUTO = "SOUR1:POW:ATT:AUTO"

    _MEASUREMENT = "CALC1:PAR1:DEF"

    # Instrument parameters
    _NUM_MARKERS = 9

    def __init__(self, visa_string: str):

        # This vna gets funny, and needs raw socket
        if visa_string.endswith("::INSTR"):
            visa_string = visa_string[:-5] + "5025::SOCKET"

        super().__init__(visa_string)

        # Markers are 1-indexed.
        self._marker = {
            x: E5071C_Marker(parent=self, index=x)
            for x in range(1, self._NUM_MARKERS + 1)
        }

    @property
    def marker(self) -> Dict:
        """
        :return: Returns a dict of marker objects, acting like a 1-indexed list.
        """
        return self._marker

    @property
    def frequency_center(self) -> float:
        """ :return: Returns the current center frequency in Hz """
        return float(self._query(self._FREQ_CENT))

    @frequency_center.setter
    def frequency_center(self, value: float) -> None:
        """ :param value: Sets the current center frequency in Hz """
        self._command(f"{self._FREQ_CENT} {value}")

    @property
    def frequency_start(self) -> float:
        """ :return: Returns the current start frequency in Hz """
        return float(self._query(self._FREQ_START))

    @frequency_start.setter
    def frequency_start(self, value: float) -> None:
        """ :param value: Sets the current start frequency in Hz """
        self._command(f"{self._FREQ_START} {value}")

    @property
    def frequency_stop(self) -> float:
        """ :return: Returns the current stop frequency in Hz """
        return float(self._query(self._FREQ_STOP))

    @frequency_stop.setter
    def frequency_stop(self, value: float) -> None:
        """ :param value: Sets the current stop frequency in Hz """
        self._command(f"{self._FREQ_STOP} {value}")

    @property
    def frequency_span(self) -> float:
        """ :return: Returns the current frequency span in Hz """
        return float(self._query(self._FREQ_SPAN))

    @frequency_span.setter
    def frequency_span(self, value: float) -> None:
        """ :param value: Sets the current frequency span in Hz """
        self._command(f"{self._FREQ_SPAN} {value}")

    @property
    def frequency_points(self) -> int:
        """ :return: Returns the number of sweep points """
        return int(float(self._query(self._FREQ_POINTS)))

    @frequency_points.setter
    def frequency_points(self, value: int) -> None:
        """ :param value: Sets the number of sweep points """
        self._command(f"{self._FREQ_POINTS} {value}")

    @property
    def source_power(self) -> float:
        """ :return: Returns the current source power in dBm """
        return float(self._query(self._SOURCE_POWER))

    @source_power.setter
    def source_power(self, value: float) -> None:
        """ :param value: Sets the current source power in dBm """
        self._command(f"{self._SOURCE_POWER} {value}")

    @property
    def reference_level(self) -> float:
        """
        :return: Y-axis reference level for trace 1.
        """
        return float(self._query(self._REF_LEVEL))

    @reference_level.setter
    def reference_level(self, value: float) -> None:
        """
        :param value: Set Y-axis reference level for trace 1.
        """
        self._command(f"{self._REF_LEVEL} {value}")

    @property
    def scale_per_division(self) -> float:
        """
        :return: Y-axis scale per division for trace 1.
        """
        return float(self._query(self._SCALE_PER_DIV))

    @scale_per_division.setter
    def scale_per_division(self, value: float) -> None:
        """
        :param value: Set Y-axis scale per division for trace 1.
        """
        self._command(f"{self._SCALE_PER_DIV} {value}")

    @property
    def reference_position(self) -> float:
        """
        :return: Reference-line position in divisions.
        """
        return float(self._query(self._REF_POSITION))

    @reference_position.setter
    def reference_position(self, value: float) -> None:
        """
        :param value: Set reference-line position in divisions.
        """
        self._command(f"{self._REF_POSITION} {value}")

    @property
    def source_attenuation(self) -> float:
        """ :return: Source attenuation in dB """
        return float(self._query(self._SOURCE_ATTENUATION))

    @source_attenuation.setter
    def source_attenuation(self, value: float) -> None:
        """ :param value: Set source attenuation in dB """
        self._command(f"{self._SOURCE_ATTENUATION} {value}")

    @property
    def source_attenuation_auto(self) -> bool:
        """ :return: True if automatic source power ranging is enabled """
        return bool(int(self._query(self._SOURCE_ATTENUATION_AUTO)))

    @source_attenuation_auto.setter
    def source_attenuation_auto(self, value: bool) -> None:
        """ :param value: Enable/disable automatic source power ranging """
        state = "ON" if value else "OFF"
        self._command(f"{self._SOURCE_ATTENUATION_AUTO} {state}")

    @property
    def measurement(self) -> str:
        """
        :return: Measurement parameter for trace 1, e.g. S11, S21, S22.
        """
        return self._query(self._MEASUREMENT).strip()

    @measurement.setter
    def measurement(self, value: str) -> None:
        """
        :param value: S-parameter to measure, e.g. S11, S21, S22.
        """
        value = value.upper()

        valid_parameters = {
            f"S{x}{y}"
            for x in range(1, 5)
            for y in range(1, 5)
        }

        if value not in valid_parameters:
            raise ValueError(
                f"Invalid measurement '{value}'. "
                f"Expected S11-S44."
            )

        self._command(f"{self._MEASUREMENT} {value}")

    def download_trace(self, trace_id: int = 1) -> Dict:
        """
        Pull the currently formatted trace data from the analyser.

        The returned Y data corresponds to the current trace display format.
        For example, a trace configured for Log Mag will return values in dB.

        :param trace_id: Trace number to download.
        :return: Dict containing 'frequency' and 'power' lists.
        """

        # Select requested trace on channel 1.
        self._command(f"CALC1:PAR{trace_id}:SEL")

        data = {}

        # Pull the actual X-axis values from the analyser. This also supports
        # non-uniform/segmented sweeps.
        x_data = self._query(self._PULL_X_DATA, qm=True)
        data["frequency"] = [float(d) for d in x_data.split(",")]

        # FDAT returns two values per sweep point. For normal rectangular
        # formats the first is the displayed value and the second is zero.
        y_data = self._query(self._PULL_Y_DATA, qm=True)
        y_values = [float(d) for d in y_data.split(",")]

        data["level"] = y_values[::2]

        return data


class VirtualE5071C(VirtualInstrument):
    """Stateful simulator for the E5071C commands implemented by ``E5071C``."""

    IDENTIFICATION = "Keysight,VirtualE5071C,0,0"

    _FREQ_CENT = "SENS1:FREQ:CENT"
    _FREQ_START = "SENS1:FREQ:STAR"
    _FREQ_STOP = "SENS1:FREQ:STOP"
    _FREQ_SPAN = "SENS1:FREQ:SPAN"
    _FREQ_POINTS = "SENS1:SWE:POIN"
    _SOURCE_POWER = "SOUR1:POW"
    _PULL_X_DATA = "CALC1:DATA:XAX"
    _PULL_Y_DATA = "CALC1:DATA:FDAT"
    _SCALE_PER_DIV = "DISP:WIND1:TRAC1:Y:SCAL:PDIV"
    _REF_LEVEL = "DISP:WIND1:TRAC1:Y:SCAL:RLEV"
    _REF_POSITION = "DISP:WIND1:TRAC1:Y:SCAL:RPOS"
    _SOURCE_ATTENUATION = "SOUR1:POW:ATT"
    _SOURCE_ATTENUATION_AUTO = "SOUR1:POW:ATT:AUTO"
    _MEASUREMENT = "CALC1:PAR1:DEF"

    _FREQUENCY_CENTER_KEY = "frequency.center.hz"
    _FREQUENCY_START_KEY = "frequency.start.hz"
    _FREQUENCY_STOP_KEY = "frequency.stop.hz"
    _FREQUENCY_SPAN_KEY = "frequency.span.hz"
    _FREQUENCY_POINTS_KEY = "frequency.points"
    _SOURCE_POWER_KEY = "source.power.dbm"
    _REFERENCE_LEVEL_KEY = "display.trace.1.reference_level"
    _SCALE_PER_DIVISION_KEY = "display.trace.1.scale_per_division"
    _REFERENCE_POSITION_KEY = "display.trace.1.reference_position"
    _SOURCE_ATTENUATION_KEY = "source.attenuation.db"
    _SOURCE_ATTENUATION_AUTO_KEY = "source.attenuation.auto"
    _MEASUREMENT_KEY = "measurement.parameter"
    _SELECTED_TRACE_KEY = "selected_trace"

    def __init__(self):
        super().__init__()
        self._set_defaults()

    def reset(self) -> None:
        super().reset()
        self._set_defaults()

    def handle_command(self, command: str) -> None:
        if command.startswith("CALC1:PAR") and command.endswith(":SEL"):
            trace_id = self._parse_trace_selection(command)
            self.write_memory(self._SELECTED_TRACE_KEY, trace_id)
            self._ensure_trace(trace_id)
            return
        if command.startswith("CALC1:MARK") and " " not in command:
            self._handle_marker_command(command, "")
            return

        prefix, separator, value = command.partition(" ")
        if not separator:
            raise NotImplementedError(f"Unsupported E5071C command: {command}")

        numeric_keys = {
            self._FREQ_CENT: self._FREQUENCY_CENTER_KEY,
            self._FREQ_START: self._FREQUENCY_START_KEY,
            self._FREQ_STOP: self._FREQUENCY_STOP_KEY,
            self._FREQ_SPAN: self._FREQUENCY_SPAN_KEY,
            self._FREQ_POINTS: self._FREQUENCY_POINTS_KEY,
            self._SOURCE_POWER: self._SOURCE_POWER_KEY,
            self._REF_LEVEL: self._REFERENCE_LEVEL_KEY,
            self._SCALE_PER_DIV: self._SCALE_PER_DIVISION_KEY,
            self._REF_POSITION: self._REFERENCE_POSITION_KEY,
            self._SOURCE_ATTENUATION: self._SOURCE_ATTENUATION_KEY,
        }
        if prefix in numeric_keys:
            number = float(value)
            self.write_memory(
                numeric_keys[prefix],
                int(number) if prefix == self._FREQ_POINTS else number,
            )
            return
        if prefix == self._SOURCE_ATTENUATION_AUTO and value in ("ON", "OFF"):
            self.write_memory(self._SOURCE_ATTENUATION_AUTO_KEY, value == "ON")
            return
        if prefix == self._MEASUREMENT:
            self.write_memory(self._MEASUREMENT_KEY, value)
            return
        if prefix.startswith("CALC1:MARK"):
            self._handle_marker_command(prefix, value)
            return
        raise NotImplementedError(f"Unsupported E5071C command: {command}")

    def handle_query(self, command: str) -> str:
        query_keys = {
            f"{self._FREQ_CENT}?": self._FREQUENCY_CENTER_KEY,
            f"{self._FREQ_START}?": self._FREQUENCY_START_KEY,
            f"{self._FREQ_STOP}?": self._FREQUENCY_STOP_KEY,
            f"{self._FREQ_SPAN}?": self._FREQUENCY_SPAN_KEY,
            f"{self._FREQ_POINTS}?": self._FREQUENCY_POINTS_KEY,
            f"{self._SOURCE_POWER}?": self._SOURCE_POWER_KEY,
            f"{self._REF_LEVEL}?": self._REFERENCE_LEVEL_KEY,
            f"{self._SCALE_PER_DIV}?": self._SCALE_PER_DIVISION_KEY,
            f"{self._REF_POSITION}?": self._REFERENCE_POSITION_KEY,
            f"{self._SOURCE_ATTENUATION}?": self._SOURCE_ATTENUATION_KEY,
            f"{self._MEASUREMENT}?": self._MEASUREMENT_KEY,
        }
        if command in query_keys:
            return str(self.read_memory(query_keys[command]))
        if command == f"{self._SOURCE_ATTENUATION_AUTO}?":
            return "1" if self.read_memory(self._SOURCE_ATTENUATION_AUTO_KEY) else "0"
        if command == f"{self._PULL_X_DATA}?":
            return self._csv(self.read_memory(self._trace_key(self._selected_trace(), "frequency_data")))
        if command == f"{self._PULL_Y_DATA}?":
            return self._csv(self.read_memory(self._trace_key(self._selected_trace(), "formatted_data")))
        if command.startswith("CALC1:MARK"):
            return self._handle_marker_query(command)
        raise NotImplementedError(f"Unsupported E5071C query: {command}")

    def _set_defaults(self) -> None:
        self.update_memory({
            self._FREQUENCY_CENTER_KEY: 1_500_000.0,
            self._FREQUENCY_START_KEY: 1_000_000.0,
            self._FREQUENCY_STOP_KEY: 2_000_000.0,
            self._FREQUENCY_SPAN_KEY: 1_000_000.0,
            self._FREQUENCY_POINTS_KEY: 3,
            self._SOURCE_POWER_KEY: -10.0,
            self._REFERENCE_LEVEL_KEY: 0.0,
            self._SCALE_PER_DIVISION_KEY: 10.0,
            self._REFERENCE_POSITION_KEY: 5.0,
            self._SOURCE_ATTENUATION_KEY: 0.0,
            self._SOURCE_ATTENUATION_AUTO_KEY: True,
            self._MEASUREMENT_KEY: "S21",
            self._SELECTED_TRACE_KEY: 1,
        })
        self._ensure_trace(1)

    def _ensure_trace(self, trace_id: int) -> None:
        frequency_key = self._trace_key(trace_id, "frequency_data")
        if frequency_key not in self.memory:
            self.update_memory({
                frequency_key: [1_000_000.0, 1_500_000.0, 2_000_000.0],
                self._trace_key(trace_id, "formatted_data"): [-20.0, 0.0, -10.0, 0.0, -15.0, 0.0],
            })

    def _selected_trace(self) -> int:
        return self.read_memory(self._SELECTED_TRACE_KEY)

    @staticmethod
    def _trace_key(trace_id: int, value_name: str) -> str:
        return f"trace.{trace_id}.{value_name}"

    def _marker_key(self, marker_index: int, value_name: str) -> str:
        return f"trace.{self._selected_trace()}.marker.{marker_index}.{value_name}"

    def _parse_trace_selection(self, command: str) -> int:
        trace = command.removeprefix("CALC1:PAR").removesuffix(":SEL")
        try:
            return int(trace)
        except ValueError as error:
            raise NotImplementedError(f"Unsupported E5071C command: {command}") from error

    def _marker_index(self, command: str) -> int:
        marker = command.removeprefix("CALC1:MARK").split(":", 1)[0]
        try:
            return int(marker)
        except ValueError as error:
            raise NotImplementedError(f"Unsupported E5071C marker command: {command}") from error

    def _handle_marker_command(self, prefix: str, value: str) -> None:
        marker_index = self._marker_index(prefix)
        if prefix.endswith(":X"):
            self.write_memory(self._marker_key(marker_index, "frequency"), float(value))
            return
        if prefix.endswith(":STAT") and value in ("ON", "OFF"):
            self.write_memory(self._marker_key(marker_index, "enabled"), value == "ON")
            return
        if prefix.endswith(":FUNC:TYPE") and value == "MAX":
            return
        if prefix.endswith(":FUNC:EXEC"):
            self._move_marker_to_peak(marker_index)
            return
        raise NotImplementedError(f"Unsupported E5071C marker command: {prefix} {value}")

    def _handle_marker_query(self, command: str) -> str:
        marker_index = self._marker_index(command)
        if command.endswith(":X?"):
            return str(self.read_memory(self._marker_key(marker_index, "frequency"), 0.0))
        if command.endswith(":Y?"):
            return str(self.read_memory(self._marker_key(marker_index, "power"), 0.0))
        if command.endswith(":STAT?"):
            return "1" if self.read_memory(self._marker_key(marker_index, "enabled"), False) else "0"
        raise NotImplementedError(f"Unsupported E5071C marker query: {command}")

    def _move_marker_to_peak(self, marker_index: int) -> None:
        frequencies: List[float] = self.read_memory(self._trace_key(self._selected_trace(), "frequency_data"))
        formatted_data: List[float] = self.read_memory(self._trace_key(self._selected_trace(), "formatted_data"))
        levels = formatted_data[::2]
        if not frequencies or len(frequencies) != len(levels):
            raise ValueError("Virtual E5071C trace data has incompatible frequency and level lengths.")
        peak_index = max(range(len(levels)), key=levels.__getitem__)
        self.update_memory({
            self._marker_key(marker_index, "frequency"): frequencies[peak_index],
            self._marker_key(marker_index, "power"): levels[peak_index],
        })

    @staticmethod
    def _csv(values: List[float]) -> str:
        return ",".join(str(value) for value in values)


class E5071C_Marker(Marker):
    """
    Marker object for the E5071C.

    Marker commands operate on the currently selected trace of channel 1.
    """

    def __init__(self, parent: Instrument, index: int):
        """
        Initialiser should be called by E5071C only.

        :param parent: Reference to parent E5071C instance
        :param index: Marker's own index number
        """

        super().__init__(parent, index)

    @property
    def frequency(self) -> float:
        """ :return: Return stimulus frequency in Hz of this marker """
        return float(
            self.parent._query(f"CALC1:MARK{self.index}:X")
        )

    @frequency.setter
    def frequency(self, value: float):
        """ :param value: Set marker stimulus frequency in Hz """
        self.parent._command(
            f"CALC1:MARK{self.index}:X {value}"
        )

    @property
    def power(self) -> float:
        """
        :return: Return the primary formatted Y-axis value at this marker.

        Despite the property name 'power', this follows the convention used
        by the analyser Marker class. On a VNA this value is determined by
        the selected trace format, e.g. dB for Log Mag.
        """

        result = self.parent._query(
            f"CALC1:MARK{self.index}:Y"
        )

        # E5071C marker Y queries may return primary and secondary values.
        # For normal rectangular formats we want the primary value.
        return float(result.split(",")[0])

    def peak_search(self):
        """ Move this marker to the maximum point on the current trace """
        self.parent._command(
            f"CALC1:MARK{self.index}:FUNC:TYPE MAX"
        )
        self.parent._command(
            f"CALC1:MARK{self.index}:FUNC:EXEC"
        )

    @property
    def enabled(self) -> bool:
        """ :return: Enable status of this marker """
        return bool(
            int(self.parent._query(f"CALC1:MARK{self.index}:STAT"))
        )

    @enabled.setter
    def enabled(self, value: bool):
        """ :param value: Enables/disables this marker """
        state = "ON" if value else "OFF"
        self.parent._command(
            f"CALC1:MARK{self.index}:STAT {state}"
        )
