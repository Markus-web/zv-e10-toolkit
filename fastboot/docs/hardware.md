# Hardware and wiring

[**English**](hardware.md) | [简体中文](hardware.zh-CN.md)

## Bill of materials

The validated design uses these parts. Manufacturer part numbers matter more
than reseller stock numbers.

| Qty | Purpose | Selected part |
|---:|---|---|
| 1 | RP2040 sender | Raspberry Pi Pico H `SC0917` (headers installed) |
| 1 | Camera plug breakout | Saiko `BRK-USB-CPV3.0`, full USB-C male breakout |
| 1 | Required reset protection | Yageo `CFR-25JB-52-470R`, 470 ohm, 1/4 W |
| 1 | Optional serial protection | Same 470 ohm resistor; see wiring below |
| 1 | Shared CC pull-down | Yageo `CFR-25JB-52-5K1`, 5.1 kohm, 1/4 W |
| 1 | Pico programming cable | USB-A to Micro-B **data** cable |
| as needed | Interconnects | Short insulated 22-28 AWG wire and heat-shrink |

Current DigiKey Finland product pages: [Pico H](https://www.digikey.fi/en/products/detail/raspberry-pi/SC0917/16608257),
[Saiko breakout](https://www.digikey.fi/en/products/detail/saiko-systems-ltd/BRK-USB-CPV3-0/15283090),
[470 ohm resistor](https://www.digikey.fi/en/products/detail/yageo/CFR-25JB-52-470R/2211),
[5.1 kohm resistor](https://www.digikey.fi/en/products/detail/yageo/CFR-25JB-52-5K1/2236),
and [short Micro-B data cable](https://www.digikey.fi/en/products/detail/cvilux-usa/DH-20M50057/13177527).
Buying resistor multiples is sensible for spares. A second breakout is useful
if the first is damaged during hand assembly, but it is not electrically
required.

Fine straight ESD-safe tweezers help place wire and resistor leads. The
[Seeed/Vetus pattern 12 tweezers, `404070001`](https://www.digikey.fi/en/products/detail/seeed-technology-co-ltd/404070001/5488233)
are a suitable low-cost option. Tweezers do not replace a fine soldering iron,
flux, insulation, strain relief, or continuity testing.

## Wiring diagram

```
Camera USB-C receptacle
      ↑ plugged in
USB-C male plug (24-pin breakout, both A and B sides exposed)
      │
      ├─ A7  D− ──[optional 470Ω]── GP28   Pico serial TX (open-drain)
      ├─ A6  D+ ── 470Ω ────────── GP27   reset
      ├─ A5  CC1 ─┐
      ├─ B5  CC2 ─┴─ 5.1kΩ ── GND
      ├─ VBUS (any one of A4/A9/B4/B9) ── Pico 5V
      └─ GND  (any one of A1/A12/B1/B12) ── Pico GND
```

Note: **if A6/A7 do not work, try B6/B7.**

## Exact physical connections

With the Pico component side facing up and Micro-USB at the top, use the right
header edge:

| Pico physical pin | Board label | Breakout connection |
|---:|---|---|
| 40, first from top | `VBUS` | A4 `VBUS` |
| 38, third from top | `GND` | A1 `GND` |
| 34, seventh from top | `GP28` | A7 `D−` |
| 32, ninth from top | `GP27` | 470Ω, then A6 `D+` |

With the breakout labels facing up and its USB-C plug at the top, the right
column runs A12 at the top to A1 at the bottom. Therefore A7, A6, A5, A4 and A1
are respectively the seventh, sixth, fifth, fourth and first round pads counted
upward from the bottom. The left column runs B1 at the top to B12 at the bottom;
B5 is the fifth round pad from the top. Bridge A5 to B5, then use one 5.1kΩ
resistor from that shared node to A1 ground. Leave every other pad disconnected.

Do not mix sides. The fallback replaces the complete A6/A7 pair with B6/B7:
GP27 goes through 470Ω to B6 D+, and GP28 goes directly to B7 D−. It does not
connect both pairs or combine A6 with B7.

### Optional passive Pico 2 monitor

The second Pico is not part of the injection circuit. For diagnostics only,
connect its physical pin 34 (`GP28`) to one camera-side signal under test and
physical pin 38 (`GND`) to common ground. Leave its physical pin 40 (`VBUS`),
physical pin 32 (`GP27`) and every other pin disconnected. Monitor A6 or A7,
never both at once. The first Pico remains the only VBUS source and sender.

## Notes

- The camera side is a USB-C receptacle; a male 24-pin breakout is required
  to reach the pins.
- During injection the camera USB-C goes to the breakout, not to the PC.
- D− is open-drain; do not use a 3.3V push-pull driver.
- GP28 and GP27 are not interchangeable.
- GP29 (MULTI_RX) is not connected.
- 470Ω: required on GP27 → D+; optional on GP28 → D−.
- CC1 and CC2 are tied together first, then that shared node uses **one** 5.1
  kΩ pull-down to GND. Do not interpret the diagram as one resistor per CC pin.
- VBUS and GND: one wire each is enough; the camera ties the pins internally.

## Assembly acceptance

The Saiko board is a bare breakout, not a finished recovery cable. If an
electronics repair shop or maker assembles it, give them this page and require:

1. Short insulated wires, insulated joints, and mechanical strain relief so
   the exposed board cannot lever against the camera socket.
2. Visual inspection under magnification.
3. Point-to-point continuity against the diagram, including the shared CC
   node and the two distinct GP27/GP28 paths.
4. A short-circuit check between VBUS, GND, D+, D−, CC, and adjacent breakout
   pads before the camera is connected.
5. No connection from Pico 3.3 V to a camera signal pin and no substitution of
   a reduced 4-pin or 6-pin USB-C breakout.

Do not connect the camera merely to test unfinished wiring. Complete and record
the passive continuity checks first.

## Battery and reset

- Battery stays in; the camera boots normally.
- The script enables the carrier, sends a 10 µs low pulse on GP27 to reset the
  camera, then replays the record group.
- **No battery removal is needed with reset.** Removing the battery to cold-boot
  is the legacy v7 method and is not used now.

### Operator-visible reset test

The camera's normal unsupported-accessory sequence is `USB Mode`, followed a
few seconds later by `Check the connected device`. That transition happens
without a Pico command and is not evidence that reset worked.

For an unambiguous test, connect the camera to the breakout, not its normal PC
cable, and wait until `Check the connected device` is steady. Then run:

```sh
.venv/bin/python pico/reset_only.py \
  --port /dev/cu.usbmodemXXXX --countdown 5
```

A successful reset means the already-steady warning disappears and the screen
goes black exactly at `NOW: reset pulse`. If the warning stays visible, stop
repeating commands and recheck the complete GP27-to-D+ path with power removed.

## Linux breadboard bring-up, 2026-11-11

The purchased Pico H and passive parts passed these pre-camera checks:

- sender firmware `zve10_uart_od 15`, open-drain build and safe idle state;
- 466-468Ω measured for the reset resistor and 4.99kΩ for the CC resistor;
- 4.90 V measured from A4 VBUS to A1 ground with the camera disconnected;
- the 7,636-byte stage1 formed five records and repeated complete groups through
  the Pico transport, returning the Pico to safe idle;
- direct computer USB enumerated the camera normally in mass-storage mode.

The breadboard adapter did **not** produce the stage1 long flash or a fastboot
device during this session. Reset observations were confounded by the camera's
natural screen sequence and changing breadboard contacts. This is an incomplete
adapter bring-up, not new fastboot hardware validation. No eMMC, SD or OTP write
was attempted. Runtime logs and device identifiers remain private and ignored.

### Two-Pico passive diagnosis, 2026-11-12

An RP2350 Pico 2 running the same v15 firmware was used only as a passive GP28
input with no pulls. The reusable `pico/monitor_line.py` tool summarized edges
while the RP2040 sender operated. Both boards repeatedly passed firmware
identity and safe-idle checks.

- One A6 observation saw 1,457 ordinary USB transitions in 729 capture windows,
  proving that the passive monitor and camera-side A6 node could be observed.
- Later, after breadboard rewiring, a bounded 10 ms GP27 reset produced no A6
  transition. Sender pad readback was low before, during and after the pulse,
  with GPIO function 5 (SIO), while the monitor had previously read A6 high.
- During a 12-second published-stage1 injection, A7 stayed low and the passive
  monitor saw zero transitions in 1,213 windows. The camera did not flash its
  LED and no fastboot device appeared.
- A6 and the reported GP27 node each measured 2.20 V with a multimeter, but that
  time-averaged reading does not prove a continuous point-to-point path.

These observations conflict across changing breadboard states. They identify
the GP27 -> 470 ohm -> A6 assembly as unresolved; they do **not** establish a
camera, BootROM or payload defect. Before another injection, power off and
record all four continuity segments: GP27 to resistor input (about 0 ohm),
across the resistor (about 470 ohm), resistor output to A6 (about 0 ohm), and
GP27 to A6 end-to-end (about 470 ohm). Then require the passive monitor to see
the bounded 10 ms A6 pulse. No camera storage write was attempted.

When two Picos are connected, use stable `/dev/serial/by-id/` paths. Before a
UF2 deployment, unplug the other board and verify the target USB ID and volume
label as documented in [Pico sender setup](../pico/README.md).

## Switching the cable to the PC

- The payload detects VBUS low → high. After the long flash, unplug the 24-pin
  breakout from the camera and connect a normal USB-C cable to the PC.
- Pico 5V and Mac 5V can back-feed through the camera VBUS; the Pico may drop
  off the Mac. This does not affect the already running payload.

## LED

- Published prebuilt: one long flash (0.4 s) means the payload is alive; its
  validated handoff window remains 30 seconds.
- Locally rebuilt source candidate: after the initial alive and USB PHY
  patterns, solid means **disconnect the breakout and insert the normal USB-C
  cable now**. It stays solid until VBUS has gone low then high. If it never
  turns off, the handoff was not detected and DWC3 initialization does not run.
- After a successful handoff, short pulse count reports DWC3 and EP0 setup.
- One short pulse every 2 s afterwards: waiting for host enumeration.
- Stopping after the Nth short pulse: the corresponding step did not return.

## Stop / return to normal boot

From the repository root:

```sh
python3 fastboot/pico/reset_only.py --port /dev/cu.usbmodemXXXX
```

One GP27 reset, carrier off, and the camera returns to normal boot without
removing the battery. Power-off or battery removal also works: the payload
lives in SRAM and is volatile.

## Boundaries

- This is BootROM serial boot, not a runtime exploit; it needs dedicated wiring
  and reset timing.
- It writes SRAM only; no eMMC, SD, or OTP writes.
