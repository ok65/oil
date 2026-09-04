
# Library imports
from setuptools import setup, find_packages

# Grab version number from file
with open("VERSION", "r") as fp:
    VERSION = fp.read().strip()

# Run setup tools
setup(
    name='oil',
    version=VERSION,
    description="Oliver's Instrument Library",
    packages=find_packages(),
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial'
    ],
    license="WTFPL"
)