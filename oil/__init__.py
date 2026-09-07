from oil.core.helper import *
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("pyoil")
except PackageNotFoundError:
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    with (_PROJECT_ROOT / "VERSION").open(encoding="utf-8") as fp:
        __version__ = fp.read().strip()
