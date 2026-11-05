import pytest


def test_znb_driver_properties_round_trip_through_virtual(znb_driver):
    driver, virtual, resource_manager = znb_driver

    driver.frequency_start = 2_000_000
    driver.frequency_points = 401
    driver.if_bandwidth = 300
    driver.averaging_count = 8
    driver.averaging_enabled = True
    driver.source_power = -5
    driver.measurement = "s11"

    assert resource_manager.opened_addresses == ["TCPIP::127.0.0.1::INSTR"]
    assert driver.frequency_start == 2_000_000
    assert driver.frequency_points == 401
    assert driver.if_bandwidth == 300
    assert driver.averaging_count == 8
    assert driver.averaging_enabled is True
    assert driver.source_power == -5
    assert driver.measurement == "S11"
    assert virtual.read_memory("measurement.parameter") == "S11"


def test_znb_driver_rejects_invalid_measurement(znb_driver):
    driver, virtual, _ = znb_driver

    with pytest.raises(ValueError, match="Invalid measurement"):
        driver.measurement = "S55"

    assert virtual.command_log == []


def test_znb_download_trace_and_marker_search_use_selected_trace(znb_driver):
    driver, virtual, _ = znb_driver
    virtual.write_memory("trace.2.frequency_data", [10.0, 20.0, 30.0])
    virtual.write_memory("trace.2.formatted_data", [-8.0, -2.0, -5.0])

    assert driver.download_trace(2) == {
        "frequency": [10.0, 20.0, 30.0],
        "level": [-8.0, -2.0, -5.0],
    }
    driver.marker[3].enabled = True
    driver.marker[3].frequency = 15.0
    driver.marker[3].peak_search()

    assert driver.marker[3].enabled is True
    assert driver.marker[3].frequency == 20.0
    assert driver.marker[3].power == -2.0


def test_znb_configuration_properties_round_trip(znb_driver):
    driver, _, _ = znb_driver
    driver.frequency_center = 5_000_000
    driver.frequency_span = 2_000_000
    driver.sweep_type = "LOG"
    driver.smoothing_enabled = True
    driver.smoothing_aperture = 2.5
    driver.reference_level = -15
    driver.scale_per_division = 5
    driver.reference_position = 4
    driver.source_attenuation = 10
    driver.source_attenuation_auto = False
    driver.restart_averaging()

    assert driver.frequency_center == 5_000_000
    assert driver.frequency_span == 2_000_000
    assert driver.sweep_type == "LOG"
    assert driver.smoothing_enabled is True
    assert driver.smoothing_aperture == 2.5
    assert driver.reference_level == -15
    assert driver.scale_per_division == 5
    assert driver.reference_position == 4
    assert driver.source_attenuation == 10
    assert driver.source_attenuation_auto is False

