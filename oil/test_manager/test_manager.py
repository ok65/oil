
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
    """
    TestManager is a helper class that takes lists of TestActions, and prepares a list of TestIterations that test every
    Combination of test actions (i.e. f1 p1, f1 p2, f2 p1, f2 p2).
    The test manager lets you compile the list of tests, and run through the entire set. It also takes care of logs
    and test results.
    """
    def __init__(self, actions: List[Union['TestAction', 'Sweep']]):
        """
        TestManager intialiser. Takes a list of TestAction and Sweeps, and creates a combination list (using the
        product function) and so preserves the order they are provided. This means you can set parameters first, then
        perform your measurement action last.
        :param actions: List of TestActions and Sweeps
        """
        # Setup the logger
        self.logger = setup_logging()

        # Prep the moving average data list
        self._moving_avg_data = []

        # Iterate through the actions, and if it's a Sweep pull the individual actions out and add.
        # The result is to create a list of lists/items
        action_list = []
        for action in actions:
            if isinstance(action, Sweep):
                action_list.append(action.values())
            else:
                action_list.append([action])

        # Create the combination list of test actions
        test_actions = list(product(*action_list))
        self.sequence = [TestIteration(ta) for ta in test_actions]

    def info(self, msg):
        """ Alias for logger.info() """
        self.logger.info(msg)

    def warn(self, msg):
        """ Alias for logger.warn() """
        self.logger.warning(msg)

    def error(self, msg):
        """ Alias for logger.error() """
        self.logger.error(msg)

    def run(self, index:int=0):
        """
        This function works through every TestIeration in the sequence. If a particular test fails, it can be restarted #
        from a given index position.
        :param index: Position to start testing from (defaults to the start)
        """
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







