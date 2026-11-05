"""Driver and virtual instrument for a Maturo MCU controlled turntable."""

import math
import time
from typing import Any, Mapping, Optional

from oil.core.instrument import Instrument
from oil.core.virtual_instrument import VirtualInstrument


class MaturoTurntable(Instrument):
    """Control a Maturo MCU turntable through a Prologix GPIB-Ethernet bridge.

    ``visa_string`` should address the adapter's TCP socket, usually
    ``TCPIP0::<adapter-ip>::1234::SOCKET``. ``gpib_address`` is the MCU's IEEE
    address configured in its front-panel menu and defaults to 7 to match the
    chamber MATLAB configuration. ``device_address`` selects the
    turntable on the MCU and defaults to 1. The MCU uses a GPIB register
    protocol rather than SCPI. Positions and limits are in degrees; speed is
    the MCU's integer setting from 1 to 8.
    """

    _HARDWARE_MINIMUM = -200.0
    _HARDWARE_MAXIMUM = 400.0

    def __init__(self, visa_string: str, gpib_address: int = 7,
                 device_address: int = 1,
                 config: Optional[Mapping[str, Any]] = None):
        self._validate_gpib_address(gpib_address)
        self._validate_device_address(device_address)
        self.gpib_address = gpib_address
        self.device_address = device_address
        super().__init__(visa_string)
        # Prologix Ethernet controllers listen on TCP port 1234. Manual
        # reads avoid the adapter's auto-read timeout after every motion write.
        for command in ("++mode 1", f"++addr {gpib_address}", "++auto 0",
                        "++read_tmo_ms 3000"):
            self.log_func(command)
            self._instr.write(command)
        if config is not None:
            self.apply_config(config)

    @property
    def position(self) -> float:
        """Current angular position in degrees."""
        return self._read_register("CP")

    @property
    def target_position(self) -> float:
        """Target angle stored in the MCU's NP register, in degrees.

        This confirms the requested setpoint independently of motor movement.
        """
        return self._read_register("NP")

    @property
    def busy(self) -> bool:
        """Whether the MCU reports that the turntable motor is moving."""
        return bool(int(self._read_register("BU")))

    @property
    def speed(self) -> int:
        """Current MCU speed setting (1 to 8)."""
        return int(self._read_register("SP"))

    @speed.setter
    def speed(self, value: int) -> None:
        self._validate_speed(value)
        self._select_device()
        self._command(f"LD {value} SP")

    @property
    def clockwise_limit(self) -> float:
        """Configured clockwise (upper) travel limit in degrees."""
        return self._read_register("WL")

    @clockwise_limit.setter
    def clockwise_limit(self, value: float) -> None:
        value = self._validate_angle(value)
        if value > self._HARDWARE_MAXIMUM:
            raise ValueError("clockwise_limit cannot exceed the +400 degree hardware limit")
        if value < self.counterclockwise_limit:
            raise ValueError("clockwise_limit must not be below counterclockwise_limit")
        self._write_register(value, "DG", "WL")

    @property
    def counterclockwise_limit(self) -> float:
        """Configured counterclockwise (lower) travel limit in degrees."""
        return self._read_register("CL")

    @counterclockwise_limit.setter
    def counterclockwise_limit(self, value: float) -> None:
        value = self._validate_angle(value)
        if value < self._HARDWARE_MINIMUM:
            raise ValueError("counterclockwise_limit cannot be below the -200 degree hardware limit")
        if value > self.clockwise_limit:
            raise ValueError("counterclockwise_limit must not exceed clockwise_limit")
        self._write_register(value, "DG", "CL")

    def move_to(self, angle: float, blocking: bool = True,
                tolerance: float = 0.5,
                timeout: Optional[float] = None,
                speed: Optional[int] = None) -> None:
        """Move to an absolute angle, optionally waiting for position feedback.

        The MCU's absolute NP/GO command is not used. The driver chooses CW or
        CC from the current position, polls CP while moving, and sends ST when
        CP enters the 2 degree coarse window, then switches to speed 1 and
        continues until CP enters ``tolerance``. ``speed`` sets the coarse
        speed (1 to 8); when omitted, the MCU's current speed is used. With
        ``blocking=False``, start coarse motion and return without polling or
        stopping. By default the blocking wait has no timeout; pass a positive
        ``timeout`` in seconds to bound the complete move.
        """
        angle = self._validate_angle(angle)
        if not isinstance(blocking, bool):
            raise TypeError("blocking must be a bool")
        try:
            tolerance = float(tolerance)
        except (TypeError, ValueError) as error:
            raise ValueError("tolerance must be a finite non-negative angle") from error
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be a finite non-negative angle")
        if speed is not None:
            self._validate_speed(speed)
        if timeout is not None:
            try:
                timeout = float(timeout)
            except (TypeError, ValueError) as error:
                raise ValueError("timeout must be a positive number of seconds or None") from error
            if not math.isfinite(timeout) or timeout <= 0:
                raise ValueError("timeout must be a positive number of seconds or None")

        lower_limit = self.counterclockwise_limit
        upper_limit = self.clockwise_limit
        if not lower_limit <= angle <= upper_limit:
            raise ValueError(
                f"Target angle {angle:g} is outside configured turntable limits "
                f"[{lower_limit:g}, {upper_limit:g}] degrees"
            )

        actual_position = self.position
        if abs(actual_position - angle) <= tolerance:
            self.stop()
            return

        coarse_speed = self.speed if speed is None else speed
        self.speed = coarse_speed

        if angle > actual_position:
            self.move_clockwise()
        else:
            self.move_counterclockwise()

        if not blocking:
            return

        start_time = time.monotonic()
        fine_speed_set = False
        try:
            while True:
                actual_position = self.position
                if abs(actual_position - angle) <= tolerance:
                    return
                if not fine_speed_set and abs(actual_position - angle) <= 2.0:
                    self.stop()
                    self.speed = 1
                    # Re-sample after stopping the coarse leg before choosing
                    # the direction of the fine correction.
                    actual_position = self.position
                    if abs(actual_position - angle) <= tolerance:
                        return
                    if angle > actual_position:
                        self.move_clockwise()
                    else:
                        self.move_counterclockwise()
                    fine_speed_set = True
                if timeout is not None and time.monotonic() - start_time >= timeout:
                    raise TimeoutError(
                        f"Maturo turntable did not reach {angle:.1f} degrees "
                        f"within {timeout:g} seconds; last position was "
                        f"{actual_position:.1f} degrees"
                    )
                time.sleep(0.1)
        finally:
            # Ensure an exception, including a read or timeout failure, cannot
            # leave continuous rotation running.
            self.stop()

    def move_clockwise(self) -> None:
        """Move clockwise until a travel limit or :meth:`stop` is reached."""
        self._select_device()
        self._command("CW")

    def move_counterclockwise(self) -> None:
        """Move counterclockwise until a travel limit or :meth:`stop` is reached."""
        self._select_device()
        self._command("CC")

    def stop(self) -> None:
        """Stop current movement."""
        self._select_device()
        self._command("ST")

    def _read_register(self, register: str) -> float:
        self._select_device()
        # MCU register reads use a plain register name. Ask the Prologix bridge
        # to read until GPIB EOI, then consume its response from the TCP socket.
        self._command(register)
        self.log_func("++read eoi")
        self._instr.write("++read eoi")
        return float(self._instr.read().strip())

    def _write_register(self, value: float, unit: str, register: str) -> None:
        self._select_device()
        self._command(f"LD {value:g} {unit} {register}")

    def _select_device(self) -> None:
        self._command(f"LD {self.device_address} DV")

    @staticmethod
    def _validate_gpib_address(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 30:
            raise ValueError("gpib_address must be an integer from 0 to 30")

    @staticmethod
    def _validate_device_address(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise ValueError("device_address must be an integer from 0 to 5")

    @classmethod
    def _validate_angle(cls, value: float) -> float:
        try:
            angle = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("angle must be a finite value in degrees") from error
        if not math.isfinite(angle) or not cls._HARDWARE_MINIMUM <= angle <= cls._HARDWARE_MAXIMUM:
            raise ValueError("angle must be between -200 and +400 degrees")
        return angle

    @staticmethod
    def _validate_speed(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 8:
            raise ValueError("speed must be an integer from 1 to 8")


class VirtualMaturoTurntable(VirtualInstrument):
    """Stateful simulator for the Maturo MCU turntable command subset."""

    IDENTIFICATION = "Maturo,VirtualMCU,0,0"

    def __init__(self, initial_memory: Optional[Mapping[str, Any]] = None):
        super().__init__()
        self._current_register = None
        self._pending_response = ""
        self._set_defaults()
        if initial_memory:
            self.update_memory(initial_memory)

    def reset(self) -> None:
        super().reset()
        self._current_register = None
        self._pending_response = ""
        self._set_defaults()

    def _set_defaults(self) -> None:
        self.update_memory({
            "positioner.address": 1,
            "position.degrees": 0.0,
            "position.target.degrees": 0.0,
            "position.busy": False,
            "position.speed": 8,
            "position.limit.clockwise.degrees": 400.0,
            "position.limit.counterclockwise.degrees": -200.0,
            "position.direction": None,
            "position.virtual_step.degrees": 0.5,
        })

    def handle_command(self, command: str) -> None:
        fields = command.split()
        if fields[:1] == ["++mode"] and fields[1:] == ["1"]:
            self.write_memory("prologix.mode", 1)
            return
        if fields[:1] == ["++addr"] and len(fields) == 2:
            self.write_memory("prologix.gpib_address", int(fields[1]))
            return
        if fields[:1] == ["++auto"] and fields[1:] == ["0"]:
            self.write_memory("prologix.auto_read", False)
            return
        if fields[:1] == ["++read_tmo_ms"] and len(fields) == 2:
            self.write_memory("prologix.read_timeout_ms", int(fields[1]))
            return
        if fields == ["++read", "eoi"]:
            if self._current_register is None:
                raise RuntimeError("No MCU register selected for Prologix read")
            self._pending_response = self.handle_query(self._current_register)
            return
        if command in {"CP", "BU", "SP", "WL", "CL", "NP"}:
            self._current_register = command
            return
        if fields[:1] == ["LD"] and len(fields) == 3 and fields[2] == "DV":
            address = int(fields[1])
            MaturoTurntable._validate_device_address(address)
            self.write_memory("positioner.address", address)
            return
        if fields[:1] == ["LD"] and len(fields) == 3 and fields[2] == "SP":
            speed = int(fields[1])
            MaturoTurntable._validate_speed(speed)
            self.write_memory("position.speed", speed)
            return
        if fields[:1] == ["LD"] and len(fields) in (4, 5):
            value = MaturoTurntable._validate_angle(fields[1])
            unit, register = fields[2:4]
            if unit != "DG" or register not in {"NP", "WL", "CL"}:
                raise NotImplementedError(f"Unsupported Maturo command: {command}")
            if len(fields) == 5 and fields[4] != "GO":
                raise NotImplementedError(f"Unsupported Maturo command: {command}")
            if len(fields) == 5 and register != "NP":
                raise NotImplementedError(f"Unsupported Maturo command: {command}")
            keys = {
                "NP": "position.target.degrees",
                "WL": "position.limit.clockwise.degrees",
                "CL": "position.limit.counterclockwise.degrees",
            }
            self.write_memory(keys[register], value)
            if register == "NP" and len(fields) == 5:
                self._move_to_target()
            return
        if command == "GO":
            self._move_to_target()
            return
        if command == "CW":
            self.write_memory("position.direction", "CW")
            self.write_memory("position.busy", True)
            return
        if command == "CC":
            self.write_memory("position.direction", "CC")
            self.write_memory("position.busy", True)
            return
        if command == "ST":
            self.write_memory("position.busy", False)
            self.write_memory("position.direction", None)
            return
        raise NotImplementedError(f"Unsupported Maturo command: {command}")

    def handle_query(self, command: str) -> str:
        register_map = {
            "CP": "position.degrees",
            "BU": "position.busy",
            "SP": "position.speed",
            "WL": "position.limit.clockwise.degrees",
            "CL": "position.limit.counterclockwise.degrees",
            "NP": "position.target.degrees",
        }
        if command not in register_map:
            raise NotImplementedError(f"Unsupported Maturo query: {command}")
        value = self.read_memory(register_map[command])
        if command == "CP":
            value = self._advance_virtual_position(value)
        if command == "BU":
            return "1" if value else "0"
        return f"{value:5g}"

    def read(self) -> str:
        """Return the response queued by the simulated Prologix ``++read``."""
        response = self._pending_response
        self._pending_response = ""
        return response

    def _move_to_target(self) -> None:
        target = self.read_memory("position.target.degrees")
        lower = self.read_memory("position.limit.counterclockwise.degrees")
        upper = self.read_memory("position.limit.clockwise.degrees")
        if not lower <= target <= upper:
            raise ValueError(f"Target angle must be within [{lower}, {upper}] degrees")
        self.write_memory("position.busy", True)
        self.write_memory("position.degrees", target)
        self.write_memory("position.busy", False)
        self.write_memory("position.direction", None)

    def _advance_virtual_position(self, position: float) -> float:
        """Advance continuous motion by one simulated encoder interval."""
        direction = self.read_memory("position.direction")
        if direction not in {"CW", "CC"}:
            return position
        step = float(self.read_memory("position.virtual_step.degrees"))
        limit_key = (
            "position.limit.clockwise.degrees"
            if direction == "CW"
            else "position.limit.counterclockwise.degrees"
        )
        limit = float(self.read_memory(limit_key))
        updated = min(position + step, limit) if direction == "CW" else max(position - step, limit)
        self.write_memory("position.degrees", updated)
        return updated


__all__ = ["MaturoTurntable", "VirtualMaturoTurntable"]
