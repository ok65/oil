"""Pico Technology PT-104 driver.

The PT-104 does not speak SCPI.  This module wraps Pico's ``usbpt104`` SDK
using ``ctypes`` and therefore requires PicoSDK to be installed on the host.
The SDK is loaded lazily, so importing :mod:`oil.data_loggers` remains safe on
machines that do not have a PT-104 or PicoSDK installed.
"""

from ctypes import byref, c_int16, c_int32, c_uint32, create_string_buffer
from enum import IntEnum
from pathlib import Path
from typing import Any, List, Mapping, Optional, Union

from oil.core.instrument import InstrumentBase
from oil.core.virtual_instrument import VirtualInstrument


class PT104DataType(IntEnum):
    OFF = 0
    PT100 = 1
    PT1000 = 2
    RESISTANCE_375R = 3
    RESISTANCE_10KR = 4
    VOLTAGE_115MV = 5
    VOLTAGE_2_5V = 6


PT100 = PT104DataType.PT100
PT1000 = PT104DataType.PT1000


class PT104ChannelNotConfiguredError(RuntimeError):
    """Raised when a reading is requested from an unconfigured PT-104 channel."""


class _PT104Info(IntEnum):
    """Values from Pico's PICO_INFO enum in PicoStatus.h."""

    VARIANT_INFO = 3
    BATCH_AND_SERIAL = 4


class PT104Channel:
    """A single PT-104 channel owned by a parent PT-104 instance."""

    def __init__(self, parent: Any, number: int):
        self.parent = parent
        self.number = number

    @property
    def probe_type(self) -> PT104DataType:
        return self.parent._channel_configuration(self.number)[0]

    @probe_type.setter
    def probe_type(self, value: PT104DataType) -> None:
        self.parent.configure_channel(self.number, value, self.wires)

    @property
    def wires(self) -> int:
        return self.parent._channel_configuration(self.number)[1]

    @wires.setter
    def wires(self, value: int) -> None:
        self.parent.configure_channel(self.number, self.probe_type, value)

    def configure(self, probe_type: PT104DataType, wires: int = 4) -> None:
        self.parent.configure_channel(self.number, probe_type, wires)

    def read(self, filtered: bool = True) -> float:
        return self.parent.read(self.number, filtered=filtered)


class PT104(InstrumentBase):
    """Control a Pico PT-104 through Pico's native ``usbpt104`` SDK.

    ``sdk`` is an optional dependency-injection hook intended for tests.  A
    real device is opened immediately when ``sdk`` is omitted.
    """

    _CT_USB = 0x00000001

    def __init__(self, serial_number: Optional[Union[str, int]] = 0,
                 sdk_path: Optional[str] = None, sdk: Any = None,
                 config: Optional[Mapping[str, Any]] = None):
        super().__init__()
        self._sdk = sdk if sdk is not None else self._load_sdk(sdk_path)
        self._handle = c_int16()
        self._closed = True
        self._channels = {number: (PT104DataType.OFF, 4) for number in range(1, 5)}
        self._channel = {
            number: PT104Channel(self, number)
            for number in range(1, 5)
        }
        serial = 0 if serial_number in (None, 0) else create_string_buffer(
            str(serial_number).encode("ascii")
        )
        status = self._sdk.UsbPt104OpenUnit(byref(self._handle), serial)
        self._check(status, "UsbPt104OpenUnit")
        self._closed = False
        if config is not None:
            self.apply_config(config)

    @classmethod
    def list_devices(cls, sdk_path: Optional[str] = None, sdk: Any = None) -> List[str]:
        """Return serial numbers for currently connected USB PT-104 devices."""
        sdk = sdk if sdk is not None else cls._load_sdk(sdk_path)
        details = create_string_buffer(4096)
        length = c_uint32(len(details))
        cls._check(sdk.UsbPt104Enumerate(details, byref(length), cls._CT_USB),
                   "UsbPt104Enumerate")

        devices = []
        for entry in details.value.decode(errors="replace").split(","):
            entry = entry.strip()
            if not entry:
                continue
            _, separator, serial = entry.partition(":")
            devices.append(serial if separator else entry)
        return devices

    def close(self) -> None:
        if not self._closed:
            self._check(self._sdk.UsbPt104CloseUnit(self._handle), "UsbPt104CloseUnit")
            self._closed = True

    def identify(self) -> str:
        """Return identity obtained from the connected PT-104 SDK handle."""
        variant = self._get_unit_info(_PT104Info.VARIANT_INFO)
        serial = self._get_unit_info(_PT104Info.BATCH_AND_SERIAL)
        return f"Pico Technology,PT-104,{variant},{serial}"

    @property
    def channel(self) -> dict:
        """Return the parent-owned channel objects indexed from 1 to 4."""
        return self._channel

    def _get_unit_info(self, info: _PT104Info) -> str:
        buffer = create_string_buffer(256)
        required_size = c_int16()
        self._check(self._sdk.UsbPt104GetUnitInfo(
            self._handle, buffer, len(buffer), byref(required_size), int(info),
        ), "UsbPt104GetUnitInfo")
        return buffer.value.decode(errors="replace")

    def __enter__(self) -> "PT104":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def set_mains_frequency(self, hertz: int) -> None:
        if hertz not in (50, 60):
            raise ValueError("PT-104 mains frequency must be 50 or 60 Hz")
        self._check(self._sdk.UsbPt104SetMains(self._handle, hertz == 60), "UsbPt104SetMains")

    def configure_channel(self, channel: int, data_type: PT104DataType,
                          wires: int = 4) -> None:
        self._validate_channel(channel)
        if data_type in (PT104DataType.PT100, PT104DataType.PT1000) and wires not in (2, 3, 4):
            raise ValueError("PT100/PT1000 channels require 2, 3, or 4 wires")
        self._check(self._sdk.UsbPt104SetChannel(
            self._handle, int(channel), int(data_type), wires,
        ), "UsbPt104SetChannel")
        self._channels[channel] = (data_type, wires)

    def _channel_configuration(self, channel: int):
        return self._channels[channel]

    def read(self, channel: int, filtered: bool = True) -> float:
        """Return the latest reading; temperature values are in degrees C."""
        self._validate_channel(channel)
        value = c_int32()
        status = self._sdk.UsbPt104GetValue(
            self._handle, int(channel), byref(value), int(filtered),
        )
        if int(status) == 0x25:
            raise PT104ChannelNotConfiguredError(
                f"PT-104 channel {channel} is not configured; "
                "configure its probe type before reading it."
            )
        self._check(status, "UsbPt104GetValue")
        data_type = self._channels.get(channel, (None, None))[0]
        if data_type in (PT104DataType.PT100, PT104DataType.PT1000):
            return value.value / 1000.0
        return float(value.value)

    read_temperature = read

    @staticmethod
    def _validate_channel(channel: int) -> None:
        if channel not in (1, 2, 3, 4):
            raise ValueError("PT-104 channel must be an integer from 1 to 4")

    @staticmethod
    def _check(status: int, function: str) -> None:
        if int(status) != 0:
            raise RuntimeError(f"{function} failed with Pico status 0x{int(status):X}")

    @staticmethod
    def _load_sdk(sdk_path: Optional[str]):
        import ctypes
        candidates = [sdk_path] if sdk_path else []
        candidates += ["usbpt104.dll", "libusbpt104.so", "libusbpt104.dylib"]
        last_error = None
        for candidate in candidates:
            if not candidate:
                continue
            try:
                return ctypes.CDLL(str(Path(candidate)))
            except OSError as error:
                last_error = error
        raise ImportError(
            "Pico's usbpt104 SDK was not found. Install PicoSDK or pass sdk_path."
        ) from last_error


class VirtualPT104(VirtualInstrument):
    """Stateful PT-104 simulator with the same public API as :class:`PT104`."""

    IDENTIFICATION = "Pico Technology,Virtual PT-104,0,0"

    def __init__(self, readings=None, mains_frequency: int = 50,
                 serial_number: str = "VIRTUAL-PT104"):
        super().__init__()
        self.serial_number = serial_number
        self._channels = {number: (PT104DataType.OFF, 4) for number in range(1, 5)}
        self._channel = {
            number: PT104Channel(self, number)
            for number in range(1, 5)
        }
        self._set_defaults(readings or {}, mains_frequency)

    def reset(self) -> None:
        super().reset()
        self._set_defaults({}, 50)

    def set_mains_frequency(self, hertz: int) -> None:
        if hertz not in (50, 60):
            raise ValueError("PT-104 mains frequency must be 50 or 60 Hz")
        self.write_memory("mains.frequency.hz", hertz)

    def identify(self) -> str:
        return f"{self.IDENTIFICATION},{self.serial_number}"

    @property
    def channel(self) -> dict:
        """Return the parent-owned channel objects indexed from 1 to 4."""
        return self._channel

    def configure_channel(self, channel: int, data_type: PT104DataType,
                          wires: int = 4) -> None:
        self._validate_channel(channel)
        if data_type in (PT104DataType.PT100, PT104DataType.PT1000) and wires not in (2, 3, 4):
            raise ValueError("PT100/PT1000 channels require 2, 3, or 4 wires")
        self.write_memory(self._channel_key(channel, "data_type"), data_type)
        self.write_memory(self._channel_key(channel, "wires"), wires)
        self._channels[channel] = (data_type, wires)

    def _channel_configuration(self, channel: int):
        return self._channels[channel]

    def set_reading(self, channel: int, value: float) -> None:
        """Set a simulated reading in engineering units."""
        self.write_memory(self._channel_key(channel, "reading"), value)

    def read(self, channel: int, filtered: bool = True) -> float:
        del filtered  # Filtering is represented by the configured test value.
        self._validate_channel(channel)
        return float(self.read_memory(self._channel_key(channel, "reading"), 0.0))

    read_temperature = read

    def _set_defaults(self, readings, mains_frequency: int) -> None:
        self.set_mains_frequency(mains_frequency)
        for channel, value in readings.items():
            self.set_reading(channel, value)

    @staticmethod
    def _channel_key(channel: int, field: str) -> str:
        return f"channel.{int(channel)}.{field}"

    @staticmethod
    def _validate_channel(channel: int) -> None:
        if channel not in (1, 2, 3, 4):
            raise ValueError("PT-104 channel must be an integer from 1 to 4")
