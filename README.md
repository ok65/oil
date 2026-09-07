# pyoil

`pyoil` is a Python library for controlling RF test equipment through PyVISA.
It currently includes drivers for the Rohde & Schwarz SMR20 signal generator,
Keysight E5071C vector network analyser, Keysight N9030 signal analyser, and a
dual-SP8T RF switch matrix.

The installed distribution is named `pyoil`; import the library as `oil`.

```bash
python -m pip install pyoil
```

```python
from oil.core import ip_address_string
from oil.sig_gens import SMR20

signal_generator = SMR20(ip_address_string("192.168.1.20"))
signal_generator.frequency = 1_000_000
signal_generator.power = -10
```

The library also provides virtual instruments for unit tests, allowing driver
behaviour to be verified without a physical instrument connection.

## Development

Run the unit suite from the project root:

```bash
python -m pytest
```

Physical-instrument smoke tests remain necessary to confirm model- and
firmware-specific SCPI behaviour.
