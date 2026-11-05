import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))

import zve10_backup_files as backup_files  # noqa: E402


class InventoryTest(unittest.TestCase):
    def test_uses_busybox_find_when_available(self):
        with mock.patch.object(
            backup_files,
            "run",
            return_value={"exit_code": 0, "output": "/setting/a\n/setting/b\n"},
        ) as run:
            files, errors = backup_files.inventory(object(), ["/setting"])

        self.assertEqual(files, ["/setting/a", "/setting/b"])
        self.assertEqual(errors, [])
        self.assertEqual(run.call_count, 1)
        self.assertIn("busybox find", run.call_args.args[2])

    def test_falls_back_to_recursive_shell_builtins(self):
        responses = [
            backup_files.CommandFailure("inventory", {"exit_code": 127, "output": ""}),
            {
                "exit_code": 0,
                "output": "/setting/a\r\n/setting/sub/b\r\n"
                + backup_files.INVENTORY_SENTINEL + "\r\n\r\n",
            },
        ]
        with mock.patch.object(backup_files, "run", side_effect=responses) as run:
            files, errors = backup_files.inventory(object(), ["/setting"])

        self.assertEqual(files, ["/setting/a", "/setting/sub/b"])
        self.assertEqual(errors, [])
        self.assertEqual(run.call_count, 2)
        self.assertIn("walk(){", run.call_args.args[2])

    def test_reports_both_inventory_failures(self):
        with mock.patch.object(
            backup_files,
            "run",
            side_effect=[
                backup_files.CommandFailure("inventory", {"exit_code": 127, "output": ""}),
                RuntimeError("fallback failed"),
            ],
        ):
            files, errors = backup_files.inventory(object(), ["/setting"])

        self.assertEqual(files, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("exit 127", errors[0]["error"])
        self.assertIn("fallback failed", errors[0]["error"])

    def test_fallback_shell_handles_names_dotfiles_and_symlink_loop(self):
        with tempfile.TemporaryDirectory(prefix="zve10 inventory '") as directory:
            root = Path(directory)
            (root / "plain file").write_text("x", encoding="ascii")
            (root / ".hidden").write_text("x", encoding="ascii")
            (root / "sub").mkdir()
            (root / "sub" / "nested").write_text("x", encoding="ascii")
            (root / "sub" / "loop").symlink_to(root, target_is_directory=True)
            command = backup_files.fallback_inventory_command(str(root))
            result = subprocess.run(
                ["/bin/sh", "-c", command], capture_output=True, text=True, check=False
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[-1], backup_files.INVENTORY_SENTINEL)
        self.assertEqual(
            set(lines[:-1]),
            {str(root / "plain file"), str(root / ".hidden"), str(root / "sub" / "nested")},
        )

    def test_transport_failure_does_not_run_fallback(self):
        with mock.patch.object(
            backup_files, "run", side_effect=TimeoutError("USB timed out")
        ) as run:
            files, errors = backup_files.inventory(object(), ["/setting"])

        self.assertEqual(files, [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(run.call_count, 1)

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
