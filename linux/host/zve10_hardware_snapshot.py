#!/usr/bin/env python3
"""Capture deep, read-only ZV-E10 hardware topology over the service terminal.

This complements ``zve10_runtime_snapshot.py`` with device-enumeration data
useful to emulator work. It reads procfs and sysfs text/listing surfaces plus
``/dev`` directory metadata; it never opens camera device nodes, changes sysfs
values, loads modules, or enables the terminal's write mode.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import zve10_common as common


def optional_cat(path: str) -> str:
    return (
        "if [ -r " + path + " ]; then busybox cat " + path
        + "; else echo MISSING: " + path + "; fi"
    )


def optional_ls(path: str) -> str:
    return (
        "if [ -d " + path + " ]; then busybox ls -la " + path
        + "; else echo MISSING: " + path + "; fi"
    )


COMMANDS = (
    ("proc_misc", optional_cat("/proc/misc")),
    ("proc_dma", optional_cat("/proc/dma")),
    ("proc_ioports", optional_cat("/proc/ioports")),
    ("proc_tty_drivers", optional_cat("/proc/tty/drivers")),
    ("proc_tty_serial", optional_cat("/proc/tty/driver/serial")),
    ("proc_input_devices", optional_cat("/proc/bus/input/devices")),
    ("proc_pci_devices", optional_cat("/proc/bus/pci/devices")),
    ("proc_usb_devices", optional_cat("/proc/bus/usb/devices")),
    ("proc_net_devices", optional_cat("/proc/net/dev")),
    ("proc_rtc", optional_cat("/proc/driver/rtc")),
    ("proc_cpu_alignment", optional_cat("/proc/cpu/alignment")),
    ("proc_swaps", optional_cat("/proc/swaps")),
    ("proc_version_signature", optional_cat("/proc/version_signature")),
    ("proc_cmd_names", (
        "for f in /proc/[0-9]*/comm; do [ -r \"$f\" ] || continue; "
        "printf '%s ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("camera_process_layout", (
        "for f in /proc/[0-9]*/comm; do [ -r \"$f\" ] || continue; "
        "n=$(busybox cat \"$f\"); case \"$n\" in bootin.elf|im.elf) "
        "p=${f%/comm}; printf '\\n[%s %s]\\n' \"$p\" \"$n\"; "
        "busybox cat \"$p/status\"; busybox cat \"$p/maps\"; "
        "busybox ls -l \"$p/exe\"; esac; done"
    )),
    ("camera_process_threads", (
        "for f in /proc/[0-9]*/comm; do [ -r \"$f\" ] || continue; "
        "n=$(busybox cat \"$f\"); case \"$n\" in bootin.elf|im.elf) "
        "p=${f%/comm}; printf '\\n[%s %s threads]\\n' \"$p\" \"$n\"; "
        "for t in \"$p\"/task/*/comm; do [ -r \"$t\" ] || continue; "
        "printf '%s ' \"$t\"; busybox cat \"$t\"; done; esac; done"
    )),
    ("camera_process_device_fds", (
        "for f in /proc/[0-9]*/comm; do [ -r \"$f\" ] || continue; "
        "n=$(busybox cat \"$f\"); case \"$n\" in bootin.elf|im.elf) "
        "p=${f%/comm}; printf '\\n[%s %s device fds]\\n' \"$p\" \"$n\"; "
        "for d in \"$p\"/fd/*; do t=$(busybox readlink \"$d\" 2>/dev/null || true); "
        "case \"$t\" in /dev/*) printf '%s -> %s\\n' \"$d\" \"$t\";; esac; "
        "done; esac; done"
    )),
    ("dev_nodes", optional_ls("/dev")),
    ("sys_classes", optional_ls("/sys/class")),
    ("sys_buses", optional_ls("/sys/bus")),
    ("sys_amba_devices", optional_ls("/sys/bus/amba/devices")),
    ("sys_amba_drivers", optional_ls("/sys/bus/amba/drivers")),
    ("sys_amba_uevents", (
        "for f in /sys/bus/amba/devices/*/uevent; do "
        "[ -r \"$f\" ] || continue; printf '\\n[%s]\\n' \"$f\"; "
        "busybox cat \"$f\"; done"
    )),
    ("sys_pci_devices", optional_ls("/sys/bus/pci/devices")),
    ("sys_serio_devices", optional_ls("/sys/bus/serio/devices")),
    ("sys_block", optional_ls("/sys/block")),
    ("sys_platform_devices", optional_ls("/sys/bus/platform/devices")),
    ("sys_platform_drivers", optional_ls("/sys/bus/platform/drivers")),
    ("sys_platform_uevents", (
        "for f in /sys/bus/platform/devices/*/uevent; do "
        "[ -r \"$f\" ] || continue; printf '\\n[%s]\\n' \"$f\"; "
        "busybox cat \"$f\"; done"
    )),
    ("sys_graphics", optional_ls("/sys/class/graphics")),
    ("sys_video4linux", optional_ls("/sys/class/video4linux")),
    ("sys_sound", optional_ls("/sys/class/sound")),
    ("sys_power_supply", optional_ls("/sys/class/power_supply")),
    ("sys_thermal", optional_ls("/sys/class/thermal")),
    ("sys_gpio", optional_ls("/sys/class/gpio")),
    ("sys_uio", optional_ls("/sys/class/uio")),
    ("sys_misc", optional_ls("/sys/class/misc")),
    ("sys_mem", optional_ls("/sys/class/mem")),
    ("sys_timed_output", optional_ls("/sys/class/timed_output")),
    ("sys_i2c", optional_ls("/sys/class/i2c-adapter")),
    ("sys_mmc", optional_ls("/sys/class/mmc_host")),
    ("sys_net", optional_ls("/sys/class/net")),
    ("sys_rtc", optional_ls("/sys/class/rtc")),
    ("sys_udc", optional_ls("/sys/class/udc")),
    ("sys_usb", optional_ls("/sys/bus/usb/devices")),
    ("sys_cpu", optional_ls("/sys/devices/system/cpu")),
    ("sys_cpu_values", (
        "for f in /sys/devices/system/cpu/kernel_max "
        "/sys/devices/system/cpu/offline /sys/devices/system/cpu/online "
        "/sys/devices/system/cpu/possible /sys/devices/system/cpu/present; do "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("sys_cpu0_topology", optional_ls("/sys/devices/system/cpu/cpu0/topology")),
    ("sys_cpu0_topology_values", (
        "for f in /sys/devices/system/cpu/cpu0/topology/*; do "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("sys_cpu0_cache", optional_ls("/sys/devices/system/cpu/cpu0/cache")),
    ("sys_dwc3", optional_ls("/sys/devices/platform/dwc3.0")),
    ("sys_dwc3_gadget", optional_ls("/sys/devices/platform/dwc3.0/gadget")),
    ("sys_dwc3_udc", optional_ls("/sys/class/udc/dwc3.0")),
    ("sys_dwc3_udc_values", (
        "for f in /sys/class/udc/dwc3.0/*; do [ -f \"$f\" ] || continue; "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_firmware", optional_ls("/sys/firmware")),
    ("sys_kernel", optional_ls("/sys/kernel")),
    ("sys_l2x0", optional_ls("/sys/kernel/l2x0")),
    ("sys_l2x0_values", (
        "for f in /sys/kernel/l2x0/*; do [ -f \"$f\" ] || continue; "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_modules", optional_ls("/sys/module")),
    ("kernel_config", (
        "if [ -r /proc/config.gz ]; then busybox ls -l /proc/config.gz; "
        "else echo MISSING: /proc/config.gz; fi"
    )),
)


def capture(dev) -> dict:
    result = {
        "tool": "zve10_hardware_snapshot.py",
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
        "# ZV-E10 hardware-topology snapshot",
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
        "The full command output is stored in `manifest.json`. `MISSING` means",
        "the running kernel does not expose that optional procfs/sysfs surface.",
        "This tool does not access block-device nodes or enable terminal write mode.",
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

    out = Path(args.out).resolve() if args.out else common.default_out("zve10-hardware-")
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
                "tool": "zve10_hardware_snapshot.py",
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
