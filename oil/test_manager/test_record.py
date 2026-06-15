
# Library imports
from typing import List, DIct
from pathlib import Path
import csv


class TestRecord:

    def __init__(self, filepath: str, columns: List[str]):
        self.filepath = Path(filepath)
        self.columns = columns

        if not self.filepath.exists():
            with self.filepath.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()

    def write(self, data: Dict):
        unknown_columns = set(data.keys()) - set(self.columns)
        if unknown_columns:
            raise ValueError(
                f"Unknown columns: {', '.join(sorted(unknown_columns))}"
            )

        row = {
            column: data.get(column, "")
            for column in self.columns
        }

        with self.filepath.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writerow(row)