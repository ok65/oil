
# Library imports
from typing import List, Dict

import numpy as np

# Project imports
from oil.core.instrument import Instrument
from oil.analyzers.markers import Marker


class N9030(Instrument):

    # SCIPI strings
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
        self._marker = {}
        for x in range(1, self._NUM_MARKERS+1):
            self._marker[x] = (N9030_Marker(parent=self, index=x))

    @property
    def marker(self) -> Dict:
        return self._marker

    @property
    def frequency_center(self) -> float:
        return float(self._query(f"{self._FREQ_CENT}"))

    @frequency_center.setter
    def frequency_center(self, value: float) -> None:
        self._command(f"{self._FREQ_CENT} {value:.0f}")

    @property
    def frequency_start(self) -> float:
        return float(self._query(f"{self._FREQ_START}"))

    @frequency_start.setter
    def frequency_start(self, value: float) -> None:
        self._command(f"{self._FREQ_START} {value}")

    @property
    def frequency_stop(self) -> float:
        return float(self._query(f"{self._FREQ_STOP}"))

    @frequency_stop.setter
    def frequency_stop(self, value: float) -> None:
        self._command(f"{self._FREQ_STOP} {value}")

    @property
    def frequency_span(self) -> float:
        return float(self._query(f"{self._FREQ_SPAN}"))

    @frequency_span.setter
    def frequency_span(self, value: float) -> None:
        self._command(f"{self._FREQ_SPAN} {value:.0f}")

    @property
    def frequency_points(self) -> int:
        return int(self._query(f"{self._FREQ_POINTS}"))

    @property
    def ref_level(self) -> float:
        return float(self._query(f"{self._REF_LEVEL}"))

    @ref_level.setter
    def ref_level(self, value: float) -> None:
        self._command(f"{self._REF_LEVEL} {value:.0f} dBm")

    @property
    def input_attenuation(self) -> float:
        atten = self._query(f"{self._ATTEN}")
        return 0 if atten == "AUTO" else atten

    @input_attenuation.setter
    def input_attenuation(self, value: float):
        self._command(f"{self._ATTEN} {value}")

    @property
    def bandwidth_setting(self) -> int:
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
        bw = f"RBW{value}" if value > 0 else "AUTO"
        self._command(f"{self._BW} {bw}")

    def download_trace(self, trace_id: int) -> Dict:
        """
        This pulls only Y data. For X, calculate the values by freq start/stop and number of points
        :param trace_id:
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

    def __init__(self, parent: Instrument, index: int):
        super().__init__(parent, index)

    def peak_search(self):
        self.parent._command(f"CALC:MARK{self.index}:MAX")

    @property
    def frequency(self) -> float:
        return float(self.parent._query(f"CALC:MARK{self.index}:X"))

    @frequency.setter
    def frequency(self, value: float):
        self.parent._command(f":CALC:MARK{self.index}:X {int(value)}")

    @property
    def power(self) -> float:
        return float(self.parent._query(f"CALC:MARK{self.index}:Y"))

    @power.setter
    def power(self, value: float):
        self.parent._command(f"CALC:MARK{self.index}:Y {value}")

    def next_peak_right(self):
        self.parent._command(f"CALC:MARK{self.index}:MAX:RIGH")

    def next_peak_left(self):
        self.parent._command(f"CALC:MARK{self.index}:MAX:LEFT")

    @property
    def enabled(self) -> bool:
        return (self.parent._query(f"CALC:MARK{self.index}:MODE")) == "POS"

    @enabled.setter
    def enabled(self, value: bool):
        mode = "POS" if value else "OFF"
        stat = "ON" if value else "OFF"
        self.parent._command(f"CALC:MARK{self.index}:STAT {stat}")
        self.parent._command(f"CALC:MARK{self.index}:MODE {mode}")