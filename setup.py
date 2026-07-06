from setuptools import setup

setup(
    name='oil',
    version='0.0.7',
    description="Oliver's Instrument Library",
    pacakges=['oil'],
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial'
    ],
    license="WTFPL"
)