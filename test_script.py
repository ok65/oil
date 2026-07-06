
from oil.test_manager import TestRecord


if __name__ == "__main__":



    tr = TestRecord("test_record1.csv", ["temp", "angle", "power"])

    tr.write({"temp": 21.2, "angle": 35, "power": 11.2})
    tr.write({"temp": 21.4, "angle": 40, "power": 7.25643})
    tr.write({"temp": 22.2, "angle": 45, "power": 4.3})
    tr.write({"temp": 23.2, "angle": 50, "power": -12.332})

    pass
