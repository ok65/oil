
# Library imports
import logging
from pathlib import Path
from datetime import datetime


def setup_logging():

    Path("logs").mkdir(exist_ok=True)
    logfile = datetime.now().strftime("logs/%Y%m%d_%H%M.log")

    logger = logging.getLogger("oil")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s]: %(message)s"
    )

    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File output
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger