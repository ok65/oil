
# Library imports
import pyvisa
import serial
import time
from typing import Callable, Optional

# Project imports
from oil.core.errors import *


class Instrument:

    # Common SCIPI commands
    _RESET = "*RST"
    _CLEAR = "*CLS"
    _IDN = "*IDN"
    _TEST = "*TST"

    def __init__(self, visa_string: str, log_func: Optional[Callable[[str], None]] = None):
        self.log_func = log_func if log_func else lambda x: None
        rm = pyvisa.ResourceManager()
        retry = True
        while True:
            try:
                self._instr = rm.open_resource(visa_string)

            # Reraise IP Visa error as oil error (after a retry)
            except pyvisa.errors.VisaIOError as e:
                if retry:
                    retry = False
                    time.sleep(1)
                    continue
                else:
                    raise PyVisaConfigError(e.description)

            # Reraise serial port error as oil error (after a retry)
            except serial.serialutil.SerialException as e:
                if retry:
                    retry = False
                    time.sleep(1)
                    continue
                else:
                    raise PyVisaConfigError(str(e))

            # If we get here, we succeeded, break from the loop.
            break

    def _command(self, cmd_string: str, auto_retry: bool = True) -> None:

        # Initialise failed flag, and attempt first command write (suppressing VisaIOError)
        failed = False
        try:
            self.log_func(cmd_string)
            self._instr.write(cmd_string)
        except pyvisa.errors.VisaIOError:
            failed = True

        # If first attempted failed, and auto_retry is set then try it again
        if auto_retry and failed:
            try:
                self.log_func(f"RETRY: {cmd_string}")
                self._instr.write(cmd_string)
            except pyvisa.errors.VisaIOError:
                failed = True
            else:
                failed = False

        # If we still failed at this point, raise a oil CommsTimeoutError
        if failed:
            raise CommsTimeoutError(f"Retry({auto_retry}), {cmd_string}")

    def _query(self, qry_string: str, qm: bool = True, auto_retry: bool = True) -> str:

        # Prepare question mark, message string and failed/result vars
        qm = "?" if qm else ""
        msg = f"{qry_string}{qm}"
        failed = False
        result = None

        # Try query first time, suppress VisaIOError
        try:
            self.log_func(msg)
            result = self._instr.query(msg)
        except pyvisa.errors.VisaIOError:
            failed = True

        # If it failed and auto_retry is enabled, try it again
        if auto_retry and failed:
            try:
                self.log_func(msg)
                result = self._instr.query(msg)
            except pyvisa.errors.VisaIOError:
                failed = True
            else:
                failed = False

        # At this point, if it failed then raise an oil CommsTimeoutError
        if failed:
            raise CommsTimeoutError(f"Retry({auto_retry}), {msg}")

        # Everything was good, return the result
        else:
            return result

    def reset(self) -> None:
        self._command(self._RESET)

    def clear(self) -> None:
        self._command(self._CLEAR)

    def identify(self) -> str:
        return self._query(self._IDN)

