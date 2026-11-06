#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

import zve10_backup_info as backup_info  # noqa: E402


class BackupInfoTests(unittest.TestCase):
    def test_summary_excludes_identifiers_and_values(self):
        header = mock.Mock(
            numSubsystems=819,
            numProperties=33178,
            dataOffset=0x31DE0,
            dataSize=1031484,
        )
        parsed = mock.Mock(revision=4, size=1235740, header=header)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Backup.bin"
            path.write_bytes(b"test")
            with mock.patch.object(backup_info, "BackupFile", return_value=parsed):
                result = backup_info.inspect_backup(path)

        self.assertEqual(result["format"], "BK4")
        self.assertEqual(result["properties"], 33178)
        self.assertFalse(result["values_disclosed"])
        for forbidden in ("region", "serial", "model", "property_values", "id1"):
            self.assertNotIn(forbidden, result)

    def test_tweak_summary_omits_ids_region_and_raw_values(self):
        values = {
            "recLimit": bytes((13, 1, 0)),
            "recLimit4k": bytes((0xff, 0x7f)),
            "language": bytes((1,)) * 35,
            "palNtscSelector": b"\x01",
            "usbAppInstaller": b"\x00",
        }
        backup = mock.Mock()
        backup.readProp.side_effect = values.__getitem__
        backup.getRegion.return_value = "MODEL_CE"
        backup.getDefaultLanguages.side_effect = (
            lambda region: backup_info.BackupInterface.getDefaultLanguages(None, region)
        )

        result = backup_info.summarize_tweaks(backup)

        self.assertEqual(
            [item["name"] for item in result],
            [
                "recording_limit", "recording_limit_4k", "languages",
                "pal_ntsc_selector", "usb_app_installer",
            ],
        )
        self.assertTrue(result[0]["enabled"])
        self.assertEqual(result[0]["status"], "13h 01m 00s")
        self.assertFalse(result[-1]["enabled"])
        rendered = repr(result).lower()
        for forbidden in ("region", "serial", "property", "0x003c", "raw"):
            self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    unittest.main()
