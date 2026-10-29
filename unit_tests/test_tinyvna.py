import pytest


def test_tinyvna_download_trace_uses_local_sweep_settings(tinyvna_driver):
    driver, virtual_instrument, _ = tinyvna_driver
    driver.frequency_start = 20_000_000
    driver.frequency_stop = 30_000_000
    driver.frequency_points = 3

    trace = driver.download_trace()

    assert trace == {
        "frequency": [20_000_000.0, 25_000_000.0, 30_000_000.0],
        "S11": [0.5 + 0.1j] * 3,
    }
    assert driver.frequency_start == 20_000_000
    assert driver.frequency_stop == 30_000_000
    assert driver.frequency_points == 3
    assert virtual_instrument.query_log == [
        "sweep",
        "scan 20000000 30000000 3 7",
    ]


def test_tinyvna_download_trace_selects_s21_for_trace_two(tinyvna_driver):
    driver, _, _ = tinyvna_driver

    trace = driver.download_trace(trace_id=2)

    assert trace["S21"] == [0.2 - 0.1j] * 101
    assert len(trace["frequency"]) == 101
    assert "S11" not in trace


def test_tinyvna_power_and_bandwidth_properties(tinyvna_driver):
    driver, virtual_instrument, _ = tinyvna_driver

    driver.output_power = 2
    driver.bandwidth = 3

    assert driver.output_power == 2
    assert driver.bandwidth == 3
    assert driver.bandwidth_hz == 1000
    assert virtual_instrument.command_log == ["power 2", "bandwidth 3"]
    assert virtual_instrument.query_log[-3:] == ["power", "bandwidth", "bandwidth"]


def test_tinyvna_identifies_from_board_info(tinyvna_driver):
    driver, _, _ = tinyvna_driver

    assert "NanoVNA-H" in driver.identify()


def test_tinyvna_rejects_invalid_sweep_and_setting_values(tinyvna_driver):
    driver, virtual_instrument, _ = tinyvna_driver

    with pytest.raises(ValueError, match="frequency_points"):
        driver.frequency_points = 102
    with pytest.raises(ValueError, match="output_power"):
        driver.output_power = 4
    with pytest.raises(ValueError, match="bandwidth"):
        driver.bandwidth = 512

    driver.frequency_start = 110_000_000
    with pytest.raises(ValueError, match="frequency_stop"):
        driver.download_trace()
    assert virtual_instrument.query_log == ["sweep"]
