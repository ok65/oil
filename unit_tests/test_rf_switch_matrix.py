import pytest


def test_driver_converts_instr_address_to_switch_socket(rf_switch_driver):
    _, _, resource_manager = rf_switch_driver

    assert resource_manager.opened_addresses == ["TCPIP::127.0.0.1::5025::SOCKET"]


def test_driver_setters_send_scpi_commands_and_update_virtual_state(rf_switch_driver):
    driver, virtual_switch, _ = rf_switch_driver

    driver.rfa = 6
    driver.rfb = 3

    assert virtual_switch.command_log == ["RFA:SWITCH 6", "RFB:SWITCH 3"]
    assert virtual_switch.memory_snapshot() == {
        "rfa.switch.position": 6,
        "rfb.switch.position": 3,
    }


def test_driver_getters_query_virtual_switch_and_return_integers(rf_switch_driver):
    driver, virtual_switch, _ = rf_switch_driver
    virtual_switch.write("RFA:SWITCH 8")
    virtual_switch.write("RFB:SWITCH 2")

    assert driver.rfa == 8
    assert driver.rfb == 2
    assert virtual_switch.query_log == ["RFA:SWITCH?", "RFB:SWITCH?"]


@pytest.mark.parametrize("value", [0, 9, 1.5, "3"])
def test_invalid_driver_positions_fail_before_writing_to_the_device(rf_switch_driver, value):
    driver, virtual_switch, _ = rf_switch_driver

    with pytest.raises((TypeError, ValueError)):
        driver.rfa = value

    assert virtual_switch.command_log == []


def test_driver_reset_resets_virtual_switch_state(rf_switch_driver):
    driver, virtual_switch, _ = rf_switch_driver
    driver.rfa = 4
    driver.rfb = 5

    driver.reset()

    assert virtual_switch.command_log[-1] == "*RST"
    assert virtual_switch.memory_snapshot() == {
        "rfa.switch.position": 1,
        "rfb.switch.position": 1,
    }


def test_driver_clear_preserves_virtual_switch_position(rf_switch_driver):
    driver, virtual_switch, _ = rf_switch_driver
    driver.rfa = 4

    driver.clear()

    assert virtual_switch.command_log[-1] == "*CLS"
    assert virtual_switch.read_memory("rfa.switch.position") == 4
