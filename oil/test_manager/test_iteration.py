
# Library imports
from typing import List, TYPE_CHECKING, Iterable

# Project imports
if TYPE_CHECKING:
    from oil.test_manager.test_action import TestAction


class TestIteration:

    def __init__(self, actions: Iterable['TestAction']):
        self.actions = actions

    def execute(self):
        for action in self.actions:
            action.execute(context=self)

    def get_string(self):
        string = ""
        for action in self.actions:
            string += f"{action.name}, "
        return string