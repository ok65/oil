
# Library imports
import pyvisa
import time

class Instrument:

    # Common SCIPI commands
    _RESET = "*RST"
    _CLEAR = "*CLS"
    _IDN = "*IDN"
    _TEST = "*TST"

    def __init__(self, visa_string: str):
        rm = pyvisa.ResourceManager()
        self._instr = rm.open_resource(visa_string)

    def _command(self, cmd_string: str) -> None:
        print(cmd_string)
        self._instr.write(cmd_string)

    def _query(self, qry_string: str, qm: bool = True) -> str:
        qm = "?" if qm else ""
        msg = f"{qry_string}{qm}"
        print(msg)
        return self._instr.query(msg)

    def reset(self) -> None:
        self._command(self._RESET)

    def clear(self) -> None:
        self._command(self._CLEAR)

    def identify(self) -> str:
        return self._query(self._IDN)

