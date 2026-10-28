import time
# Library imports
from typing import List, Dict, TYPE_CHECKING
from pathlib import Path
import csv
import json
from datetime import datetime
from uuid import NAMESPACE_DNS, uuid3, uuid4
import time

if TYPE_CHECKING:
    from paho.mqtt.client import Client


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


class MQTTTestRecord:
    """Publish timestamped test records as JSON through a connected MQTT client.

    The caller owns the client's connection, network loop, and cleanup.
    """

    def __init__(self, topic: str, columns: List[str], client: "Client",
                 test_name: str, run_name: str, operator_name: str,
                 publish_timeout: float = 10.0):
        if not topic or "+" in topic or "#" in topic:
            raise ValueError("topic must be a non-empty MQTT publish topic without wildcards")
        if publish_timeout <= 0:
            raise ValueError("publish_timeout must be positive")
        for field_name, value in (("test_name", test_name), ("run_name", run_name),
                                  ("operator_name", operator_name)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        self.topic = topic
        self.columns = list(columns)
        self.client = client
        # UUID3 is name-based; a fresh UUID4 supplies a unique name per record
        # instance. Keep the requested compact final eight hexadecimal digits.
        self.run_id = uuid3(NAMESPACE_DNS, uuid4().hex).hex[-8:]
        self.test_name = test_name
        self.run_name = run_name
        self.operator_name = operator_name
        self.publish_timeout = publish_timeout
        self.test_start_timestamp = TestRecord._timestamp()

    def write(self, row_data: Dict) -> None:
        """Publish one JSON object, waiting for its QoS 1 acknowledgement."""
        record = {column: row_data.get(column, "") for column in self.columns}
        record["run_id"] = self.run_id
        record["test_name"] = self.test_name
        record["run_name"] = self.run_name
        record["operator_name"] = self.operator_name
        record["timestamp"] = TestRecord._timestamp()
        record["test_start_timestamp"] = self.test_start_timestamp
        payload = json.dumps(record, allow_nan=False)

        info = self.client.publish(self.topic, payload, qos=1, retain=False)
        if info.rc != 0:
            raise RuntimeError(f"MQTT publish failed for topic {self.topic!r} (rc={info.rc})")

        try:
            info.wait_for_publish(timeout=self.publish_timeout)
        except (RuntimeError, ValueError) as error:
            raise RuntimeError(f"MQTT publish failed for topic {self.topic!r}") from error
        if not info.is_published():
            raise TimeoutError(f"MQTT publish timed out for topic {self.topic!r}")
