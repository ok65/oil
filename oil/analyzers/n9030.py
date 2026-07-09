
# Library imports
from typing import Dict

# Project imports
from oil.core.instrument import Instrument
from oil.analyzers.markers import Marker


class N9030(Instrument):

    # SCPI strings
    _FREQ_CENT = "FREQ:CENT"
    _FREQ_START = "FREQ:STAR"
    _FREQ_STOP = "FREQ:STOP"
    _FREQ_SPAN = "FREQ:SPAN"
    _REF_LEVEL = "DISP:WIND1:TRAC:Y:RLEV"
    _ATTEN = "POW:RF:ATT"
    _BW = "BAND:SEL"
    _PULL_DATA = ":TRAC:DATA? TRACE"
    _FREQ_POINTS = "SENS:SWE:POIN"

    # Instrument parameters
    _NUM_MARKERS = 12

    def __init__(self, visa_string:str):
        super().__init__(visa_string)
        
        # Initialise list of markers (markers are 1-indexed)
        self._marker = []
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
        return 0 if atten == "AUTO" else atten

    @input_attenuation.setter
    def input_attenuation(self, value: float):
        """ :param value: Sets the current input power attenuation in dBm (refer to user docs for acceptable values) """
        self._command(f"{self._ATTEN} {value}")

    @property
    def bandwidth_setting(self) -> int:
        """ :return: Returns the current setting of the resolution bandwidth auto setting. The output
                     corresponds to the RBWn setting, as defined in the user manuals. A value of 0 refers
                     to AUTO.
                     This setting it used to set the way RBW is defined (as a product of the frequency)
                     rather than setting an absolute value. Default is auto.
         """
        result = self._query(f"{self._BW}")
        if "RBW1" in result:
            return 1
        if "RBW2" in result:
            return 2
        if "RBW3" in result:
            return 3
        if "RBW4" in result:
            return 4
        if "RBW5" in result:
            return 5
        if "RBW6" in result:
            return 6
        if "AUTO" in result:
            return 0
        raise Exception()

    @bandwidth_setting.setter
    def bandwidth_setting(self, value: int) -> None:
        """ :param value: Sets the current setting of the resolution bandwidth auto setting. The output
                          corresponds to the RBWn setting, as defined in the user manuals. A value of 0 refers
                          to AUTO.
                          This setting it used to set the way RBW is defined (as a product of the frequency)
                          rather than setting an absolute value. Default is auto.
         """
        bw = f"RBW{value}" if value > 0 else "AUTO"
        self._command(f"{self._BW} {bw}")

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
        step = (stop - start)/points

        data["frequency"] = [round((x*step)+start, 1) for x in range(points)]

        data_str = self._query(f"{self._PULL_DATA}{trace_id}", qm=False)
        data["power"] = [float(d) for d in data_str.split(",")]
        return data


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