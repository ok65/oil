
# Library imports

# Project imports
from oil.core.instrument import Instrument


class SMR20(Instrument):

    # SCIPI strings
    _FREQ = "FREQ"
    _POWER = "POW"
    _RFON = "OUTP1:PON"
    _EXTREF = "ROSC:SOUR"

    def __init__(self):
        super().__init__()

    @property
    def frequency(self) -> float:
        return float(self._query(f"{self._FREQ}"))

    @frequency.setter
    def frequency(self, value: float) -> None:
        self._command(f"{self._FREQ} {value:.0f}")

    @property
    def power(self) -> float:
        return float(self._query(f"{self._POWER}"))

    @power.setter
    def power(self, value: float) -> None:
        self._command(f"{self._POWER} {value} dBM")

    @property
    def rf_enable(self) -> bool:
        return (self._query(f"{self._RFON}")) == "ON"

    @rf_enable.setter
    def rf_enable(self, value: bool) -> None:
        onoff = "ON" if value else "OFF"
        self._command(f"{self._RFON} {onoff}")

    @property
    def external_reference(self) -> bool:
        return (self._query(self._EXTREF)) == "EXT"

    @external_reference.setter
    def external_reference(self, value: bool) -> None:
        ext_in = "EXT" if value else "INT"
        self._command(f"{self._RFON} {ext_in}")

if __name__ == "__main__":

    smr20 = SMR20()

    pass