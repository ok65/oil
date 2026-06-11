
# Library imports
from typing import Callable, List


class TestParameter:

    def __init__(self, name: str, setter: Callable[[float], None], start_value: float, stop_value: float, step_size: float):
        self._idx = 0
        self.name = name
        self.setter = setter
        self.start_value = start_value
        self.stop_value = stop_value
        self.step_size = step_size

    def next(self):
        value = self.start_value + (self.step_size * self._idx)
        if value > self.stop_value:
            raise StopIteration
        else:
            self.setter(value)
            self._idx += 1

    def reset(self):
        self._idx = 0

    def values(self) -> List:
        values = []
        for x in range(int((self.stop_value - self.start_value) / self.step_size)):
            values.append(self.next())
        return values