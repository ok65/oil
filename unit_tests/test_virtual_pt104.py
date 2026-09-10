import pytest

from oil.data_loggers import PT100, PT104DataType, VirtualPT104


def test_virtual_pt104_configures_channels_and_reads_temperature():
    logger = VirtualPT104(
        {1: 23.125},
        serial_number="TEST-104-001",
    )
    logger.configure_channel(1, PT104DataType.PT100, 4)

    assert logger.read_temperature(1) == pytest.approx(23.125)
    assert logger.read_memory("channel.1.data_type") == PT104DataType.PT100
    assert logger.read_memory("channel.1.wires") == 4
    assert logger.identify() == "Pico Technology,Virtual PT-104,0,0,TEST-104-001"


def test_virtual_pt104_can_change_readings_and_reset():
    logger = VirtualPT104()
    logger.set_reading(2, 42.5)
    assert logger.read(2) == 42.5

    logger.reset()
    assert logger.read(2) == 0.0
    assert logger.read_memory("mains.frequency.hz") == 50


def test_virtual_pt104_channel_objects_are_indexed_by_integer():
    logger = VirtualPT104({1: 23.125})

    logger.channel[1].probe_type = PT100

    assert logger.channel[1].probe_type is PT100
    assert logger.channel[1].read() == pytest.approx(23.125)
