
# Library imports
from typing import Callable
from oil.test_manager.test_iteration import TestIteration


class TestAction:

    def __init__(self, name: str, value: float, execute: Callable[['TestIteration', float], None]):
        self.name = name
        self.value = value
        self._execute_func = execute

    def execute(self, context: TestIteration):
        return self._execute_func(context, self.value)

    def __repr__(self):
        return f"TestAction({self.name})"


