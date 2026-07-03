from setuptools import setup

setup(
    name='oil',
    version='0.0.1',
    py_modules=['oil'],
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial'
    ]
)