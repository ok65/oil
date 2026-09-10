from oil.core.instrument import Instrument
from oil.core.virtual_instrument import VirtualInstrument


class RFSwitchMatrix(Instrument):
    """
    Driver for the dual SP8T RF switch matrix (designed by Oliver)

    The unit contains two independently controlled SP8T RF switches:
        RFA: ports 1-8
        RFB: ports 1-8
    """

    _RFA = "RFA:SWITCH"
    _RFB = "RFB:SWITCH"

    def __init__(self, visa_string: str, config=None):
        if visa_string.endswith("INSTR"):
            visa_string = visa_string[:-5]+"5025::SOCKET"
        super().__init__(visa_string, config=config)

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


class VirtualRFSwitchMatrix(VirtualInstrument):
    """Stateful simulator for :class:`RFSwitchMatrix`.

    It models the driver's current two-command surface only: selecting and
    reading one port (1--8) for each independent RF switch.
    """

    _RFA = "RFA:SWITCH"
    _RFB = "RFB:SWITCH"
    _RFA_MEMORY_KEY = "rfa.switch.position"
    _RFB_MEMORY_KEY = "rfb.switch.position"

    def __init__(self, rfa: int = 1, rfb: int = 1):
        super().__init__()
        self._set_positions(rfa, rfb)

    def reset(self) -> None:
        super().reset()
        self._set_positions(1, 1)

    def handle_command(self, command: str) -> None:
        prefix, separator, value = command.partition(" ")
        if not separator or prefix not in (self._RFA, self._RFB):
            raise NotImplementedError(f"Unsupported RF switch command: {command}")

        try:
            position = int(value)
        except ValueError as error:
            raise ValueError(f"RF switch position must be an integer: {value}") from error

        self._validate_switch_position(position)
        memory_key = self._RFA_MEMORY_KEY if prefix == self._RFA else self._RFB_MEMORY_KEY
        self.write_memory(memory_key, position)

    def handle_query(self, command: str) -> str:
        if command == f"{self._RFA}?":
            return str(self.read_memory(self._RFA_MEMORY_KEY))
        if command == f"{self._RFB}?":
            return str(self.read_memory(self._RFB_MEMORY_KEY))
        raise NotImplementedError(f"Unsupported RF switch query: {command}")

    def _set_positions(self, rfa: int, rfb: int) -> None:
        self._validate_switch_position(rfa)
        self._validate_switch_position(rfb)
        self.update_memory({
            self._RFA_MEMORY_KEY: rfa,
            self._RFB_MEMORY_KEY: rfb,
        })

    @staticmethod
    def _validate_switch_position(value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("RF switch position must be an integer")
        if not 1 <= value <= 8:
            raise ValueError("RF switch position must be between 1 and 8")
