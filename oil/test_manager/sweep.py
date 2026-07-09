
# Library imports
from typing import Callable, List, TYPE_CHECKING

# Project imports
from oil.test_manager.test_action import TestAction
if TYPE_CHECKING:
    from oil.test_manager.test_iteration import TestIteration


class Sweep:
    """
    Generic Sweep base class. Do not use directly
    """
    def __init__(self):
        self.test_actions = []

    def values(self) -> List['TestAction']:
        """
        Return list of TestActions contained in this sweep
        :return: List of TestActions
        """
        return self.test_actions


class ParameterSweep(Sweep):
    """
    Parameter sweep class. Takes start/stop/step parameters and produces a list of TestAction instances
    that covers the test sweep specified.
    """

    def __init__(self, name: str, execute: Callable[['TestIteration', float], None],
                 start_value: float, stop_value: float, step_size: float):
        """
        ParameterSweep initialiser takes an execute function, and sweep parameters to create an internal list of
        TestAction instances. Number of tests is calculated as stop-start/step.
        :param name: String name to represent this sweep
        :param execute: Callable function to perform the test action. Should take a TestIteraion instance (the context)
                        and the value to use for this test action.
        :param start_value: Value to start sweeping from (float)
        :param stop_value: Value to stop sweeping at (float)
        :param step_size: Size of steps (float)
        """
        super().__init__()

        self.start_value = start_value
        self.stop_value = stop_value
        self.step_size = step_size

        for x in range(int((self.stop_value - self.start_value) / self.step_size) + 1):
            value = round(self.start_value + (x * self.step_size), 5)
            self.test_actions.append(TestAction(name=f"{name}-{value}", value=value, execute=execute))


class ListSweep(Sweep):
    """
    List sweep class, takes a list of values and produces a list of TestAction instances.
    """

    def __init__(self, name: str, execute: Callable[['TestIteration', float], None], value_list: List):
        """
        List sweep initialiser takes a list of values and creates an internal list of TestAction instances.
        :param name: String name to represent this sweep
        :param execute: Callable function to perform the test action. Should take a TestIteration instance (the context)
        :param value_list: List of values to use (order will be preserved)
        """
        super().__init__()

        for value in value_list:
            self.test_actions.append(TestAction(name=f"{name}-{value}", value=value, execute=execute))