
# Library imports
import pyvisa
import serial
import threading
import time
from typing import Any, Callable, List, Mapping, Optional

# Project imports
from oil.core.errors import *


class InstrumentBase:
    """Common base for instrument drivers, independent of transport/protocol."""

    def __init__(self, log_func: Optional[Callable[[str], None]] = None,
                 config: Optional[Mapping[str, Any]] = None):
        self.log_func = log_func if log_func else lambda x: None
        if config is not None:
            self.apply_config(config)

    def apply_config(self, config: Mapping[str, Any]) -> None:
        """Set writable driver properties from a parameter dictionary."""
        for name, value in config.items():
            if not isinstance(name, str) or not isinstance(
                    getattr(type(self), name, None), property) or getattr(type(self), name).fset is None:
                raise ValueError(f"Unknown or read-only instrument parameter: {name}")
            setattr(self, name, value)

    def identify(self) -> str:
        """Return the connected instrument's identification string."""
        raise NotImplementedError("This instrument does not provide identification")

    def validate_instrument(self, expected_model: str) -> str:
        """Check that the connected instrument identifies as the expected model.

        Search for the model substring because IDN fields vary by vendor and
        firmware. Return the complete IDN response when validation succeeds.
        """
        if not isinstance(expected_model, str) or not expected_model.strip():
            raise ValueError("expected_model must be a non-empty string")
        identity = self.identify()
        if expected_model.casefold() not in identity.casefold():
            raise InstrumentIdentityError(
                f"Expected instrument model {expected_model!r}, got IDN {identity!r}"
            )
        return identity

    def close(self) -> None:
        """Release the instrument connection, if the driver has one."""


class InstrumentSerial(InstrumentBase):
    """Base for instruments controlled through a serial command interface."""

    def __init__(self, port: str, baudrate: int = 115200,
                 timeout: float = 5.0,
                 log_func: Optional[Callable[[str], None]] = None,
                 config: Optional[Mapping[str, Any]] = None):
        super().__init__(log_func)
        if not isinstance(port, str) or not port.strip():
            raise ValueError("port must be a non-empty serial port name")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._port = port
        self._timeout = timeout
        self._serial_lock = threading.RLock()
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=min(timeout, 0.2),
            write_timeout=timeout,
        )
        self._serial.reset_input_buffer()
        if config is not None:
            self.apply_config(config)

    def close(self) -> None:
        with self._serial_lock:
            if getattr(self, "_serial", None) is not None and self._serial.is_open:
                self._serial.close()

    def _serial_command(self, command: str, prompt: bytes = b"ch> ") -> str:
        """Send one CR-terminated shell command and read through its prompt.

        NanoVNA-H echoes each command and terminates the response with a
        ``ch> `` prompt. Concrete drivers can parse the returned response.
        """
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string")
        if "\r" in command or "\n" in command:
            raise ValueError("command must be a single line")

        with self._serial_lock:
            self._serial.reset_input_buffer()
            self.log_func(command)
            self._serial.write(command.encode("ascii") + b"\r")
            self._serial.flush()

            deadline = time.monotonic() + self._timeout
            response = bytearray()
            while time.monotonic() < deadline:
                chunk = self._serial.read(256)
                if chunk:
                    response.extend(chunk)
                    if response.endswith(prompt):
                        break
            if not response.endswith(prompt):
                raise CommsTimeoutError(
                    f"Timed out waiting for serial response to {command!r}"
                )
        try:
            text = response[:-len(prompt)].decode("ascii").strip()
        except UnicodeDecodeError as error:
            raise ValueError("Serial response was not ASCII text") from error

        # The shell echoes the command as the first response line.
        lines = text.splitlines()
        if lines and lines[0].strip() == command.strip():
            lines = lines[1:]
        return "\n".join(lines).strip()


class InstrumentSCPI(InstrumentBase):
    """Instrument base for VISA-connected SCPI devices."""

    # Common SCIPI commands
    _RESET = "*RST"
    _CLEAR = "*CLS"
    _IDN = "*IDN"
    _TEST = "*TST"

    def __init__(self, visa_string: str, log_func: Optional[Callable[[str], None]] = None,
                 config: Optional[Mapping[str, Any]] = None):
        super().__init__(log_func)
        self._visa_string = visa_string
        self._rm = pyvisa.ResourceManager("@py")
        retry = True
        while True:
            try:
                self._connect()

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
        if config is not None:
            self.apply_config(config)

    def close(self) -> None:
        if hasattr(self, "_instr"):
            self._instr.close()


    def _connect(self) -> None:
        self._instr = self._rm.open_resource(self._visa_string)
        self._instr.read_termination = "\n"
        self._instr.write_termination = "\n"
        self._instr.timeout = 5_000

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

    def _query(self, qry_string: str, parameters: Optional[str] = None,
               qm: bool = True, auto_retry: bool = True) -> str:

        # Prepare question mark, message string and failed/result vars
        # Parameters belong after the query marker, e.g. ``VOLT? MAX``.
        # Keep ``qm`` for compatibility with existing callers that query a
        # command which already includes its own question mark.
        query_marker = "?" if qm and not qry_string.rstrip().endswith("?") else ""
        msg = f"{qry_string}{query_marker}"
        if parameters:
            msg = f"{msg} {parameters}"
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

    @staticmethod
    def _parse_numeric_csv(response: str) -> List[float]:
        """Return the first complete numeric CSV line, ignoring socket chaff."""
        for line in response.splitlines():
            fields = [field.strip() for field in line.split(",")]
            if not fields or any(not field for field in fields):
                continue
            try:
                return [float(field) for field in fields]
            except ValueError:
                continue
        raise ValueError("Instrument response did not contain numeric CSV data")

    def reset(self) -> None:
        self._command(self._RESET)

    def clear(self) -> None:
        self._command(self._CLEAR)

    def identify(self) -> str:
        return self._query(self._IDN)


# Backwards-compatible name used by existing drivers and client code.
Instrument = InstrumentSCPI

