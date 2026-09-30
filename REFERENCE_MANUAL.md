# Oil Reference Manual

`oil` is a small Python library for controlling test equipment. The SCPI
instrument drivers use PyVISA and expose Python properties instead of requiring
callers to compose SCPI strings. The PT-104 uses Pico Technology's native USB
SDK and is not a SCPI instrument.

## Installation

```bash
python -m pip install pyoil
```

For development and tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Common helpers

```python
from oil.core import ip_address_string, serial_port_string

tcp_resource = ip_address_string("192.168.1.20")  # TCPIP0::192.168.1.20::INSTR
serial_resource = serial_port_string(7)             # ASRL7::INSTR
```

## Loading instruments from YAML

Keep machine-specific VISA addresses and PT-104 serial numbers in a local YAML
file rather than in test scripts. Copy `oil/config.example.yaml` to
`instruments.local.yaml`, edit its connection details, and load the configured
instances by name:

```python
from oil import load_instruments

instruments = load_instruments("instruments.local.yaml")
generator = instruments["signal_generator"]
analyser = instruments["analyser"]

generator.frequency = 2_000_000
print(analyser.download_trace())

for instrument in instruments.values():
    instrument.close()
```

Each entry has a supported driver `type`, connection fields, and optional
`expected_model` substring and `settings`. The loader queries each instrument's
identification string and requires it to contain the configured model name,
case-insensitively. Settings are applied through the driver's writable
properties immediately after connecting. See `oil/config.example.yaml` for all
supported instrument types and the expected connection fields. If a
configuration entry or identity check fails, instances created in that load
are closed and the loader raises an exception.

## Fixed-address DHCP service

The optional fixed-address DHCP service is in `oil/dhcp_server.py`. Add a
`dhcp_server` section to the same local YAML file with one interface name and a
`reservations` mapping from MAC addresses to IP addresses. The interface must
have a static IPv4 address; each reservation must be a unique address on that
interface's subnet. Only listed MAC addresses receive DHCP replies. The
service has no dynamic pool and grants infinite DHCP leases for configured
addresses.

On Windows, run `start_dhcp_server.bat` as Administrator to start it in a
separate minimized console. It reads `instruments.local.yaml` beside the batch
file. Port 67 must be available. From Python, query the service with:

```python
from oil import is_dhcp_server_running

if is_dhcp_server_running("instruments.local.yaml"):
    print("DHCP service is running")
```

`python -m oil.dhcp_server instruments.local.yaml --status` provides the same
check from a command prompt.

SCPI drivers connect when instantiated and provide these common methods:

```python
instrument.reset()     # sends *RST
instrument.clear()     # sends *CLS
instrument.identify()  # queries *IDN?
instrument.close()     # closes the VISA resource
```

The drivers can also be used with a `with` statement. Explicit `close()` is
recommended when managing the lifetime manually.

## SMR20 signal generator

Import:

```python
from oil.core import ip_address_string
from oil.sig_gens import SMR20

smr20 = SMR20(ip_address_string("192.168.1.20"))
```

Properties:

| Property | Type | Meaning |
| --- | --- | --- |
| `frequency` | `float` | RF frequency in Hz |
| `power` | `float` | RF power in dBm |
| `rf_enable` | `bool` | RF output state |
| `external_reference` | `bool` | External reference state |

Example:

```python
smr20.frequency = 1_000_000
smr20.power = -10
smr20.rf_enable = True
smr20.external_reference = False

print(smr20.frequency)
print(smr20.power)
smr20.rf_enable = False
smr20.close()
```

## E5071C vector network analyser

Import and connect:

```python
from oil.analyzers import E5071C

vna = E5071C("TCPIP::192.168.1.21::INSTR")
```

The driver converts an `::INSTR` resource into the E5071C socket resource on
port 5025.

Properties:

| Property | Type | Meaning |
| --- | --- | --- |
| `frequency_center` | `float` | Center frequency in Hz |
| `frequency_start` | `float` | Start frequency in Hz |
| `frequency_stop` | `float` | Stop frequency in Hz |
| `frequency_span` | `float` | Span in Hz |
| `frequency_points` | `int` | Number of sweep points |
| `source_power` | `float` | Source power in dBm |
| `reference_level` | `float` | Display reference level |
| `scale_per_division` | `float` | Display scale per division |
| `reference_position` | `float` | Display reference position |
| `source_attenuation` | `float` | Source attenuation in dB |
| `source_attenuation_auto` | `bool` | Automatic source attenuation |
| `measurement` | `str` | S-parameter, for example `S11` or `S21` |
| `marker` | `dict` | Markers indexed from 1 to 9 |

Example:

```python
vna.frequency_center = 1_500_000
vna.frequency_span = 1_000_000
vna.frequency_points = 401
vna.source_power = -10
vna.source_attenuation_auto = True
vna.measurement = "S21"

vna.marker[1].enabled = True
vna.marker[1].frequency = 1_500_000
vna.marker[1].peak_search()
print(vna.marker[1].frequency)
print(vna.marker[1].power)

trace = vna.download_trace()
# {"frequency": [...], "level": [...]}
vna.close()
```

`download_trace(trace_id=1)` selects the requested trace and returns the
current X-axis data and formatted Y-axis data. The returned dictionary has
`frequency` and `level` lists.

Marker operations:

| Operation | Meaning |
| --- | --- |
| `vna.marker[n].frequency` | Read or set marker frequency in Hz |
| `vna.marker[n].power` | Read marker Y value |
| `vna.marker[n].enabled` | Read or set marker enable state |
| `vna.marker[n].peak_search()` | Move marker to the maximum trace point |

## N9030 spectrum analyser

Import and connect:

```python
from oil.analyzers import N9030

analyser = N9030("TCPIP::192.168.1.22::INSTR")
```

Properties:

| Property | Type | Meaning |
| --- | --- | --- |
| `frequency_center` | `float` | Center frequency in Hz |
| `frequency_start` | `float` | Start frequency in Hz |
| `frequency_stop` | `float` | Stop frequency in Hz |
| `frequency_span` | `float` | Span in Hz |
| `frequency_points` | `int` | Number of sweep points; read-only |
| `ref_level` | `float` | Reference level in dBm |
| `input_attenuation` | `float` | Input attenuation in dB; `0` represents AUTO on readback |
| `rbw` | `float` | Resolution bandwidth in Hz |
| `marker` | `dict` | Markers indexed from 1 to 12 |

Example:

```python
analyser.frequency_center = 2_500_000
analyser.frequency_start = 2_000_000
analyser.frequency_stop = 3_000_000
analyser.frequency_span = 1_000_000
analyser.ref_level = -10
analyser.input_attenuation = 20
analyser.rbw = 10_000  # Hz

analyser.marker[1].enabled = True
analyser.marker[1].frequency = 2_500_000
analyser.marker[1].peak_search()
analyser.marker[1].next_peak_right()
analyser.marker[1].next_peak_left()

trace = analyser.download_trace()
# {"frequency": [...], "power": [...]}
analyser.close()
```

Marker operations:

| Operation | Meaning |
| --- | --- |
| `analyser.marker[n].frequency` | Read or set marker frequency in Hz |
| `analyser.marker[n].power` | Read marker power in dBm |
| `analyser.marker[n].enabled` | Read or set marker state |
| `analyser.marker[n].peak_search()` | Search for the maximum peak |
| `analyser.marker[n].next_peak_right()` | Search for the next peak to the right |
| `analyser.marker[n].next_peak_left()` | Search for the next peak to the left |

## RF switch matrix

Import and connect:

```python
from oil.switches import RFSwitchMatrix

switch = RFSwitchMatrix("TCPIP::192.168.1.23::INSTR")
```

The driver converts an `::INSTR` resource to the switch socket on port 5025.

Properties:

| Property | Type | Meaning |
| --- | --- | --- |
| `rfa` | `int` | RFA port, from 1 to 8 |
| `rfb` | `int` | RFB port, from 1 to 8 |

Example:

```python
switch.rfa = 3
switch.rfb = 7
print(switch.rfa)
print(switch.rfb)
switch.reset()
switch.close()
```

## PT-104 temperature logger

The PT-104 uses Pico Technology's native `usbpt104` SDK over USB. It does not
use VISA or SCPI. PicoSDK must be installed separately on the host.

### Device discovery and connection

```python
from oil.data_loggers import PT104

devices = PT104.list_devices()
print(devices)  # for example: ["CT264/118", "CT264/119"]

pt104 = PT104()                         # auto-connect first USB device
pt104_specific = PT104(serial_number="CT264/119")
```

`serial_number=0` is the default and preserves the convenient single-device
behaviour. Call `close()` when finished:

```python
pt104.close()
pt104_specific.close()
```

The driver also supports `with PT104(...) as pt104`, but an explicit lifetime
is often more convenient for long-running test programs.

### Identification

```python
print(pt104.identify())
# Pico Technology,PT-104,<variant>,<batch-and-serial>
```

The real driver obtains variant and serial information from the SDK.

### Channel objects

Four parent-owned channel objects are available through the read-only
`channel` property and are indexed with integers from 1 to 4.

```python
from oil.data_loggers import PT100

pt104.channel[1].probe_type = PT100
pt104.channel[1].wires = 4
temperature_c = pt104.channel[1].read()
print(f"{temperature_c:.3f} °C")
```

Channel members:

| Member | Meaning |
| --- | --- |
| `channel[n].probe_type` | Read or set the sensor type |
| `channel[n].wires` | Read or set PT100/PT1000 wire count |
| `channel[n].configure(type, wires=4)` | Configure both values |
| `channel[n].read(filtered=True)` | Read the latest value |

Direct parent methods are also available:

```python
pt104.configure_channel(1, PT100, wires=4)
temperature_c = pt104.read_temperature(1)
temperature_c = pt104.read(1, filtered=False)
pt104.set_mains_frequency(50)  # or 60
```

Supported data types:

| Name | SDK value | Meaning |
| --- | ---: | --- |
| `PT104DataType.OFF` | 0 | Disable channel |
| `PT104DataType.PT100` / `PT100` | 1 | PT100 RTD |
| `PT104DataType.PT1000` / `PT1000` | 2 | PT1000 RTD |
| `PT104DataType.RESISTANCE_375R` | 3 | 0–375 Ω resistance |
| `PT104DataType.RESISTANCE_10KR` | 4 | 0–10 kΩ resistance |
| `PT104DataType.VOLTAGE_115MV` | 5 | 0–115 mV differential voltage |
| `PT104DataType.VOLTAGE_2_5V` | 6 | 0–2.5 V differential voltage |

`PT100` and `PT1000` are convenience aliases exported from
`oil.data_loggers`.

## Test manager

The test manager creates the Cartesian product of sweeps and actions.

```python
from oil.test_manager import (
    ListSweep,
    ParameterSweep,
    TestAction,
    TestManager,
    TestRecord,
)

def set_frequency(iteration, value):
    generator.frequency = value
    iteration.data["frequency_hz"] = value

def record_measurement(iteration, _unused):
    iteration.data["measured_dbm"] = analyser.marker[1].power
    record.write(iteration.data)

record = TestRecord(
    "measurements.csv",
    ["frequency_hz", "measured_dbm"],
)

test = TestManager([
    ParameterSweep("frequency", set_frequency, 1_000_000, 2_000_000, 500_000),
    ListSweep("measurement", record_measurement, [None]),
])

test.run()
```

Classes and methods:

| Class | Use |
| --- | --- |
| `TestAction(name, value, execute)` | One action in an iteration |
| `ParameterSweep(name, execute, start, stop, step)` | Numeric inclusive sweep |
| `ListSweep(name, execute, values)` | Ordered list sweep |
| `TestIteration(actions, test_manager)` | One combination of actions |
| `TestManager(actions)` | Build and run all combinations |
| `TestRecord(filepath, columns)` | Append timestamped CSV rows |
| `TestParameter(...)` | Legacy/helper numeric parameter representation |

`TestManager` also exposes `info()`, `warn()`, and `error()` logging helpers.
`TestRecord.write()` ignores undeclared data keys and writes blank values for
declared columns that are missing.

## Plotting traces

```python
from oil.core import plot_trace

trace = analyser.download_trace()
plot_trace(trace)
```

The trace dictionary must contain a `frequency` list and exactly one other
measurement list of the same length.
