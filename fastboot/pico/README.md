# Pico sender setup

[简体中文](README.zh-CN.md) · [Bare-metal guide](../README.md) · [Wiring](../docs/hardware.md)

Use an RP2040 Raspberry Pi Pico. Sender firmware `zve10_uart_od 15` provides
PIO/DMA transmission, open-drain output and GP27 reset.

## Build and install

Install `arduino-cli` and the Arduino-Pico `rp2040:rp2040` core (build checked with core 6.3.0). From `fastboot/`:

```sh
arduino-cli compile --fqbn rp2040:rp2040:rpipico \
  --build-property build.extra_flags=-DOPEN_DRAIN \
  --output-dir pico/build-v15-rp2040 pico/firmware/zve10_pico_od_reset
arduino-cli compile --fqbn rp2040:rp2040:rpipico2 \
  --build-property build.extra_flags=-DOPEN_DRAIN \
  --output-dir pico/build-v15-rp2350 pico/firmware/zve10_pico_od_reset
```

Hold BOOTSEL while connecting Pico to USB, then copy the compiled UF2 to the
`RPI-RP2` volume. Keep `serialboot.pio.h` alongside `.pio`: it is a required
source header for the sketch.

The production default reset pulse is 10 us. Use `reset_only.py --pulse-us`
for bounded 10 us to 100 ms diagnostics; injection always retains the default.
Local UF2 files stay in ignored `pico/build-v*/` directories.

### Safe deployment with two Picos

Linux `/dev/ttyACM*` numbers can swap after reconnects. Use the stable
`/dev/serial/by-id/` link for commands. Before installing a UF2, unplug the
other Pico, enter BOOTSEL manually, and verify exactly one boot drive:

- RP2040 sender: USB ID `2e8a:0003`, volume label `RPI-RP2`, RP2040 UF2;
- RP2350 Pico 2: USB ID `2e8a:000f`, volume label `RP2350`, RP2350 UF2.

Never let an automatic uploader select a drive while both boot volumes are
present. Copy the matching UF2 only after checking the USB ID and volume label.

## Inspect and use

```sh
.venv/bin/python pico/inspect_pico.py --port /dev/cu.usbmodemXXXX
.venv/bin/python pico/inject_payload.py --port /dev/cu.usbmodemXXXX \
  --file prebuilt/stage1.bin --duration 15 --record-gap 0.002 --countdown 5
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5 --pulses 5 --interval 1
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5 --pulse-us 10000
.venv/bin/python pico/monitor_line.py --port /dev/cu.usbmodemMONITOR \
  --duration 20
```

Replace the serial port. Injection checks the firmware version, idle state and
open-drain configuration before the countdown starts. The reset-only command
provides the same visible action boundary for camera-screen observation. See
wiring for connections and handoff timing, and
[the protocol](PROTOCOL.md) for record encoding.
Use its bounded `--pulses` mode only for passive reset-line capture; normal
camera reset and recovery use the one-pulse default. Current firmware also
returns GP27 pad levels before, during and after the pulse plus its GPIO mux
function. Expected output is `before=1`, `during=0`, `after=1`,
`gpio_function=5` (SIO). The host remains compatible with older empty replies.
`--pulse-us` requests a diagnostic width from 10 us through 100 ms; omit it for
the normal 10 us reset used by injection.
Injection prints and records the same GP27 observation when current firmware
returns it.

`monitor_line.py` reuses an idle sender as a passive GP28 transition monitor.
Connect only monitor GP28 to the camera-side line under test and monitor GND to
the common ground; leave its 5V and GP27 disconnected. The tool refuses a Pico
that is not idle with no pulls and reports transition counts and edge timing.
It does not drive GP28, pulse reset or save raw captures. Run it on a second
Pico while the first Pico performs injection.
