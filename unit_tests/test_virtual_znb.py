from oil.analyzers import VirtualZNB


def test_virtual_znb_supports_trace_selection_data_and_marker_peak():
    analyser = VirtualZNB()
    analyser.write_memory("trace.2.frequency_data", [10.0, 20.0, 30.0])
    analyser.write_memory("trace.2.formatted_data", [-8.0, -2.0, -5.0])

    analyser.write("CALC1:PAR:SEL 'Trc2'")
    analyser.write("CALC1:MARK3:FUNC:TYPE MAX")
    analyser.write("CALC1:MARK3:FUNC:EXEC")

    assert analyser.query("CALC1:DATA:STIM?") == "10.0,20.0,30.0"
    assert analyser.query("CALC1:DATA? FDAT") == "-8.0,-2.0,-5.0"
    assert analyser.query("CALC1:MARK3:X?") == "20.0"
    assert analyser.query("CALC1:MARK3:Y?") == "-2.0"


def test_virtual_znb_trace_definition_and_reset_restore_default_state():
    analyser = VirtualZNB()
    analyser.write("CALC1:PAR:SDEF 'Trc1','S11'")
    assert analyser.query("CALC1:PAR:MEAS? 'Trc1'") == "S11"

    analyser.write("*RST")

    assert analyser.query("CALC1:PAR:MEAS? 'Trc1'") == "S21"
    assert analyser.read_memory("selected_trace") == 1
    assert analyser.query("*IDN?") == "Rohde&Schwarz,VirtualZNB,0,0"
