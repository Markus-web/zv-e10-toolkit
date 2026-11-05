# Cross-camera research applied to the ZV-E10

[简体中文](cross-camera-research.zh-CN.md)

Sony camera research is useful when it is treated as a source of hypotheses and
formats, not as a source of addresses. This comparison used
[`RafalB82/sony-a6000-re`](https://github.com/RafalB82/sony-a6000-re) at
`e73517998e92a186e247da32cf84ea305fd206a1` and
[`nicolvus/a6000-fw-decomp`](https://github.com/nicolvus/a6000-fw-decomp) at
`d07ae93f15b790ff17746d79537ac1a886c2796e`.

## Confirmed reusable findings

| A6000 finding | ZV-E10 result | Use |
|---|---|---|
| Sony `Backup.bin` BK format and Sony-PMCA-RE parser | The private ZV-E10 file parses as checksum-valid BK4 with 819 subsystems and 33,178 properties | Offline structure and future differential analysis |
| Musashi, SABIN and scenario layers | ZV-E10 ships Musashi-named SABIN programs, `scenario.elf`, and matching scenario plug-in families | Naming and subsystem map |
| DFE/Regulus/ZPD split | ZV-E10 `av-cam.bin` contains Regulus, ZPD, DFE camera and SSG paths; separate `dfe_app.bin` and `dfe_dat.bin` are present | Sensor-front-end analysis target |
| TPZL/LDEC compressed images | TPZL markers occur in the ZV-E10 boot image, kernel modules and snapshot-boot programs | Add hardware-geometry checks before any future image rebuild |
| Updater flag files | ZV-E10 libraries and scripts reference `updater/mode`, `mode1`, `mode2`, `mode3`, `mode5`, and `mode6` below `/setting` | Static boot-path lead; do not create these files on hardware without a recovery plan |
| USB charge mode is not recovery USB | ZV-E10 `usbj` is explicitly USB charge mode; no BootROM or fastboot transition was found | Closes the regular-cable charge-mode hypothesis |

The sanitized offline inspector is:

```sh
./scripts/inspect_backup.sh /private/path/Backup.bin
./scripts/inspect_backup.sh --json /private/path/Backup.bin
```

It intentionally omits region, model, serial, property IDs and property values.
The A6000 research tool prints some of those fields by default and must not be
used for public logs without filtering.

## Findings that do not transfer directly

- A6000 Loader3 addresses, SWD pads, bootloader checks and memory maps are tied
  to CXD90014 firmware and the A6000 board. They are not ZV-E10 addresses.
- The A6000 DFE naming script targets one 64 KiB raw image loaded at
  `0x01000000`. The ZV-E10 splits DFE material differently, so names and offsets
  require fresh analysis.
- A6000 TPZL limits are a strong validation checklist, not proof that every
  later loader uses identical limits.
- The ZV-E10 `MPR_SCN_GET_TOTAL_LOG.so` plug-in opens `/log/mprlog.bin` and
  `/dev/mem`; it was not run during the read-only camera session.
- Creating an updater mode file is a persistent camera write and may change the
  next boot. Static evidence alone does not make that a safe fastboot route.

## Next evidence needed

1. Identify the ZV-E10 board's SoC and debug pads from its own service manual or
   continuity measurements before considering SWD.
2. Map the ZV-E10 loader's reads of `/setting/updater/mode*` and determine each
   mode's USB identity without creating a flag.
3. Validate ZV-E10 TPZL block geometry against unmodified Sony images before
   reusing any A6000 encoder or patch workflow.
4. Analyze `dfe_app.bin`, `dfe_dat.bin`, and their load path as ZV-E10-specific
   binaries; use A6000 Regulus names only where strings or control flow match.
