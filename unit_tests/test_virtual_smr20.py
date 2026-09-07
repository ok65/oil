from oil.sig_gens import VirtualSMR20


def test_virtual_smr20_uses_its_own_scpi_contract_and_memory():
    signal_generator = VirtualSMR20()

    signal_generator.write("FREQ 2500000")
    signal_generator.write("POW -3.5 dBM")
    signal_generator.write("OUTP1:STAT ON")
    signal_generator.write("ROSC:SOUR EXT")

    assert signal_generator.memory_snapshot() == {
        "frequency.hz": 2_500_000.0,
        "power.dbm": -3.5,
        "rf.enabled": True,
        "reference.external": True,
    }
    assert signal_generator.query("FREQ?") == "2500000.0"
    assert signal_generator.query("POW?") == "-3.5"
    assert signal_generator.query("OUTP1:STAT?") == "ON"
    assert signal_generator.query("ROSC:SOUR?") == "EXT"


def test_virtual_smr20_reset_and_identification_are_common_resource_behaviour():
    signal_generator = VirtualSMR20(frequency=2_000_000.0, power=1.0, rf_enabled=True)

    assert signal_generator.query("*IDN?") == "Rohde&Schwarz,VirtualSMR20,0,0"
    signal_generator.write("*RST")

    assert signal_generator.read_memory("frequency.hz") == 1_000_000.0
    assert signal_generator.read_memory("power.dbm") == -10.0
    assert signal_generator.read_memory("rf.enabled") is False
