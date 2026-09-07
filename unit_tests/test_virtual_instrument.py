import pytest

from oil.core import VirtualInstrument


def test_memory_store_reads_updates_and_clears_values():
    instrument = VirtualInstrument({"source.power": -10})

    instrument.write_memory("channel.1.enabled", True)
    instrument.update_memory({"channel.1.frequency": 1_000_000, "source.power": -5})

    assert instrument.read_memory("source.power") == -5
    assert instrument.read_memory("channel.1.enabled") is True
    assert instrument.read_memory("missing", "fallback") == "fallback"

    instrument.clear_memory()

    assert instrument.memory == {}


def test_memory_snapshot_is_isolated_from_live_state():
    instrument = VirtualInstrument({"trace.data": [1.0]})

    snapshot = instrument.memory_snapshot()
    snapshot["trace.data"].append(2.0)

    assert instrument.read_memory("trace.data") == [1.0]


def test_common_reset_clears_memory_and_is_logged():
    instrument = VirtualInstrument({"source.power": -10})

    instrument.write("*RST")

    assert instrument.memory == {}
    assert instrument.command_log == ["*RST"]


def test_unsupported_commands_and_queries_are_logged_then_fail():
    instrument = VirtualInstrument()

    with pytest.raises(NotImplementedError, match="command"):
        instrument.write("SOUR:POW -10")
    with pytest.raises(NotImplementedError, match="query"):
        instrument.query("SOUR:POW?")

    assert instrument.command_log == ["SOUR:POW -10"]
    assert instrument.query_log == ["SOUR:POW?"]
