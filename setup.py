from setuptools import setup

setup(
    name='oil',
    version='0.0.2',
    py_modules=['oil'],
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial'
    ]
)