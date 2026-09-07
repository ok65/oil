from unittest.mock import Mock

import pytest

import oil.core.helper as helper


def test_visa_address_helpers_format_serial_and_tcpip_addresses():
    assert helper.serial_port_string(7) == "ASRL7::INSTR"
    assert helper.ip_address_string("192.168.1.20") == "TCPIP0::192.168.1.20::INSTR"


@pytest.mark.parametrize(
    "trace_data",
    [
        {"frequency": [1.0], "power": [2.0], "phase": [3.0]},
        {"frequency": [1.0]},
    ],
)
def test_plot_trace_rejects_missing_or_ambiguous_measurements(trace_data):
    with pytest.raises(ValueError, match="exactly one measurement"):
        helper.plot_trace(trace_data)


def test_plot_trace_rejects_mismatched_data_lengths():
    with pytest.raises(ValueError, match="same length"):
        helper.plot_trace({"frequency": [1.0, 2.0], "power": [-10.0]})


def test_plot_trace_configures_a_plot_for_one_measurement(monkeypatch):
    plot = Mock()
    monkeypatch.setattr(helper.plt, "figure", Mock())
    monkeypatch.setattr(helper.plt, "plot", plot)
    monkeypatch.setattr(helper.plt, "xlabel", Mock())
    monkeypatch.setattr(helper.plt, "ylabel", Mock())
    monkeypatch.setattr(helper.plt, "title", Mock())
    monkeypatch.setattr(helper.plt, "grid", Mock())
    monkeypatch.setattr(helper.plt, "tight_layout", Mock())
    monkeypatch.setattr(helper.plt, "show", Mock())

    helper.plot_trace({"frequency": [1.0, 2.0], "level": [-10.0, -5.0]})

    plot.assert_called_once_with([1.0, 2.0], [-10.0, -5.0])
    helper.plt.ylabel.assert_called_once_with("Level")
    helper.plt.show.assert_called_once_with()
