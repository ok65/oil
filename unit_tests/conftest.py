"""Shared fixtures for driver tests that run without physical instruments."""

import pytest

import oil.core.instrument as instrument_module
from oil.analyzers import E5071C, VirtualE5071C, N9030, VirtualN9030
from oil.sig_gens import SMR20, VirtualSMR20
from oil.switches import RFSwitchMatrix, VirtualRFSwitchMatrix


class VirtualResourceManager:
    """Minimal ResourceManager replacement that returns one virtual device."""

    def __init__(self, resource):
        self.resource = resource
        self.opened_addresses = []

    def open_resource(self, address):
        self.opened_addresses.append(address)
        return self.resource


@pytest.fixture
def virtual_rf_switch():
    return VirtualRFSwitchMatrix()


@pytest.fixture
def rf_switch_driver(monkeypatch, virtual_rf_switch):
    """Connect the real driver to its virtual device through fake PyVISA."""
    resource_manager = VirtualResourceManager(virtual_rf_switch)
    monkeypatch.setattr(
        instrument_module.pyvisa,
        "ResourceManager",
        lambda backend: resource_manager,
    )

    driver = RFSwitchMatrix("TCPIP::127.0.0.1::INSTR")
    return driver, virtual_rf_switch, resource_manager


def _connect_driver(monkeypatch, driver_type, virtual_instrument, visa_string):
    resource_manager = VirtualResourceManager(virtual_instrument)
    monkeypatch.setattr(
        instrument_module.pyvisa,
        "ResourceManager",
        lambda backend: resource_manager,
    )
    return driver_type(visa_string), resource_manager


@pytest.fixture
def smr20_driver(monkeypatch):
    virtual_instrument = VirtualSMR20()
    driver, resource_manager = _connect_driver(
        monkeypatch, SMR20, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager


@pytest.fixture
def e5071c_driver(monkeypatch):
    virtual_instrument = VirtualE5071C()
    driver, resource_manager = _connect_driver(
        monkeypatch, E5071C, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager


@pytest.fixture
def n9030_driver(monkeypatch):
    virtual_instrument = VirtualN9030()
    driver, resource_manager = _connect_driver(
        monkeypatch, N9030, virtual_instrument, "TCPIP::127.0.0.1::INSTR",
    )
    return driver, virtual_instrument, resource_manager
