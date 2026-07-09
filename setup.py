
# Library imports
from setuptools import setup

# Grab version number from file
with open("VERSION", "r") as fp:
    VERSION = fp.read().strip()

# Run setup tools
setup(
    name='oil',
    version=VERSION,
    description="Oliver's Instrument Library",
    pacakges=['oil'],
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial'
    ],
    license="WTFPL"
)