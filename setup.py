
# Library imports
from pathlib import Path
from setuptools import setup, find_packages

# Grab version number from file
project_root = Path(__file__).resolve().parent
with (project_root / "VERSION").open(encoding="utf-8") as fp:
    VERSION = fp.read().strip()
with (project_root / "README.md").open(encoding="utf-8") as fp:
    LONG_DESCRIPTION = fp.read()

# Run setup tools
setup(
    name='pyoil',
    version=VERSION,
    description="Python drivers and test tooling for RF instruments",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/ok65/oil",
    project_urls={
        "Homepage": "https://github.com/ok65/oil",
        "Source": "https://github.com/ok65/oil",
        "Issue tracker": "https://github.com/ok65/oil/issues",
    },
    packages=find_packages(),
    install_requires=[
        'pyvisa',
        'pyvisa-py',
        'pyserial',
        'matplotlib',
    ],
    license="WTFPL",
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
