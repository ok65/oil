
# Library imports
from typing import List, Dict
from pathlib import Path
import csv
from datetime import datetime


class TestRecord:
    """
    Simple test record class to wrap around writing rows of data into a csv file in a safe manner.
    """
    def __init__(self, filepath: str, columns: List[str]):
        """
        Simple class to manage a csv test record. Class is designed to be crash-safe, so the file is only open whilst
        performing a write. Valid data should be stored in there at all times (unless it crashes during the write).

        If you specify a filepath that doesn't exist, a new file will be created. If it already exists, it will
        continue to append to the existing one. In this case the columns paramter is ignored.
        :param filepath: Path to store file to.
        :param columns: List of names for each column
        """
        # Store the filepath
        self.filepath = Path(filepath)

        # If the file doesn't exist, create it
        if not self.filepath.exists():
            with self.filepath.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[*columns, "timestamp"])
                writer.writeheader()

    def write(self, row_data: Dict):
        """
        Write function to write a single row into the database
        :param row_data: Dictionary of values
        :return:
        """
        # Open the csv
        with self.filepath.open("a+", newline="") as f:
            # Move to beginning of file, and pull the fieldnames using a reader
            f.seek(0)
            fieldnames = None
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            # Redefine row data to ignore keys not in the csv fieldnames already,
            # and put empty string for values not present
            row_data = {k: row_data.get(k, "") for k in fieldnames}

            # Insert timestamp into the data
            row_data["timestamp"] = self._timestamp()

            # Move to end of file, and write the data
            f.seek(0, 2)
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(row_data)

    @staticmethod
    def _timestamp() -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d-%H:%M:%S")