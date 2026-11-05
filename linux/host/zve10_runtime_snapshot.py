#!/usr/bin/env python3
"""Capture volatile, read-only ZV-E10 Linux state over the service terminal.

The snapshot complements raw and file backups with data that exists only while
the camera is running: kernel command line, loaded modules, interrupts, memory
map, mounts, device classes, and the kernel log. It never accesses block-device
nodes and never enables the terminal's write mode.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import zve10_common as common


COMMANDS = (
    ("firmware_version", "busybox cat /version.txt"),
    ("kernel_version", "busybox cat /proc/version"),
    ("kernel_cmdline", "busybox cat /proc/cmdline"),
    ("cpuinfo", "busybox cat /proc/cpuinfo"),
    ("meminfo", "busybox cat /proc/meminfo"),
    ("modules", "busybox cat /proc/modules"),
    ("interrupts", "busybox cat /proc/interrupts"),
    ("iomem", "busybox cat /proc/iomem"),
    ("devices", "busybox cat /proc/devices"),
    ("filesystems", "busybox cat /proc/filesystems"),
    ("mounts", "busybox cat /proc/mounts"),
    ("partitions", "busybox cat /proc/partitions"),
    ("uptime", "busybox cat /proc/uptime"),
    ("dmesg", "busybox dmesg"),
    ("input_classes", "busybox ls -la /sys/class/input"),
    ("tty_classes", "busybox ls -la /sys/class/tty"),
)


def capture(dev) -> dict:
    result = {
        "tool": "zve10_runtime_snapshot.py",
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "camera_side_writes": (
            "none by this tool; service authentication may update "
            "/setting/.etools and /setting/.hasp"
        ),
        "commands": [],
        "completed": False,
    }
    for name, command in COMMANDS:
        print("CAPTURE: " + name, flush=True)
        try:
            record = common.command(dev, name, command, 60)
            record.pop("raw", None)
        except Exception as exc:  # noqa: BLE001
            record = {"name": name, "command": command, "error": repr(exc)}
        result["commands"].append(record)
    result["completed"] = all(
        item.get("exit_code") == 0 and "error" not in item
        for item in result["commands"]
    )
    return result


def write_outputs(out: Path, result: dict) -> None:
    manifest = out / "manifest.json"
    manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.chmod(manifest, 0o600)

    lines = [
        "# ZV-E10 runtime snapshot",
        "",
        "Started: %s" % result["started"],
        "Completed: **%s**" % result["completed"],
        "Terminal closed: **%s**" % result.get("terminal_closed", False),
        "",
        "| capture | exit | bytes |",
        "|---|---:|---:|",
    ]
    for item in result["commands"]:
        output = item.get("output", "")
        status = item.get("exit_code", "error")
        lines.append("| `%s` | %s | %d |" % (item["name"], status, len(output)))
    lines += [
        "",
        "The full command output is stored in `manifest.json`. This tool does not",
        "access camera block-device nodes or enable terminal write mode.",
        "",
    ]
    report = out / "REPORT.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(report, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="output directory (default: ./backups/...)")
    parser.add_argument("--driver", default="libusb")
    args = parser.parse_args()

    out = Path(args.out).resolve() if args.out else common.default_out("zve10-runtime-")
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    print("OUTPUT: " + str(out), flush=True)
    result = None

    def callback(camera):
        nonlocal result
        camera.readHasp()
        common.check_version(camera)
        enabled = False
        try:
            enabled = True
            camera.setTerminalEnable(True)
            common.drain(camera.dev, 1.0)
            result = capture(camera.dev)
        finally:
            if enabled:
                camera.setTerminalEnable(False)
            if result is not None:
                result["terminal_closed"] = enabled

    try:
        common.connect(callback, args.driver)
    finally:
        if result is None:
            result = {
                "tool": "zve10_runtime_snapshot.py",
                "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "camera_side_writes": "none by this tool",
                "commands": [],
                "completed": False,
                "terminal_closed": False,
                "error": "snapshot did not return a result",
            }
        write_outputs(out, result)
        common.restore_tree_owner(out)
        print("SNAPSHOT_OUT:", out, flush=True)
        print("SNAPSHOT_REPORT:", out / "REPORT.md", flush=True)


if __name__ == "__main__":
    main()
