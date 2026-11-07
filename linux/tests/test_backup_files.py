import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))

import zve10_backup_files as backup_files  # noqa: E402


class BackupCompletionTest(unittest.TestCase):
    def test_backup_is_incomplete_when_inventory_has_errors(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            backup_files, "metadata", return_value={}
        ), mock.patch.object(
            backup_files, "inventory", return_value=([], [{"root": "/setting", "error": "x"}])
        ):
            result = backup_files.backup(
                object(), Path(directory), "critical", max_file_bytes=0,
                max_files=0, double_read_all=False
            )

        self.assertFalse(result["completed"])


if __name__ == "__main__":
    unittest.main()
