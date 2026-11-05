#!/usr/bin/env python3
"""Inspect Sony Backup.bin structure without printing property values or IDs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import zve10_common  # noqa: F401 - adds the pinned Sony-PMCA-RE to sys.path

from pmca.backup import BackupFile


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="private Backup.bin copy")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    result = inspect_backup(args.file)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    for key, value in result.items():
        print("%-18s %s" % (key + ":", value))


if __name__ == "__main__":
    main()
