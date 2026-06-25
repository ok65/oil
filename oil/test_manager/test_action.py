
# Library imports
from typing import Callable
from oil.test_manager.test_iteration import TestIteration


class TestAction:
    """
    Simple class that details a single test action (set frequency, measure voltage, set attenuator etc).
    This class stores a function to perform the action, and a value to apply to it.
    """
    def __init__(self, name: str, value: float, execute: Callable[['TestIteration', float], None]):
        """
        TestAction initialiser.
        :param name: Name string to represent test action for logging purposes
        :param value: Float value to apply to execute function
        :param execute: Function to call to perform action, should take TestIteration (context) and the float value
        """
        self.name = name
        self.value = value
        self._execute_func = execute

    def execute(self, context: TestIteration):
        """
        Call this function perform the test action
        :param context: Provide the TestIteration context (provides link to all other test actions in this iteration).
                        This can be used to vary this action based on other tests (set analyser to same freq as sig gen)
        :return: Returns whatever the execute function returns
        """
        return self._execute_func(context, self.value)

    def __repr__(self):
        return f"TestAction({self.name})"


