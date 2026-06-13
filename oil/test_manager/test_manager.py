
# Library import
from typing import List, TYPE_CHECKING
from itertools import product

# Project import
from oil.test_manager.log import setup_logging
if TYPE_CHECKING:
    from oil.test_manager.test_parameter import TestParameter

class TestManager:

    def __init__(self, parameters: List['TestParameter']):

        self.logger = setup_logging()

        self.parameters = parameters
        self.sequence = []

        self.sequence = list(product(*[p.values_tuple() for p in parameters]))

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def run(self, index:int=0):
        for idx in range(index, len(self.sequence)):
            params = self.sequence[idx]
            msg = f"Test Sequence {idx}: "
            for value, param in params:
                msg += f"{param.name}={value} "
                param.setter(value)
            self.info(msg)









