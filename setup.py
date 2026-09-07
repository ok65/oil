
# Library imports
from pathlib import Path
from setuptools import setup, find_packages

# Grab version number from file
project_root = Path(__file__).resolve().parent
with (project_root / "VERSION").open(encoding="utf-8") as fp:
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
