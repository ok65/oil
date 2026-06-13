
# Library imports
from typing import Callable, List, Tuple


class TestParameter:

    def __init__(self, name: str, setter: Callable[[float], None], start_value: float, stop_value: float, step_size: float):
        self._idx = 0
        self.name = name
        self.setter = setter
        self.start_value = start_value
        self.stop_value = stop_value
        self.step_size = step_size
        self.test_values = []

        for x in range(int((self.stop_value - self.start_value) / self.step_size)):
            self.test_values.append(self.start_value + (x * self.step_size))

    def values(self) -> List:
        return self.test_values

    def values_tuple(self) -> List[Tuple]:
        return [(v, self) for v in self.values()]