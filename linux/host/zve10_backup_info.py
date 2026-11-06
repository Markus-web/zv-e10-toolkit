#!/usr/bin/env python3
"""Inspect Sony Backup.bin structure without printing property values or IDs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import zve10_common  # noqa: F401 - adds the pinned Sony-PMCA-RE to sys.path

from pmca.backup import BackupFile
from pmca.platform.backup import BackupFileDataInterface, BackupInterface
from pmca.platform.tweaks import (
    BooleanBackupTweak,
    LanguageTweak,
    RecLimit4kTweak,
    RecLimitTweak,
)


def inspect_backup(path: Path) -> dict:
    with path.open("rb") as handle:
        backup = BackupFile(handle)
    header = backup.header
    return {
        "format": "BK%d" % backup.revision,
        "file_size": path.stat().st_size,
        "logical_size": backup.size,
        "subsystems": header.numSubsystems,
        "properties": header.numProperties,
        "data_offset": header.dataOffset,
        "data_size": header.dataSize,
        "checksum_valid": True,
        "values_disclosed": False,
    }


def summarize_tweaks(backup: BackupInterface) -> list[dict]:
    candidates = (
        ("recording_limit", "Disable video recording limit", RecLimitTweak(backup)),
        ("recording_limit_4k", "Disable 4K recording limit", RecLimit4kTweak(backup)),
        ("languages", "Unlock all languages", LanguageTweak(backup)),
        (
            "pal_ntsc_selector", "Enable PAL/NTSC selector and warning",
            BooleanBackupTweak(backup, "palNtscSelector"),
        ),
        (
            "usb_app_installer", "Enable USB app installer",
            BooleanBackupTweak(backup, "usbAppInstaller"),
        ),
    )
    result = []
    for name, description, tweak in candidates:
        if tweak.available():
            result.append({
                "name": name,
                "description": description,
                "enabled": tweak.enabled(),
                "status": tweak.strValue(),
            })
    return result


def inspect_tweaks(path: Path) -> list[dict]:
    with path.open("rb") as handle:
        return summarize_tweaks(BackupInterface(BackupFileDataInterface(handle)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="private Backup.bin copy")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--tweaks", action="store_true",
        help="list supported hidden-tweak states without identifiers or raw values",
    )
    args = parser.parse_args()

    result = inspect_backup(args.file)
    if args.tweaks:
        result["hidden_tweaks"] = inspect_tweaks(args.file)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    for key, value in result.items():
        if key == "hidden_tweaks":
            continue
        print("%-18s %s" % (key + ":", value))
    if args.tweaks:
        print("hidden_tweaks:")
        for item in result["hidden_tweaks"]:
            state = "enabled" if item["enabled"] else "disabled"
            print("  %-20s %-8s %s" % (item["name"], state, item["status"]))


if __name__ == "__main__":
    main()
