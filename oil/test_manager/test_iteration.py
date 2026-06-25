
# Library imports
from typing import List, TYPE_CHECKING, Iterable

# Project imports
if TYPE_CHECKING:
    from oil.test_manager.test_action import TestAction


class TestIteration:
    """
    Class to store a collection of TestActions that should be performed sequentially as part of a single test iteration
    E.g. if you sweep over frequency and power settings, then each iteration will have a different pairing of frequency
    and power test actions to perform.
    """
    def __init__(self, actions: Iterable['TestAction']):
        """
        TestIteration Initialiser. Actions should be a list or tuple of TestActions.
        :param actions: Iterable container of Test Actions.
        """
        self.actions = actions

    def execute(self) -> None:
        """
        Execute all test actions in this TestIteration sequentially
        :return: None
        """
        for action in self.actions:
            action.execute(context=self)

    def get_string(self):
        """
        Fetch a description string that concats the name of all the TestActions within the TestIteration
        :return:
        """
        string = ""
        for action in self.actions:
            string += f"{action.name}, "
        return string