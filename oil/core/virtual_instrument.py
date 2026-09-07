"""Shared base class for stateful, in-process instrument simulators."""

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional


_MISSING = object()


class VirtualInstrument:
    """A VISA-resource-shaped base class for simulated instruments.

    All simulated device state belongs in :attr:`memory`.  Concrete virtual
    instruments implement :meth:`handle_command` and :meth:`handle_query` to
    translate their SCPI vocabulary into reads and writes against that shared
    store.  This keeps simulator state inspectable and consistent across every
    instrument implementation.
    """

    _RESET = "*RST"
    _CLEAR = "*CLS"
    _IDN = "*IDN?"
    IDENTIFICATION = "oil,VirtualInstrument,0,0"

    def __init__(self, initial_memory: Optional[Mapping[str, Any]] = None):
        self.memory: Dict[str, Any] = {}
        self.command_log: List[str] = []
        self.query_log: List[str] = []

        if initial_memory:
            self.update_memory(initial_memory)

    def write_memory(self, key: str, value: Any) -> None:
        """Store one simulated value under a namespaced memory key."""
        self.memory[key] = value

    def update_memory(self, values: Mapping[str, Any]) -> None:
        """Store several simulated values using the common memory store."""
        for key, value in values.items():
            self.write_memory(key, value)

    def read_memory(self, key: str, default: Any = _MISSING) -> Any:
        """Read a simulated value, or raise ``KeyError`` when it is absent."""
        if default is _MISSING:
            return self.memory[key]
        return self.memory.get(key, default)

    def clear_memory(self) -> None:
        """Remove all simulated device state."""
        self.memory.clear()

    def memory_snapshot(self) -> Dict[str, Any]:
        """Return an isolated copy of the current simulated device state."""
        return deepcopy(self.memory)

    def reset(self) -> None:
        """Apply the common reset behaviour.

        Concrete instruments may override this to populate their own default
        state, but should call ``super().reset()`` first.
        """
        self.clear_memory()

    def clear_status(self) -> None:
        """Clear simulated status information.

        The base class has no status queue; subclasses can override this when
        they simulate one.
        """

    def write(self, command: str) -> None:
        """Accept a VISA-style command write and dispatch it to the simulator."""
        self.command_log.append(command)

        if command == self._RESET:
            self.reset()
            return
        if command == self._CLEAR:
            self.clear_status()
            return

        self.handle_command(command)

    def query(self, command: str) -> str:
        """Accept a VISA-style query and dispatch it to the simulator."""
        self.query_log.append(command)
        if command == self._IDN:
            return self.IDENTIFICATION
        return self.handle_query(command)

    def handle_command(self, command: str) -> None:
        """Implement one non-common SCPI command in a concrete simulator."""
        raise NotImplementedError(f"Unsupported virtual-instrument command: {command}")

    def handle_query(self, command: str) -> str:
        """Implement one SCPI query in a concrete simulator."""
        raise NotImplementedError(f"Unsupported virtual-instrument query: {command}")
