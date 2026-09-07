def test_n9030_driver_constructs_markers_and_uses_expected_scpi(n9030_driver):
    driver, virtual_instrument, resource_manager = n9030_driver

    driver.frequency_center = 2_500_000.4
    driver.ref_level = -10.2
    driver.input_attenuation = 20
    driver.bandwidth_setting = 3

    assert resource_manager.opened_addresses == ["TCPIP::127.0.0.1::INSTR"]
    assert len(driver.marker) == 12
    assert virtual_instrument.command_log == [
        "FREQ:CENT 2500000",
        "DISP:WIND1:TRAC:Y:RLEV -10 dBm",
        "POW:RF:ATT 20",
        "BAND:SEL RBW3",
    ]
    assert driver.frequency_center == 2_500_000.0
    assert driver.ref_level == -10.0
    assert driver.input_attenuation == 20.0
    assert driver.bandwidth_setting == 3


def test_n9030_driver_downloads_trace_with_both_frequency_endpoints(n9030_driver):
    driver, virtual_instrument, _ = n9030_driver
    virtual_instrument.write_memory("trace.2.power_data", [-50.0, -40.0, -45.0])

    result = driver.download_trace(trace_id=2)

    assert result == {
        "frequency": [1_000_000.0, 1_500_000.0, 2_000_000.0],
        "power": [-50.0, -40.0, -45.0],
    }
    assert virtual_instrument.query_log == [
        "FREQ:STAR?",
        "FREQ:STOP?",
        "SENS:SWE:POIN?",
        ":TRAC:DATA? TRACE2",
    ]


def test_n9030_marker_driver_uses_virtual_marker_contract(n9030_driver):
    driver, virtual_instrument, _ = n9030_driver

    driver.marker[3].enabled = True
    driver.marker[3].frequency = 1_234.9
    driver.marker[3].peak_search()
    driver.marker[3].next_peak_right()
    driver.marker[3].next_peak_left()

    assert virtual_instrument.command_log == [
        "CALC:MARK3:STAT ON",
        "CALC:MARK3:MODE POS",
        ":CALC:MARK3:X 1234",
        "CALC:MARK3:MAX",
        "CALC:MARK3:MAX:RIGH",
        "CALC:MARK3:MAX:LEFT",
    ]
    assert driver.marker[3].enabled is True
    assert driver.marker[3].frequency == 1234.0
