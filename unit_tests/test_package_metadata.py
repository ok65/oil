"""Regression tests for package metadata that must not depend on the CWD."""

import os
from pathlib import Path
import subprocess
import sys


def test_importing_oil_from_another_working_directory_reads_its_version():
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [
        str(project_root),
        environment.get("PYTHONPATH"),
    ]))

    result = subprocess.run(
        [sys.executable, "-c", "import oil; print(oil.__version__)"],
        cwd=Path(__file__).resolve().parent,
        env=environment,
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout.strip() == (project_root / "VERSION").read_text().strip()
