from oil.test_manager.test_manager import TestManager
from oil.test_manager.test_parameter import TestParameter#



if __name__ == "__main__":

    tp1 = TestParameter("Frequency", lambda x: x, 100, 200, 10)
    tp2 = TestParameter("Power", lambda x: x, 0, 14, 0.2)
    tp3 = TestParameter("Attenuation", lambda x: x, 0, 20, 10)

    tm = TestManager([tp1, tp2, tp3])


    tm.run()

    pass