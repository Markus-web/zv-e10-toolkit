#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

import zve10_hardware_snapshot as snapshot  # noqa: E402


class HardwareSnapshotTests(unittest.TestCase):
    def test_optional_commands_do_not_fail_when_surface_is_missing(self):
        self.assertIn("echo MISSING:", snapshot.optional_cat("/proc/example"))
        self.assertIn("echo MISSING:", snapshot.optional_ls("/sys/example"))

    def test_commands_exclude_mutating_operations(self):
        commands = "\n".join(command for _name, command in snapshot.COMMANDS)
        for forbidden in (
            " dd ", "mount ", "umount ", "insmod ", "rmmod ", "modprobe ",
            "reboot", "poweroff", "> /", "/dev/mem |",
        ):
            self.assertNotIn(forbidden, " " + commands)

    def test_capture_records_all_commands_and_drops_raw_transport(self):
        def command(_dev, name, text, _timeout):
            return {
                "name": name,
                "command": text,
                "exit_code": 0,
                "output": name + "\n",
                "raw": "discarded",
            }

        with mock.patch.object(snapshot.common, "command", side_effect=command):
            result = snapshot.capture(object())

        self.assertTrue(result["completed"])
        self.assertEqual(len(result["commands"]), len(snapshot.COMMANDS))
        self.assertNotIn("raw", result["commands"][0])

    def test_command_failure_is_preserved(self):
        with mock.patch.object(snapshot.common, "command", side_effect=TimeoutError("late")):
            result = snapshot.capture(object())

        self.assertFalse(result["completed"])
        self.assertIn("TimeoutError", result["commands"][0]["error"])

    def test_outputs_are_private_machine_and_human_readable(self):
        result = {
            "started": "2026-11-06T00:00:00+0200",
            "completed": True,
            "terminal_closed": True,
            "commands": [{
                "name": "example",
                "command": "busybox cat /proc/example",
                "exit_code": 0,
                "output": "MISSING: /proc/example\n",
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            snapshot.write_outputs(out, result)
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            report = (out / "REPORT.md").read_text(encoding="utf-8")

        self.assertEqual(manifest["commands"][0]["exit_code"], 0)
        self.assertIn("MISSING", report)
        self.assertIn("Terminal closed: **True**", report)


if __name__ == "__main__":
    unittest.main()
