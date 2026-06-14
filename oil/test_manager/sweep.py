
# Library imports
from typing import Callable, List

# Project imports
from oil.test_manager.test_action import TestAction
from oil.test_manager.test_iteration import TestIteration


class Sweep:

    def __init__(self):
        self.test_actions = []

    def values(self) -> List:
        return self.test_actions


class ParameterSweep(Sweep):

    def __init__(self, name: str, execute: Callable[[TestIteration, float], None],
                 start_value: float, stop_value: float, step_size: float):

        super().__init__()

        self.start_value = start_value
        self.stop_value = stop_value
        self.step_size = step_size

        for x in range(int((self.stop_value - self.start_value) / self.step_size)):
            value = round(self.start_value + (x * self.step_size), 5)
            self.test_actions.append(TestAction(name=f"{name}-{value}", value=value, execute=execute))
