import csv
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock

import oil.test_manager.log as log_module
import oil.test_manager.test_manager as manager_module
import oil.test_manager.test_record as record_module
from oil.test_manager import ListSweep, ParameterSweep
from oil.test_manager import TestAction as Action
from oil.test_manager import TestIteration as Iteration
from oil.test_manager import TestManager as Manager
from oil.test_manager.test_parameter import TestParameter as Parameter


def test_action_and_iteration_execute_in_order_and_describe_themselves():
    calls = []

    def record(context, value):
        calls.append((context, value))
        return value * 2

    first = Action("first", 1.0, record)
    second = Action("second", 2.0, record)
    iteration = Iteration([first, second], test_manager=None)

    iteration.execute()

    assert [value for _, value in calls] == [1.0, 2.0]
    assert iteration.get_string() == "first, second, "
    assert repr(first) == "TestAction(first)"


def test_sweeps_and_test_parameter_include_both_endpoints():
    execute = lambda context, value: None

    parameter_sweep = ParameterSweep("frequency", execute, 1.0, 2.0, 0.5)
    list_sweep = ListSweep("power", execute, [-10, -5])
    parameter = Parameter("gain", lambda value: None, 0.0, 1.0, 0.5)

    assert [action.value for action in parameter_sweep.values()] == [1.0, 1.5, 2.0]
    assert [action.name for action in list_sweep.values()] == ["power--10", "power--5"]
    assert parameter.values() == [0.0, 0.5, 1.0]
    assert parameter.values_tuple() == [(0.0, parameter), (0.5, parameter), (1.0, parameter)]


def test_manager_builds_cartesian_product_runs_actions_and_logs_progress(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(manager_module, "setup_logging", lambda: logger)
    clock = iter([10.0, 11.0, 20.0, 22.0, 30.0, 33.0, 40.0, 44.0])
    monkeypatch.setattr(manager_module, "time", lambda: next(clock))
    executed = []

    def record(context, value):
        executed.append(value)

    manager = Manager([
        ParameterSweep("frequency", record, 1.0, 2.0, 1.0),
        ListSweep("power", record, [-10, -5]),
    ])

    assert len(manager.sequence) == 4
    assert [iteration.get_string() for iteration in manager.sequence] == [
        "frequency-1.0, power--10, ",
        "frequency-1.0, power--5, ",
        "frequency-2.0, power--10, ",
        "frequency-2.0, power--5, ",
    ]

    manager.run()

    assert executed == [1.0, -10, 1.0, -5, 2.0, -10, 2.0, -5]
    assert logger.info.call_count == 8
    manager.info("information")
    manager.warn("warning")
    manager.error("error")
    logger.info.assert_any_call("information")
    logger.warning.assert_called_once_with("warning")
    logger.error.assert_called_once_with("error")


def test_manager_moving_average_keeps_the_latest_ten_values(monkeypatch):
    monkeypatch.setattr(manager_module, "setup_logging", Mock())
    manager = Manager([])

    for value in range(12):
        average = manager._moving_avg(value)

    assert manager._moving_avg_data == list(range(2, 12))
    assert average == 6.5


class _InMemoryOpen:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        return self.path.contents

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _InMemoryPath:
    def __init__(self, filepath):
        self.filepath = filepath
        self.contents = StringIO()
        self.created = False

    def exists(self):
        return self.created

    def open(self, mode, newline=""):
        if "w" in mode:
            self.contents = StringIO()
            self.created = True
        return _InMemoryOpen(self)


def test_record_creates_headers_and_writes_filtered_timestamped_rows(monkeypatch):
    in_memory_path = _InMemoryPath("record.csv")
    monkeypatch.setattr(record_module, "Path", lambda filepath: in_memory_path)
    monkeypatch.setattr(record_module.TestRecord, "_timestamp", staticmethod(lambda: "2026-09-07-12:00:00"))

    record = record_module.TestRecord("record.csv", ["frequency", "power"])
    record.write({"frequency": 1_000_000, "ignored": "value"})

    rows = list(csv.DictReader(StringIO(in_memory_path.contents.getvalue())))
    assert rows == [{
        "frequency": "1000000",
        "power": "",
        "timestamp": "2026-09-07-12:00:00",
    }]


class _FakePath:
    def __init__(self):
        self.mkdir = Mock()


def test_setup_logging_adds_handlers_once_without_touching_real_log_files(monkeypatch):
    logger = Mock()
    logger.handlers = []
    logger.addHandler.side_effect = logger.handlers.append
    fake_path = _FakePath()
    console_handler = Mock()
    file_handler = Mock()
    monkeypatch.setattr(log_module, "Path", lambda path: fake_path)
    fake_logging = SimpleNamespace(
        DEBUG=10,
        INFO=20,
        getLogger=lambda name: logger,
        StreamHandler=lambda: console_handler,
        FileHandler=lambda filename: file_handler,
        Formatter=lambda pattern: pattern,
    )
    monkeypatch.setattr(log_module, "logging", fake_logging)

    configured_logger = log_module.setup_logging()
    repeated_logger = log_module.setup_logging()

    assert configured_logger is logger
    assert repeated_logger is logger
    assert fake_path.mkdir.call_count == 2
    fake_path.mkdir.assert_called_with(exist_ok=True)
    assert logger.addHandler.call_count == 2
    console_handler.setLevel.assert_called_once_with(fake_logging.INFO)
    file_handler.setLevel.assert_called_once_with(fake_logging.DEBUG)
