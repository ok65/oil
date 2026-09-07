import pytest

from oil.switches import VirtualRFSwitchMatrix


def test_defaults_are_stored_in_shared_memory():
    switch = VirtualRFSwitchMatrix()

    assert switch.memory_snapshot() == {
        "rfa.switch.position": 1,
        "rfb.switch.position": 1,
    }


def test_initial_positions_can_be_configured():
    switch = VirtualRFSwitchMatrix(rfa=2, rfb=8)

    assert switch.query("RFA:SWITCH?") == "2"
    assert switch.query("RFB:SWITCH?") == "8"


def test_writes_update_only_the_selected_switch_and_are_logged():
    switch = VirtualRFSwitchMatrix(rfa=2, rfb=3)

    switch.write("RFA:SWITCH 7")

    assert switch.read_memory("rfa.switch.position") == 7
    assert switch.read_memory("rfb.switch.position") == 3
    assert switch.command_log == ["RFA:SWITCH 7"]


@pytest.mark.parametrize(
    ("command", "expected_exception"),
    [
        ("RFA:SWITCH 0", ValueError),
        ("RFB:SWITCH 9", ValueError),
        ("RFA:SWITCH wrong", ValueError),
        ("RFX:SWITCH 1", NotImplementedError),
    ],
)
def test_invalid_or_unsupported_commands_fail_loudly(command, expected_exception):
    switch = VirtualRFSwitchMatrix()

    with pytest.raises(expected_exception):
        switch.write(command)


def test_reset_restores_both_switches_to_port_one():
    switch = VirtualRFSwitchMatrix(rfa=4, rfb=6)

    switch.write("*RST")

    assert switch.memory_snapshot() == {
        "rfa.switch.position": 1,
        "rfb.switch.position": 1,
    }
