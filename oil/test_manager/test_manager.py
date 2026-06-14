
# Library import
from typing import List, TYPE_CHECKING, Union
from itertools import product
from time import time
from datetime import timedelta

# Project import
from oil.test_manager.log import setup_logging
from oil.test_manager.test_iteration import TestIteration
from oil.test_manager.sweep import Sweep

if TYPE_CHECKING:
    from oil.test_manager.test_action import TestAction



class TestManager:

    def __init__(self, actions: List[Union['TestAction', 'Sweep']]):

        self.logger = setup_logging()

        self.sequence = []
        self._moving_avg_data = []

        action_list = []
        for action in actions:
            if isinstance(action, Sweep):
                action_list.append(action.values())
            else:
                action_list.append([action])

        test_actions = list(product(*action_list))
        self.sequence = [TestIteration(ta) for ta in test_actions]
        pass

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def run(self, index:int=0):
        for idx in range(index, len(self.sequence)):
            self.logger.info(self.sequence[idx].get_string())
            start = time()
            self.sequence[idx].execute()
            elapsed = round(time() - start, 1)
            est_remain = self._moving_avg(elapsed * (len(self.sequence) - idx))
            self.logger.info(f"Test {idx}/{len(self.sequence)} - Est. time remain: {timedelta(seconds=est_remain)}")

    def _moving_avg(self, new_value) -> float:

        self._moving_avg_data.append(new_value)

        if len(self._moving_avg_data) > 10:
            self._moving_avg_data.pop(0)

        return sum(self._moving_avg_data)/len(self._moving_avg_data)







