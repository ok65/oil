import pytest

from oil.data_loggers import PT100, PT104, PT104ChannelNotConfiguredError, PT104DataType


class FakeSDK:
    def __init__(self):
        self.value = 23125
        self.get_value_status = 0
        self.calls = []
        self.devices = b"USB:TEST-104-001,USB:TEST-104-002"

    def UsbPt104OpenUnit(self, handle, port):
        serial = None if port in (0, None) else port.value.decode()
        self.calls.append(("open", serial))
        return 0

    def UsbPt104Enumerate(self, details, length, communication_type):
        details.value = self.devices
        length._obj.value = len(self.devices)
        self.calls.append(("enumerate", communication_type))
        return 0

    def UsbPt104CloseUnit(self, handle):
        self.calls.append(("close",))
        return 0

    def UsbPt104SetMains(self, handle, sixty):
        self.calls.append(("mains", sixty))
        return 0

    def UsbPt104SetChannel(self, handle, channel, data_type, wires):
        self.calls.append(("channel", channel, data_type, wires))
        return 0

    def UsbPt104GetValue(self, handle, channel, value, filtered):
        if self.get_value_status:
            return self.get_value_status
        value._obj.value = self.value
        self.calls.append(("read", channel, filtered))
        return 0

    def UsbPt104GetUnitInfo(self, handle, buffer, buffer_length, required_size, info):
        value = {3: b"PT-104", 4: b"TEST-104-001"}[info]
        buffer.value = value
        required_size._obj.value = len(value) + 1
        return 0


def test_pt104_configures_and_scales_temperature():
    sdk = FakeSDK()
    with PT104(sdk=sdk) as logger:
        logger.set_mains_frequency(50)
        logger.configure_channel(1, PT104DataType.PT100, 4)
        assert logger.read_temperature(1) == pytest.approx(23.125)
    assert sdk.calls[0] == ("open", None)
    assert sdk.calls[-1] == ("close",)


def test_pt104_lists_usb_devices_and_opens_selected_serial():
    sdk = FakeSDK()

    assert PT104.list_devices(sdk=sdk) == ["TEST-104-001", "TEST-104-002"]
    logger = PT104(serial_number="TEST-104-002", sdk=sdk)

    assert ("open", "TEST-104-002") in sdk.calls
    logger.close()


def test_pt104_rejects_invalid_channel():
    logger = PT104(sdk=FakeSDK())
    with pytest.raises(ValueError, match="integer from 1 to 4"):
        logger.read_temperature(5)
    logger.close()


def test_pt104_reports_unconfigured_channel():
    sdk = FakeSDK()
    sdk.get_value_status = 0x25
    logger = PT104(sdk=sdk)
    with pytest.raises(PT104ChannelNotConfiguredError, match="channel 1 is not configured"):
        logger.read_temperature(1)
    logger.close()


def test_pt104_channel_objects_configure_and_read():
    sdk = FakeSDK()
    logger = PT104(sdk=sdk)

    logger.channel[1].probe_type = PT100

    assert logger.channel[1].probe_type is PT100
    assert logger.channel[1].wires == 4
    assert logger.channel[1].read() == pytest.approx(23.125)
    logger.close()


def test_pt104_identify_reads_sdk_metadata():
    logger = PT104(sdk=FakeSDK())
    assert logger.identify() == "Pico Technology,PT-104,PT-104,TEST-104-001"
    logger.close()
