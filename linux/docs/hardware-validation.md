# Linux host validation: firmware 30110_05

This record summarizes a read-only Linux-host session on an owned Sony ZV-E10 running `30110_05.2025031501`. Raw evidence and camera data remain outside the repository.

## Connection and boundary

- Host: Linux x86_64.
- Physical connection: one direct USB-C data cable.
- Initial USB state: Sony mass storage (`054c:0d95`).
- Access route: camera Linux service interface launched by the repository's privilege-aware scripts.
- Persistent camera writes: none.
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
| CPU topology | Four ARMv7 Cortex-A5 cores active on the physical camera |
| GPE interrupt | IRQ 76 (`dmpgles2`) active; useful as a QEMU hardware-model reference |
| Runtime UARTs | `ttyAM0` at `uart0` and `ttyAM1` at `uart3` are registered |
| Linux input class | Only the virtual `mice` node was present; no physical touchscreen input node was exposed |
| Temporary helper | Executed from `/tmp_network`, removed after use |
| Offline Linux tests | 12 passed |
| Fastboot offline tests | 18 passed; ABI and release-pair checks passed |

The BootROM helper first tried a tmpfs path absent on this firmware and stopped without changing the camera. The maintained launcher now selects from an explicit tmpfs allow-list (`/tmp_bt`, `/tmp_network`, `/tmp_ipsec`) and rejects other locations.

## What this proves

The Linux route supports direct-USB inventory, selected file backup, Linux-visible raw eMMC backup, offline verification, and the documented 24 KiB BootROM read on this firmware and host. It does not prove fastboot entry, partition restore, hidden storage access, RPMB access, or recovery from a camera that cannot boot Linux.

The runtime snapshot also establishes useful emulator baselines without changing the camera: all four CPU cores are online, GPE completion uses IRQ 76, two SoC UARTs are registered, and the touchscreen path is not exposed as a conventional Linux input-class device. The maintained tool completed all 16 captures, closed its terminal, and returned the camera to mass storage. Its private manifest is identified by SHA-256 `0ecf36d61dc9206ac7fdb61ed8056c71310eee694e50ab6eb0e2f37f383bf35f`.

Repeat hardware validation after changing transport, privilege launch, temporary-helper placement, device paths, backup semantics, or the tested firmware.
