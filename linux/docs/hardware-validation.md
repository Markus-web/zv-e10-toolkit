# Linux host validation: firmware 30110_05

This record summarizes a read-only Linux-host session on an owned Sony ZV-E10 running `30110_05.2025031501`. Raw evidence and camera data remain outside the repository.

## Connection and boundary

- Host: Linux x86_64.
- Physical connection: one direct USB-C data cable.
- Initial USB state: Sony mass storage (`054c:0d95`).
- Access route: camera Linux service interface launched by the repository's privilege-aware scripts.
- Persistent camera writes by the capture commands: none. Service
  authentication may refresh `/setting/.etools` and `/setting/.hasp`.
- Fastboot: not attempted on the camera. Direct USB cannot replace the RP2040, CC breakout, and UART injection required by the fastboot route.

## Results

| Check | Result |
|---|---|
| Service root terminal | Opened and closed cleanly; camera returned to mass storage |
| File inventory | 1,139 paths; BusyBox-without-`find` fallback validated |
| Critical-file phase | 79 candidates inventoried; 78 copied and independently rehashed |
| Large skipped file | `/setting/psd.bin` exceeded the 4 MiB per-file cap; its bytes remain covered by the raw eMMC backup |
| Raw Linux-visible eMMC | Completed with receive-time and host-disk verification; digest retained with private evidence |
| BootROM range | Two identical reads of `0xffff0000–0xffff5fff` (24 KiB) |
| BootROM SHA-256 | `c068b4e9222970263b376c1298fa5714670b205d183dd8fa77413a2b43d17939` |
| Runtime snapshot | Completed 16 fixed read-only captures; terminal closed and mass storage returned |
| Deep hardware snapshot | Completed 111 default read-only captures; terminal closed and mass storage returned |
| CPU topology | Four ARMv7 Cortex-A5 cores active on the physical camera |
| GPE interrupt | IRQ 76 (`dmpgles2`) active; useful as a QEMU hardware-model reference |
| Runtime UARTs | `ttyAM0` at `uart0` and `ttyAM1` at `uart3` use AMBA PL011-compatible ID `00241011` |
| Linux input class | Only the virtual `mice` node was present; no physical touchscreen input node was exposed |
| Camera input path | `im.elf` owns `I-TpMain`, `I-TpRecv`, `I-InputMain`, `I-InputRecv`, and many `I-InputEvent` threads |
| USB device controller | DWC3 gadget configured at high speed; controller reports SuperSpeed maximum and no OTG |
| Standard Linux classes | No video4linux, sound, power-supply, thermal, GPIO, I2C-adapter, or MMC-host class was exposed |
| Camera application | `im.elf` had 188 threads and directly held GPE, stream, USB gadget, USB service, storage, and `/dev/mem` nodes |
| Proprietary hardware map | UDM exposed MMIO/IRQ topology for timers, 18 GPIO banks, XDMAC, MMC/eMMC, I2C, SPI, HDMI/CEC, USB, and DMA330 |
| Input scheduling | Touch/input workers used proprietary OSAL, futex, and `utimer_res_sleep` wait paths rather than Linux input events |
| USB scheduling | USB workers used `usb_event_read`, poll, OSAL, and futex wait paths |
| Boot state | UPM reported `NORM`; snapshot boot was in optimize/normal state with no swap file |
| eMMC health | Alfred reported normal pre-EOL/lifetime values and no read/write retry counts |
| Temporary helper | Executed from `/tmp_network`, removed after use |
| Offline Linux tests | 20 passed |
| Fastboot offline tests | 18 passed; ABI and release-pair checks passed |

The BootROM helper first tried a tmpfs path absent on this firmware and stopped without changing the camera. The maintained launcher now selects from an explicit tmpfs allow-list (`/tmp_bt`, `/tmp_network`, `/tmp_ipsec`) and rejects other locations.

## What this proves

The Linux route supports direct-USB inventory, selected file backup, Linux-visible raw eMMC backup, offline verification, and the documented 24 KiB BootROM read on this firmware and host. It does not prove fastboot entry, partition restore, hidden storage access, RPMB access, or recovery from a camera that cannot boot Linux.

The runtime and deep-hardware snapshots establish useful emulator baselines
without issuing persistent write commands. All four CPU cores are online, GPE
completion uses IRQ 76, and the two SoC UARTs identify as PL011-compatible AMBA
devices. DWC3 is the only active platform peripheral exposed through normal
sysfs and is configured as a high-speed gadget despite reporting a SuperSpeed
maximum. PCI and the standard Linux media, input, sound, sensor, and power
classes do not expose the camera hardware.

The proprietary UDM inventory supplies the missing emulator map: four hardware
timers, 18 GPIO banks, XDMAC, three MMC controllers, eMMC, two I2C and two SPI
controllers, HDMI/CEC, USB and DMA330, with their physical ranges and IRQs.
The active USB controller reports native-speed capability, while the configured
gadget and host descriptor remain USB 2 high-speed. UPM reports normal boot;
the firmware strings and init parser identify `usbj` as USB charge mode, not a
software route to BootROM USB or fastboot.

The camera application instead owns the hardware through proprietary device
nodes and direct physical-memory mappings. Its live thread names place touch at
`I-TpMain`/`I-TpRecv`, feed input through `I-InputMain`/`I-InputRecv`, and fan
events into many `I-InputEvent` workers. Their wait channels use Sony OSAL,
futex and microtimer paths; USB workers similarly wait through Sony's USB event
driver. This corroborates the emulator finding
that touch does not arrive through a conventional Linux input device. The
maintained deep tool completed all 111 default captures, closed its terminal, and
returned the camera to mass storage. Its private manifest is identified by
SHA-256 `15705a4ee9cea760b7e065b856678cb66c2d6b5d3ea54c656b899fbcebc1e3e8`.

The remaining 34 vendor diagnostic files are maintained as isolated `--only`
targets. All were exercised in small groups. They produced register snapshots,
driver help, boot state, input tables and storage health, but no additional USB
boot transition. One broad exploratory session was interrupted after a vendor
procfs read delayed the shell; this is why these reads are not part of the
default pass.

Repeat hardware validation after changing transport, privilege launch, temporary-helper placement, device paths, backup semantics, or the tested firmware.
