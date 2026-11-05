from oil.positioners import VirtualMaturoTurntable


def test_virtual_maturo_applies_register_load_and_goto_commands():
    table = VirtualMaturoTurntable()

    table.write("LD 1 DV")
    table.write("LD 123.4 DG NP")

    assert table.query("CP") == "    0"
    assert table.query("NP") == "123.4"
    table.write("GO")

    assert table.read_memory("positioner.address") == 1
    assert table.read_memory("position.target.degrees") == 123.4
    assert table.query("CP") == "123.4"
    assert table.query("BU") == "0"


def test_virtual_maturo_continuous_motion_stops_at_limit():
    table = VirtualMaturoTurntable()
    table.write("LD 20 DG WL")
    table.write("CW")

    assert table.query("BU") == "1"
    assert table.query("CP") == "  0.5"
    table.write("ST")

    assert table.query("BU") == "0"
    assert table.query("CP") == "  0.5"


def test_virtual_maturo_reset_restores_table_defaults():
    table = VirtualMaturoTurntable()
    table.write("LD 1 DV")
    table.write("LD 55 DG NP GO")
    table.write("*RST")

    assert table.query("CP") == "    0"
    assert table.query("SP") == "    8"
    assert table.query("WL") == "  400"
    assert table.query("CL") == " -200"
