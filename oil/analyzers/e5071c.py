# Library imports
from typing import Dict

# Project imports
from oil.core.instrument import Instrument
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

        data["power"] = y_values[::2]

        return data


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
