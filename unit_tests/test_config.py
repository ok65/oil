import pytest

from oil import load_instruments
from oil.analyzers import N9030, VirtualN9030
from oil.core.errors import InstrumentIdentityError


def test_load_instruments_creates_named_drivers_and_applies_settings(
        tmp_path, monkeypatch):
    config_file = tmp_path / "instruments.yaml"
    config_file.write_text(
        """instruments:
  analyser:
    type: N9030
    expected_model: VirtualN9030
    visa: TCPIP::127.0.0.1::INSTR
    settings:
      frequency_center: 2500000
      rbw: 10000
""",
        encoding="utf-8",
    )
    virtual_instrument = VirtualN9030()
    virtual_instrument.closed = False
    virtual_instrument.close = lambda: setattr(virtual_instrument, "closed", True)

    def connect_virtual(self):
        self._instr = virtual_instrument
        self._instr.read_termination = "\\n"
        self._instr.write_termination = "\\n"
        self._instr.timeout = 5_000

    monkeypatch.setattr(N9030, "_connect", connect_virtual)

    instruments = load_instruments(str(config_file))

    assert list(instruments) == ["analyser"]
    assert instruments["analyser"].frequency_center == 2_500_000
    assert instruments["analyser"].rbw == 10_000
    instruments["analyser"].close()


def test_load_instruments_rejects_invalid_root(tmp_path):
    config_file = tmp_path / "instruments.yaml"
    config_file.write_text("not_instruments: {}", encoding="utf-8")

    with pytest.raises(ValueError, match="'instruments' mapping"):
        load_instruments(str(config_file))


def test_load_instruments_closes_created_instances_when_later_entry_fails(
        tmp_path, monkeypatch):
    config_file = tmp_path / "instruments.yaml"
    config_file.write_text(
        """instruments:
  first:
    type: N9030
    expected_model: VirtualN9030
    visa: TCPIP::127.0.0.1::INSTR
  second:
    type: unknown
""",
        encoding="utf-8",
    )
    virtual_instrument = VirtualN9030()
    virtual_instrument.closed = False
    virtual_instrument.close = lambda: setattr(virtual_instrument, "closed", True)

    def connect_virtual(self):
        self._instr = virtual_instrument

    monkeypatch.setattr(N9030, "_connect", connect_virtual)

    with pytest.raises(ValueError, match="Unknown instrument type"):
        load_instruments(str(config_file))

    assert virtual_instrument.closed is True


def test_load_instruments_validates_model_and_closes_on_identity_mismatch(
        tmp_path, monkeypatch):
    config_file = tmp_path / "instruments.yaml"
    config_file.write_text(
        """instruments:
  analyser:
    type: N9030
    expected_model: N9030A
    visa: TCPIP::127.0.0.1::INSTR
""",
        encoding="utf-8",
    )
    virtual_instrument = VirtualN9030()
    virtual_instrument.closed = False
    virtual_instrument.close = lambda: setattr(virtual_instrument, "closed", True)
    monkeypatch.setattr(N9030, "_connect", lambda self: setattr(self, "_instr", virtual_instrument))

    with pytest.raises(InstrumentIdentityError, match="Expected instrument model 'N9030A'"):
        load_instruments(str(config_file))

    assert virtual_instrument.closed is True
