
# Library imports
from typing import Callable, List, Tuple


class TestParameter:
    """
    The class
    """
    def __init__(self, name: str, setter: Callable[[float], None], start_value: float, stop_value: float, step_size: float):
        """
        Class of init
        :param name:
        :param setter:
        :param start_value:
        :param stop_value:
        :param step_size:
        """

        self._idx = 0
        self.name = name
        self.setter = setter
        self.start_value = start_value
        self.stop_value = stop_value
        self.step_size = step_size
        self.test_values = []

        for x in range(int((self.stop_value - self.start_value) / self.step_size) + 1):
            self.test_values.append(round(self.start_value + (x * self.step_size), 5))

    def values(self) -> List[float]:
        """Return the configured sweep values, including both endpoints."""
        return self.test_values

    def values_tuple(self) -> List[Tuple]:
        return [(v, self) for v in self.values()]


