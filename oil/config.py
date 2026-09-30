"""Load named instrument instances from a YAML configuration file."""

from pathlib import Path
from typing import Dict, Mapping, Type

import yaml

from oil.analyzers import E5071C, N9030
from oil.core.instrument import InstrumentBase
from oil.core.errors import InstrumentIdentityError
from oil.data_loggers import PT104
from oil.sig_gens import SMR20
from oil.switches import RFSwitchMatrix


_INSTRUMENT_TYPES: Dict[str, Type[InstrumentBase]] = {
    "E5071C": E5071C,
    "N9030": N9030,
    "PT104": PT104,
    "RFSwitchMatrix": RFSwitchMatrix,
    "SMR20": SMR20,
}


def load_instruments(filepath: str) -> Dict[str, InstrumentBase]:
    """Create the configured instruments and return them by name.

    YAML has an ``instruments`` mapping whose entries specify a supported
    ``type``, connection fields, and optional writable driver ``settings``.
    If an entry fails to load, already-created instruments are closed before
    the original exception is raised.
    """
    with Path(filepath).open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, Mapping) or not isinstance(config.get("instruments"), Mapping):
        raise ValueError("Configuration must contain an 'instruments' mapping")

    instruments: Dict[str, InstrumentBase] = {}
    try:
        for name, definition in config["instruments"].items():
            if not isinstance(name, str) or not name:
                raise ValueError("Instrument names must be non-empty strings")
            if not isinstance(definition, Mapping):
                raise ValueError(f"Configuration for instrument '{name}' must be a mapping")

            instrument_type = definition.get("type")
            if instrument_type not in _INSTRUMENT_TYPES:
                supported = ", ".join(sorted(_INSTRUMENT_TYPES))
                raise ValueError(
                    f"Unknown instrument type for '{name}': {instrument_type!r}. "
                    f"Supported types: {supported}"
                )

            settings = definition.get("settings", {})
            if not isinstance(settings, Mapping):
                raise ValueError(f"Settings for instrument '{name}' must be a mapping")

            expected_model = definition.get("expected_model")
            if not isinstance(expected_model, str) or not expected_model.strip():
                raise ValueError(
                    f"Instrument '{name}' requires a non-empty 'expected_model' string"
                )

            driver = _INSTRUMENT_TYPES[instrument_type]
            options = {key: value for key, value in definition.items()
                       if key not in ("type", "settings", "expected_model", "visa")}
            try:
                if instrument_type == "PT104":
                    if "visa" in definition:
                        raise ValueError("PT104 configuration uses 'serial_number', not 'visa'")
                    instrument = driver(**options)
                else:
                    visa = definition.get("visa")
                    if not isinstance(visa, str) or not visa:
                        raise ValueError(f"Instrument '{name}' requires a non-empty 'visa' string")
                    instrument = driver(visa, **options)
            except TypeError as error:
                raise ValueError(f"Invalid connection options for instrument '{name}': {error}") from error

            instruments[name] = instrument
            if settings:
                instrument.apply_config(settings)

        # Validate only after construction and settings have succeeded for the
        # full list, and before returning any of the instances to the caller.
        identity_errors = []
        for name, definition in config["instruments"].items():
            try:
                instruments[name].validate_instrument(definition["expected_model"])
            except Exception as error:
                identity_errors.append(f"{name}: {error}")
        if identity_errors:
            raise InstrumentIdentityError(
                "Instrument identity validation failed: " + "; ".join(identity_errors)
            )
    except Exception:
        for instrument in instruments.values():
            try:
                instrument.close()
            except Exception:
                pass
        raise

    return instruments
