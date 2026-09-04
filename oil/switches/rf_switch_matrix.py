from oil.core.instrument import Instrument


class RFSwitchMatrix(Instrument):
    """
    Driver for the dual SP8T RF switch matrix (designed by Oliver)

    The unit contains two independently controlled SP8T RF switches:
        RFA: ports 1-8
        RFB: ports 1-8
    """

    _RFA = "RFA:SWITCH"
    _RFB = "RFB:SWITCH"

    def __init__(self, visa_string: str):
        super().__init__(visa_string)

    @property
    def rfa(self) -> int:
        """ :return: Currently selected RFA port, 1-8 """
        return int(self._query(self._RFA))

    @rfa.setter
    def rfa(self, value: int) -> None:
        """ :param value: Select RFA port, 1-8 """
        self._validate_switch(value)
        self._command(f"{self._RFA} {value}")

    @property
    def rfb(self) -> int:
        """ :return: Currently selected RFB port, 1-8 """
        return int(self._query(self._RFB))

    @rfb.setter
    def rfb(self, value: int) -> None:
        """ :param value: Select RFB port, 1-8 """
        self._validate_switch(value)
        self._command(f"{self._RFB} {value}")

    @staticmethod
    def _validate_switch(value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("RF switch position must be an integer")

        if not 1 <= value <= 8:
            raise ValueError("RF switch position must be between 1 and 8")