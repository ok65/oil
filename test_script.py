from oil.test_manager.test_manager import TestManager
from oil.test_manager.test_parameter import TestParameter#
from oil.test_manager.test_action import TestAction
from oil.test_manager.sweep import ParameterSweep


from time import sleep
from random import random


def specan_measure(context, value):
    sleep(random()* 3)


if __name__ == "__main__":

    sweepF = ParameterSweep("Freq", lambda x,y: x, 100, 200, 10)
    sweepP = ParameterSweep("Power", lambda x,y: x, 0, 14, 0.2)
    sweepA = ParameterSweep("Atten", lambda x,y: x, 0, 20, 10)

    measure = TestAction(name="SpecAn Measure", value=0, execute=specan_measure)

    tm = TestManager([sweepF, sweepP, sweepA, measure])


    tm.run()

    pass