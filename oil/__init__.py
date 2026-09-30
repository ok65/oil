from oil.core.helper import *
from oil.config import load_instruments
from oil.dhcp_server import is_dhcp_server_running
from importlib.metadata import PackageNotFoundError, version as distribution_version
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VERSION_FILE = _PROJECT_ROOT / "VERSION"

if _VERSION_FILE.is_file():
    # A checkout takes precedence over metadata from an older installed copy.
    # The VERSION file is not installed inside the wheel, so installed packages
    # use their immutable distribution metadata below.
    with _VERSION_FILE.open(encoding="utf-8") as fp:
        __version__ = fp.read().strip()
else:
    try:
        __version__ = distribution_version("pyoil")
    except PackageNotFoundError:
        __version__ = "unknown"
