def test_smr20_driver_sets_and_reads_the_virtual_signal_generator(smr20_driver):
    driver, virtual_instrument, resource_manager = smr20_driver

    driver.frequency = 2_500_000.4
    driver.power = -3.5
    driver.rf_enable = True
    driver.external_reference = True

    assert resource_manager.opened_addresses == ["TCPIP::127.0.0.1::INSTR"]
    assert virtual_instrument.command_log == [
        "FREQ 2500000",
        "POW -3.5 dBM",
        "OUTP1:STAT ON",
        "ROSC:SOUR EXT",
    ]
    assert driver.frequency == 2_500_000.0
    assert driver.power == -3.5
    assert driver.rf_enable is True
    assert driver.external_reference is True


def test_smr20_driver_reset_and_identify_use_the_common_virtual_resource(smr20_driver):
    driver, virtual_instrument, _ = smr20_driver
    driver.rf_enable = True

    assert driver.identify() == "Rohde&Schwarz,VirtualSMR20,0,0"
    driver.reset()

    assert virtual_instrument.command_log[-1] == "*RST"
    assert driver.rf_enable is False
