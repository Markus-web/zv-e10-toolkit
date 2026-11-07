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

## Switching the cable to the PC

- The payload detects VBUS low → high. After the long flash, unplug the 24-pin
  breakout from the camera and connect a normal USB-C cable to the PC.
- Pico 5V and Mac 5V can back-feed through the camera VBUS; the Pico may drop
  off the Mac. This does not affect the already running payload.

## LED

- One long flash (0.4 s): payload is alive.
- Short pulse count: USB clock/PHY → DWC3 → EP0 configuration → waiting for host.
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
