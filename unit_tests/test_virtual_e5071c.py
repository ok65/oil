from oil.analyzers import VirtualE5071C


def test_virtual_e5071c_stores_scalar_commands_in_shared_memory():
    analyser = VirtualE5071C()

    analyser.write("SENS1:FREQ:STAR 2000000")
    analyser.write("SENS1:SWE:POIN 401")
    analyser.write("SOUR1:POW -5")
    analyser.write("SOUR1:POW:ATT:AUTO OFF")
    analyser.write("CALC1:PAR1:DEF S11")

    assert analyser.read_memory("frequency.start.hz") == 2_000_000.0
    assert analyser.read_memory("frequency.points") == 401
    assert analyser.query("SOUR1:POW?") == "-5.0"
    assert analyser.query("SOUR1:POW:ATT:AUTO?") == "0"
    assert analyser.query("CALC1:PAR1:DEF?") == "S11"


def test_virtual_e5071c_download_data_and_marker_peak_are_trace_specific():
    analyser = VirtualE5071C()
    analyser.write_memory("trace.2.frequency_data", [10.0, 20.0, 30.0])
    analyser.write_memory("trace.2.formatted_data", [-8.0, 0.0, -2.0, 0.0, -5.0, 0.0])

    analyser.write("CALC1:PAR2:SEL")
    analyser.write("CALC1:MARK3:FUNC:TYPE MAX")
    analyser.write("CALC1:MARK3:FUNC:EXEC")

    assert analyser.query("CALC1:DATA:XAX?") == "10.0,20.0,30.0"
    assert analyser.query("CALC1:DATA:FDAT?") == "-8.0,0.0,-2.0,0.0,-5.0,0.0"
    assert analyser.query("CALC1:MARK3:X?") == "20.0"
    assert analyser.query("CALC1:MARK3:Y?") == "-2.0"


def test_virtual_e5071c_reset_restores_default_measurement_and_trace():
    analyser = VirtualE5071C()
    analyser.write("CALC1:PAR1:DEF S44")
    analyser.write("CALC1:PAR4:SEL")

    analyser.write("*RST")

    assert analyser.query("CALC1:PAR1:DEF?") == "S21"
    assert analyser.read_memory("selected_trace") == 1
    assert analyser.query("*IDN?") == "Keysight,VirtualE5071C,0,0"
