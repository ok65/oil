# Oliver's Instrument Library (`pyoil`)

<img src="assets/oil-logo.png" alt="OIL project logo"  height="300">

Oliver's Instrument Library is an open-source collection of test-equipment
driver code that saves me from having to write the same instrument control
layer over and over. It is built around [PyVISA](https://pyvisa.readthedocs.io/),
but presents supported instrument features as Pythonic getters and setters so
normal use does not require hand-crafted SCPI commands.

The PyPI distribution is named `pyoil`; import it as `oil`.

```bash
python -m pip install pyoil
```

## Supported instruments

- Rohde & Schwarz SMR20 signal generator
- Keysight E5071C vector network analyser
- Keysight N9030 signal analyser
- Dual-SP8T RF switch matrix
- Pico Technology PT-104 temperature/resistance data logger

The supported surface is deliberately small and explicit. Instrument- and
firmware-specific behaviour still needs a physical-instrument smoke test
before it is relied on in production.

The PT-104 uses Pico's native `usbpt104` SDK rather than VISA/SCPI. Install
PicoSDK separately, then use `oil.data_loggers.PT104`.

With more than one USB PT-104 connected, discover and select devices by serial
number. The default `serial_number=0` keeps the single-device convenience
behaviour and opens the first device found:

```python
from oil.data_loggers import PT104

serial_numbers = PT104.list_devices()
logger = PT104()                         # first USB PT-104
logger_two = PT104(serial_number=serial_numbers[1])
```

Each PT-104 exposes four parent-owned channel objects, indexed by integer:

```python
from oil.data_loggers import PT100

logger.channel[1].probe_type = PT100
temperature_c = logger.channel[1].read()
```

## Instrument control

Create a driver with its VISA resource string, then use properties rather
than composing SCPI messages yourself:

```python
from oil.core import ip_address_string
from oil.sig_gens import SMR20

signal_generator = SMR20(ip_address_string("192.168.1.20"))
signal_generator.frequency = 1_000_000
signal_generator.power = -10
signal_generator.rf_enable = True

print(signal_generator.frequency)  # 1000000.0
```

## Product-based test runs

`TestManager` turns sweeps into the Cartesian product of their values. For
example, two frequencies and three power levels create six sequential test
iterations. Each action receives the current `TestIteration`, which provides a
`data` dictionary for passing settings and measurements to later actions.

This example sets an SMR20 and N9030 to each frequency, sweeps generator
power, peak-searches the analyser, and records the result:

```python
from oil.analyzers import N9030
from oil.core import ip_address_string
from oil.sig_gens import SMR20
from oil.test_manager import ListSweep, ParameterSweep, TestAction, TestManager, TestRecord

generator = SMR20(ip_address_string("192.168.1.20"))
analyser = N9030(ip_address_string("192.168.1.21"))
record = TestRecord(
    "measured_power.csv",
    ["frequency_hz", "generator_power_dbm", "measured_power_dbm"],
)


def set_frequency(iteration, frequency_hz):
    generator.frequency = frequency_hz
    analyser.frequency_center = frequency_hz
    iteration.data["frequency_hz"] = frequency_hz


def set_power(iteration, power_dbm):
    generator.power = power_dbm
    iteration.data["generator_power_dbm"] = power_dbm


def measure_and_record(iteration, _unused):
    marker = analyser.marker[1]
    marker.enabled = True
    marker.peak_search()
    iteration.data["measured_power_dbm"] = marker.power
    record.write(iteration.data)


test = TestManager([
    ParameterSweep("frequency", set_frequency, 1_000_000, 2_000_000, 1_000_000),
    ListSweep("power", set_power, [-20, -10, 0]),
    TestAction("measure", 0, measure_and_record),
])

generator.rf_enable = True
test.run()
generator.rf_enable = False
```

`ParameterSweep` includes both endpoints when the interval is divisible by the
step. `ListSweep` preserves the supplied order. Use `TestAction` for a single
operation that should be included in every product combination.

## Test records

`TestRecord` creates a CSV with the columns you specify plus `timestamp`. It
opens the file only while writing a row, which keeps each completed row on disk
if the process stops unexpectedly. Extra keys in `iteration.data` are ignored;
declared columns without a value are written as empty cells.

The example above produces rows shaped like:

```csv
frequency_hz,generator_power_dbm,measured_power_dbm,timestamp
1000000,-20,-20.14,2026-09-07-22:32:08
```

## Test logging

Each `TestManager` configures an `oil` logger. Informational progress is shown
on the console; a timestamped log file is written under `logs/` in the current
working directory and includes debug-level messages. Use the manager's helper
methods from actions when a run needs contextual messages:

```python
def verify_power(iteration, _unused):
    measured = iteration.data["measured_power_dbm"]
    if measured < -25:
        iteration.test_manager.error(f"Power too low: {measured:.2f} dBm")
    else:
        iteration.test_manager.info(f"Power OK: {measured:.2f} dBm")
```

## Virtual instruments and unit tests

Virtual versions of the supported instruments run the same driver-level API
without a VISA connection. They make unit tests deterministic and let driver
tests assert the SCPI contract at the virtual boundary; they are not a
substitute for hardware verification.

```python
from oil.sig_gens import VirtualSMR20

generator = VirtualSMR20()
generator.frequency = 2_400_000_000
generator.power = -5

assert generator.frequency == 2_400_000_000
assert generator.power == -5
```

Run the project unit suite from the repository root:

```bash
python -m pytest
```
