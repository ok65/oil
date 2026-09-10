
# Library imports

# Project imports
from oil.core.instrument import Instrument
from oil.core.virtual_instrument import VirtualInstrument


class SMR20(Instrument):

    # SCPI strings
    _FREQ = "FREQ"
    _POWER = "POW"
    _RFON = "OUTP1:STAT"
    _EXTREF = "ROSC:SOUR"

    def __init__(self, visa_string: str, config=None):
        """
        SMR20 instrument class
        :param visa_string: pyvisa connection string (use oil.serial_port_string() or oil.ip_address_string() as
                                                      helper functions, or refer to pyvisa documentation)
        """
        super().__init__(visa_string, config=config)

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
        self._command(f"{self._EXTREF} {ext_in}")


class VirtualSMR20(VirtualInstrument):
    """Stateful simulator for the implemented SMR20 command surface."""

    IDENTIFICATION = "Rohde&Schwarz,VirtualSMR20,0,0"

    _FREQ = "FREQ"
    _POWER = "POW"
    _RFON = "OUTP1:STAT"
    _EXTREF = "ROSC:SOUR"

    _FREQUENCY_KEY = "frequency.hz"
    _POWER_KEY = "power.dbm"
    _RF_ENABLE_KEY = "rf.enabled"
    _EXTERNAL_REFERENCE_KEY = "reference.external"

    def __init__(self, frequency: float = 1_000_000.0, power: float = -10.0,
                 rf_enabled: bool = False, external_reference: bool = False):
        super().__init__()
        self._set_defaults(frequency, power, rf_enabled, external_reference)

    def reset(self) -> None:
        super().reset()
        self._set_defaults(1_000_000.0, -10.0, False, False)

    def handle_command(self, command: str) -> None:
        prefix, separator, value = command.partition(" ")
        if not separator:
            raise NotImplementedError(f"Unsupported SMR20 command: {command}")

        if prefix == self._FREQ:
            self.write_memory(self._FREQUENCY_KEY, float(value))
            return
        if prefix == self._POWER:
            power = value[:-4] if value.endswith(" dBM") else value
            self.write_memory(self._POWER_KEY, float(power))
            return
        if prefix == self._RFON and value in ("ON", "OFF"):
            self.write_memory(self._RF_ENABLE_KEY, value == "ON")
            return
        if prefix == self._EXTREF and value in ("EXT", "INT"):
            self.write_memory(self._EXTERNAL_REFERENCE_KEY, value == "EXT")
            return
        raise NotImplementedError(f"Unsupported SMR20 command: {command}")

    def handle_query(self, command: str) -> str:
        if command == f"{self._FREQ}?":
            return str(self.read_memory(self._FREQUENCY_KEY))
        if command == f"{self._POWER}?":
            return str(self.read_memory(self._POWER_KEY))
        if command == f"{self._RFON}?":
            return "ON" if self.read_memory(self._RF_ENABLE_KEY) else "OFF"
        if command == f"{self._EXTREF}?":
            return "EXT" if self.read_memory(self._EXTERNAL_REFERENCE_KEY) else "INT"
        raise NotImplementedError(f"Unsupported SMR20 query: {command}")

    def _set_defaults(self, frequency: float, power: float, rf_enabled: bool,
                      external_reference: bool) -> None:
        self.update_memory({
            self._FREQUENCY_KEY: frequency,
            self._POWER_KEY: power,
            self._RF_ENABLE_KEY: rf_enabled,
            self._EXTERNAL_REFERENCE_KEY: external_reference,
        })
