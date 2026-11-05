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


def optional_ls_recursive(path: str) -> str:
    return (
        "if [ -d " + path + " ]; then busybox ls -laR " + path
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
    ("proc_root", optional_ls("/proc")),
    ("proc_driver", optional_ls("/proc/driver")),
    ("proc_fs", optional_ls("/proc/fs")),
    ("proc_scsi", optional_ls("/proc/scsi")),
    ("proc_diskstats", optional_cat("/proc/diskstats")),
    ("proc_locks", optional_cat("/proc/locks")),
    ("proc_timer_list", optional_cat("/proc/timer_list")),
    ("proc_sched_debug", optional_cat("/proc/sched_debug")),
    ("proc_consoles", optional_cat("/proc/consoles")),
    ("proc_softirqs", optional_cat("/proc/softirqs")),
    ("proc_bam", optional_cat("/proc/bam")),
    ("proc_klog", optional_cat("/proc/klog")),
    ("proc_nodeorder", optional_cat("/proc/nodeorder")),
    ("proc_nlver", optional_cat("/proc/nlver")),
    ("proc_pgscan", optional_cat("/proc/pgscan")),
    ("proc_pmon", optional_cat("/proc/pmon")),
    ("proc_rmon", optional_cat("/proc/rmon")),
    ("proc_usb_event", optional_cat("/proc/usb_event")),
    ("proc_usb_otg", optional_cat("/proc/usb_otg")),
    ("proc_vtp", optional_cat("/proc/vtp")),
    ("proc_driver_alfred", optional_ls_recursive("/proc/driver/alfred")),
    ("proc_driver_pcie", optional_ls_recursive("/proc/driver/pcie")),
    ("proc_hwtimer", optional_ls_recursive("/proc/hwtimer")),
    ("proc_liro", optional_ls_recursive("/proc/liro")),
    ("proc_osal", optional_ls_recursive("/proc/osal")),
    ("proc_ssboot", optional_ls_recursive("/proc/ssboot")),
    ("proc_udm", optional_ls_recursive("/proc/udm")),
    ("proc_alfred_dev_type", optional_cat("/proc/driver/alfred/dev_type")),
    ("proc_alfred_drv_ver", optional_cat("/proc/driver/alfred/drv_ver")),
    ("proc_alfred_ext_modules", optional_cat("/proc/driver/alfred/ext_mod/list")),
    ("proc_alfred_emmc_cmd_count", optional_cat("/proc/driver/alfred/nflasha/emmc_cmd_count")),
    ("proc_alfred_emmc_smart", optional_cat("/proc/driver/alfred/nflasha/emmc_smart")),
    ("proc_pcie0_root", optional_cat("/proc/driver/pcie/0/root_ctrl")),
    ("proc_pcie1_root", optional_cat("/proc/driver/pcie/1/root_ctrl")),
    ("proc_hwtimer_cpu0", optional_cat("/proc/hwtimer/cpu0")),
    ("proc_hwtimer_cpu1", optional_cat("/proc/hwtimer/cpu1")),
    ("proc_hwtimer_cpu2", optional_cat("/proc/hwtimer/cpu2")),
    ("proc_hwtimer_cpu3", optional_cat("/proc/hwtimer/cpu3")),
    ("proc_liro_suspend_resume", optional_cat("/proc/liro/susres")),
    ("proc_osal_memory", optional_cat("/proc/osal/minfo")),
    ("proc_ssboot_mode", optional_cat("/proc/ssboot/mode")),
    ("proc_ssboot_operation", optional_cat("/proc/ssboot/operation")),
    ("proc_ssboot_resmode", optional_cat("/proc/ssboot/resmode")),
    ("proc_ssboot_section", optional_cat("/proc/ssboot/section")),
    ("proc_ssboot_state", optional_cat("/proc/ssboot/state")),
    ("proc_ssboot_swapfile", optional_cat("/proc/ssboot/swapfile")),
    ("proc_ssboot_optimizer_operation", optional_cat("/proc/ssboot/optimizer/operation")),
    ("proc_ssboot_optimizer_estimation", optional_cat("/proc/ssboot/optimizer/basic/estimation")),
    ("proc_ssboot_optimizer_profile", optional_cat("/proc/ssboot/optimizer/basic/profname")),
    ("proc_udm_devices", optional_cat("/proc/udm/devices")),
    ("proc_udm_drivers", optional_cat("/proc/udm/drivers")),
    ("proc_udm_dma330", optional_cat("/proc/udm/dma330")),
    ("proc_udm_dmac", optional_cat("/proc/udm/dmac")),
    ("proc_udm_fusb", optional_cat("/proc/udm/fusb")),
    ("proc_udm_gpio", optional_cat("/proc/udm/gpio")),
    ("proc_udm_input", optional_cat("/proc/udm/input")),
    ("proc_udm_upm_bootmode", optional_cat("/proc/udm/upm_bootmode")),
    ("proc_udm_usb_buspwr", optional_cat("/proc/udm/usb_buspwr")),
    ("proc_udm_usb_darwin", optional_cat("/proc/udm/usb_darwin")),
    ("proc_udm_usb_port_monitor", optional_cat("/proc/udm/usb_portMonitor")),
    ("proc_udm_utimer", optional_cat("/proc/udm/utimer")),
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
    ("camera_process_wait_channels", (
        "for f in /proc/[0-9]*/comm; do [ -r \"$f\" ] || continue; "
        "n=$(busybox cat \"$f\"); case \"$n\" in bootin.elf|im.elf) "
        "p=${f%/comm}; printf '\\n[%s %s wait channels]\\n' \"$p\" \"$n\"; "
        "for t in \"$p\"/task/*; do [ -r \"$t/comm\" ] || continue; "
        "printf '%s ' \"$t\"; busybox cat \"$t/comm\"; "
        "printf '  '; busybox cat \"$t/wchan\" 2>/dev/null || echo UNREADABLE; "
        "done; esac; done"
    )),
    ("dev_nodes", optional_ls("/dev")),
    ("dev_usb_nodes", optional_ls("/dev/usb")),
    ("dev_sound_nodes", optional_ls("/dev/snd")),
    ("dev_net_nodes", optional_ls("/dev/net")),
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
    ("sys_devices", optional_ls("/sys/devices")),
    ("sys_devices_system", optional_ls("/sys/devices/system")),
    ("sys_devices_virtual", optional_ls("/sys/devices/virtual")),
    ("sys_pcie0", optional_ls_recursive("/sys/devices/pci0000:00")),
    ("sys_pcie1", optional_ls_recursive("/sys/devices/pci0000:80")),
    ("sys_pcie_affinity", (
        "for f in /sys/devices/pci0000:*/pci_bus/*/cpuaffinity "
        "/sys/devices/pci0000:*/pci_bus/*/cpulistaffinity; do "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("sys_system_klog", optional_ls_recursive("/sys/devices/system/klog")),
    ("sys_system_memory", optional_ls_recursive("/sys/devices/system/memory")),
    ("sys_system_memory_values", (
        "for f in /sys/devices/system/memory/*; do [ -f \"$f\" ] || continue; "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("sys_system_node", optional_ls_recursive("/sys/devices/system/node")),
    ("sys_system_node_values", (
        "for f in /sys/devices/system/node/has_cpu "
        "/sys/devices/system/node/has_normal_memory /sys/devices/system/node/online "
        "/sys/devices/system/node/possible /sys/devices/system/node/node*/cpulist "
        "/sys/devices/system/node/node*/cpumap /sys/devices/system/node/node*/distance; do "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("sys_section_group", optional_ls_recursive("/sys/devices/system/section_group")),
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
    ("sys_clocksource", optional_ls("/sys/devices/system/clocksource")),
    ("sys_clocksource_values", (
        "for f in /sys/devices/system/clocksource/clocksource0/*; do "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_dwc3", optional_ls("/sys/devices/platform/dwc3.0")),
    ("sys_dwc3_gadget", optional_ls("/sys/devices/platform/dwc3.0/gadget")),
    ("sys_dwc3_udc", optional_ls("/sys/class/udc/dwc3.0")),
    ("sys_dwc3_udc_values", (
        "for f in /sys/class/udc/dwc3.0/*; do [ -f \"$f\" ] || continue; "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_firmware", optional_ls("/sys/firmware")),
    ("sys_power", optional_ls("/sys/power")),
    ("sys_power_values", (
        "for f in /sys/power/*; do [ -r \"$f\" ] || continue; "
        "printf '[%s] ' \"$f\"; busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_kernel", optional_ls("/sys/kernel")),
    ("sys_l2x0", optional_ls("/sys/kernel/l2x0")),
    ("sys_l2x0_values", (
        "for f in /sys/kernel/l2x0/*; do [ -f \"$f\" ] || continue; "
        "[ -r \"$f\" ] || continue; printf '[%s] ' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done"
    )),
    ("sys_modules", optional_ls("/sys/module")),
    ("sys_module_metadata", (
        "for d in /sys/module/*; do [ -d \"$d\" ] || continue; "
        "printf '\\n[%s]\\n' \"$d\"; for n in coresize initstate refcnt taint version; "
        "do f=\"$d/$n\"; [ -r \"$f\" ] || continue; printf '%s=' \"$n\"; "
        "busybox cat \"$f\"; done; done"
    )),
    ("sys_module_parameters", (
        "for d in /sys/module/*/parameters; do [ -d \"$d\" ] || continue; "
        "printf '\\n[%s]\\n' \"$d\"; for f in \"$d\"/*; do "
        "[ -r \"$f\" ] || continue; printf '%s=' \"$f\"; "
        "busybox cat \"$f\" 2>/dev/null || echo UNREADABLE; done; done"
    )),
    ("irq_affinity", (
        "for f in /proc/irq/*/smp_affinity; do [ -r \"$f\" ] || continue; "
        "printf '[%s] ' \"$f\"; busybox cat \"$f\"; done"
    )),
    ("selected_kernel_symbols", (
        "if [ -r /proc/kallsyms ]; then busybox grep -Ei "
        "'dmpgles|dwc3|cxd900x0|usb_extcmd|usb_portmonitor|ud_get_boot|boot_device|gadgetcore|usbg_' "
        "/proc/kallsyms; else echo MISSING: /proc/kallsyms; fi"
    )),
    ("kernel_config", (
        "if [ -r /proc/config.gz ]; then busybox ls -l /proc/config.gz; "
        "else echo MISSING: /proc/config.gz; fi"
    )),
)

# Vendor diagnostic procfs files can block independently of the shell command
# timeout when the camera firmware is busy. Keep them available for isolated,
# explicitly named captures without including them in the broad default pass.
TARGET_ONLY_NAMES = frozenset({
    "proc_alfred_dev_type",
    "proc_alfred_drv_ver",
    "proc_alfred_ext_modules",
    "proc_alfred_emmc_cmd_count",
    "proc_alfred_emmc_smart",
    "proc_pcie0_root",
    "proc_pcie1_root",
    "proc_hwtimer_cpu0",
    "proc_hwtimer_cpu1",
    "proc_hwtimer_cpu2",
    "proc_hwtimer_cpu3",
    "proc_liro_suspend_resume",
    "proc_osal_memory",
    "proc_ssboot_mode",
    "proc_ssboot_operation",
    "proc_ssboot_resmode",
    "proc_ssboot_section",
    "proc_ssboot_state",
    "proc_ssboot_swapfile",
    "proc_ssboot_optimizer_operation",
    "proc_ssboot_optimizer_estimation",
    "proc_ssboot_optimizer_profile",
    "proc_udm_devices",
    "proc_udm_drivers",
    "proc_udm_dma330",
    "proc_udm_dmac",
    "proc_udm_fusb",
    "proc_udm_gpio",
    "proc_udm_input",
    "proc_udm_upm_bootmode",
    "proc_udm_usb_buspwr",
    "proc_udm_usb_darwin",
    "proc_udm_usb_port_monitor",
    "proc_udm_utimer",
})
DEFAULT_COMMANDS = tuple(
    item for item in COMMANDS if item[0] not in TARGET_ONLY_NAMES
)


def capture(dev, commands=COMMANDS) -> dict:
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
    for name, command in commands:
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
    parser.add_argument(
        "--only",
        action="append",
        choices=[name for name, _command in COMMANDS],
        help="capture only this fixed surface; repeat for more than one",
    )
    args = parser.parse_args()
    selected = (
        tuple(item for item in COMMANDS if item[0] in args.only)
        if args.only else DEFAULT_COMMANDS
    )

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
            result = capture(camera.dev, selected)
        finally:
            if enabled:
                try:
                    camera.setTerminalEnable(False)
                    if result is not None:
                        result["terminal_closed"] = True
                except Exception as exc:  # noqa: BLE001
                    if result is not None:
                        result["terminal_closed"] = False
                        result["terminal_close_error"] = repr(exc)
            if result is not None:
                result.setdefault("terminal_closed", False)

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
