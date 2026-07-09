
# Library imports

# Project imports
from oil.core.instrument import Instrument


class SMR20(Instrument):

    # SCPI strings
    _FREQ = "FREQ"
    _POWER = "POW"
    _RFON = "OUTP1:STAT"
    _EXTREF = "ROSC:SOUR"

    def __init__(self, visa_string: str):
        """
        SMR20 instrument class
        :param visa_string: pyvisa connection string (use oil.serial_port_string() or oil.ip_address_string() as
                                                      helper functions, or refer to pyvisa documentation)
        """
        super().__init__(visa_string)

    @property
    def frequency(self) -> float:
        """ :return: Return the sig gen's current output frequency in Hz """
        return float(self._query(f"{self._FREQ}"))

    @frequency.setter
    def frequency(self, value: float) -> None:
        """ :param value: Set the sig gen's output frequency in Hz """
        self._command(f"{self._FREQ} {value:.0f}")

    @property
    def power(self) -> float:
        """ :return: Return the sig gen's current output power in dBm """
        return float(self._query(f"{self._POWER}"))

    @power.setter
    def power(self, value: float) -> None:
        """ :param value: Set the sig gen's output power in dBm """
        self._command(f"{self._POWER} {value} dBM")

    @property
    def rf_enable(self) -> bool:
        """ :return: Return the sig gen's current rf output enable state """
        return (self._query(f"{self._RFON}")) == "ON"

    @rf_enable.setter
    def rf_enable(self, value: bool) -> None:
        """ :param value: Set the sig gen's rf output enable state """
        onoff = "ON" if value else "OFF"
        self._command(f"{self._RFON} {onoff}")

    @property
    def external_reference(self) -> bool:
        """ :return: Return the external reference enabled state """
        return (self._query(self._EXTREF)) == "EXT"

    @external_reference.setter
    def external_reference(self, value: bool) -> None:
        """ :param value: Set the external reference enabled state """
        ext_in = "EXT" if value else "INT"
        self._command(f"{self._RFON} {ext_in}")
