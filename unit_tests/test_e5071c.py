import pytest


def test_e5071c_driver_converts_address_and_uses_expected_scalar_scpi(e5071c_driver):
    driver, virtual_instrument, resource_manager = e5071c_driver

    driver.frequency_start = 2_000_000.0
    driver.frequency_points = 401
    driver.source_power = -5.0
    driver.reference_level = -20.0
    driver.source_attenuation_auto = False
    driver.measurement = "s11"

    assert resource_manager.opened_addresses == ["TCPIP::127.0.0.1::5025::SOCKET"]
    assert virtual_instrument.command_log == [
        "SENS1:FREQ:STAR 2000000.0",
        "SENS1:SWE:POIN 401",
        "SOUR1:POW -5.0",
        "DISP:WIND1:TRAC1:Y:SCAL:RLEV -20.0",
        "SOUR1:POW:ATT:AUTO OFF",
        "CALC1:PAR1:DEF S11",
    ]
    assert driver.frequency_start == 2_000_000.0
    assert driver.frequency_points == 401
    assert driver.source_power == -5.0
    assert driver.reference_level == -20.0
    assert driver.source_attenuation_auto is False
    assert driver.measurement == "S11"


def test_e5071c_driver_rejects_invalid_measurement_without_writing(e5071c_driver):
    driver, virtual_instrument, _ = e5071c_driver

    with pytest.raises(ValueError, match="Invalid measurement"):
        driver.measurement = "S55"

    assert virtual_instrument.command_log == []


def test_e5071c_driver_downloads_interleaved_trace_data_from_selected_trace(e5071c_driver):
    driver, virtual_instrument, _ = e5071c_driver
    virtual_instrument.write_memory("trace.2.frequency_data", [10.0, 20.0])
    virtual_instrument.write_memory("trace.2.formatted_data", [-9.0, 0.0, -3.0, 0.0])

    result = driver.download_trace(trace_id=2)

    assert result == {"frequency": [10.0, 20.0], "level": [-9.0, -3.0]}
    assert virtual_instrument.command_log == ["CALC1:PAR2:SEL"]
    assert virtual_instrument.query_log == ["CALC1:DATA:XAX?", "CALC1:DATA:FDAT?"]


def test_e5071c_driver_ignores_stale_idn_response_during_trace_download(e5071c_driver, monkeypatch):
    driver, _, _ = e5071c_driver
    responses = iter([
        "Agilient Technologies,E5071C,0,0\n10.0,20.0",
        "Agilient Technologies,E5071C,0,0\n-9.0,0.0,-3.0,0.0",
    ])
    monkeypatch.setattr(driver, "_query", lambda *_args, **_kwargs: next(responses))

    assert driver.download_trace() == {
        "frequency": [10.0, 20.0],
        "level": [-9.0, -3.0],
    }


def test_e5071c_marker_driver_uses_virtual_marker_contract(e5071c_driver):
    driver, virtual_instrument, _ = e5071c_driver
    virtual_instrument.write_memory("trace.1.frequency_data", [10.0, 20.0])
    virtual_instrument.write_memory("trace.1.formatted_data", [-6.0, 0.0, -1.0, 0.0])

    driver.marker[2].enabled = True
    driver.marker[2].frequency = 12.0
    driver.marker[2].peak_search()

    assert virtual_instrument.command_log == [
        "CALC1:MARK2:STAT ON",
        "CALC1:MARK2:X 12.0",
        "CALC1:MARK2:FUNC:TYPE MAX",
        "CALC1:MARK2:FUNC:EXEC",
    ]
    assert driver.marker[2].enabled is True
    assert driver.marker[2].frequency == 20.0
    assert driver.marker[2].power == -1.0
