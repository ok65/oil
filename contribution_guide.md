# Contribution Guide

These conventions keep instrument drivers predictable and make changes easier
to review. Follow them for new code and when updating existing code nearby.

## Units and naming

- Express every frequency value in **Hz** at the Python API boundary, in stored
  simulator state, and in examples and documentation. Use names such as
  `frequency_hz` when a variable or data column needs its unit made explicit.
- Keep conversions to instrument-specific units inside the driver and document
  any conversion at the property that performs it.
- Include units in names for measured or recorded quantities when ambiguity is
  possible, such as `_dbm`, `_db`, and `_c`.

## Instrument drivers

- Expose supported instrument features through small, documented Python
  properties and methods rather than requiring callers to compose SCPI strings.
- Keep SCPI command strings in the relevant driver and validate user-provided
  values before sending commands where practical.
- Keep each virtual instrument aligned with the real driver's supported
  command and query contract. Use it to exercise behavior without hardware.
- Close instrument resources explicitly, or use a context manager when one is
  available.

## Python style

- Follow the surrounding code's formatting, naming, and typing conventions.
- Prefer descriptive names and focused methods; avoid unrelated refactoring in
  feature changes.
- Raise clear, specific exceptions for invalid input and unsupported
  operations.

## Tests and documentation

- Add or update focused tests for changed driver behavior, including simulator
  behavior when its command contract changes.
- Keep `REFERENCE_MANUAL.md` and relevant examples consistent with the public
  API, including units and read-only properties.
- Do not claim simulator coverage proves behavior on physical equipment;
  verify instrument- and firmware-specific behavior on hardware when needed.
- Keep changes scoped to the feature and explain externally visible behavior
  changes in the documentation.
