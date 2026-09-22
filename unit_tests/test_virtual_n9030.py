from oil.analyzers import VirtualN9030


def test_virtual_n9030_stores_analyser_settings_with_its_own_scpi_contract():
    analyser = VirtualN9030()

    analyser.write("FREQ:CENT 2500000")
    analyser.write("DISP:WIND1:TRAC:Y:RLEV -10 dBm")
    analyser.write("POW:RF:ATT 20")
    analyser.write("BAND:RES 3 kHz")

    assert analyser.query("FREQ:CENT?") == "2500000.0"
    assert analyser.query("DISP:WIND1:TRAC:Y:RLEV?") == "-10.0"
    assert analyser.query("POW:RF:ATT?") == "20.0"
    assert analyser.query("BAND:RES?") == "3.0 kHz"


def test_virtual_n9030_exposes_trace_data_and_marker_state():
    analyser = VirtualN9030()
    analyser.write_memory("trace.2.power_data", [-50.0, -40.0])

    analyser.write(":CALC:MARK4:X 1234")
    analyser.write("CALC:MARK4:STAT ON")
    analyser.write("CALC:MARK4:MODE POS")

    assert analyser.query(":TRAC:DATA? TRACE2") == "-50.0,-40.0"
    assert analyser.query("CALC:MARK4:X?") == "1234.0"
    assert analyser.query("CALC:MARK4:MODE?") == "POS"


def test_virtual_n9030_reset_restores_automatic_settings_and_identity():
    analyser = VirtualN9030()
    analyser.write("POW:RF:ATT 10")
    analyser.write("BAND:RES 6 kHz")

    analyser.write("*RST")

    assert analyser.query("POW:RF:ATT?") == "AUTO"
    assert analyser.query("BAND:RES?") == "10.0 kHz"
    assert analyser.query("*IDN?") == "Keysight,VirtualN9030,0,0"
