
# Library import
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from oil.test_manager.test_parameter import TestParameter


class TestManager:

    def __init__(self, parameters: List['TestParameter']):
        self.parameters = parameters



    def run(self):

        for param in self.parameters:









