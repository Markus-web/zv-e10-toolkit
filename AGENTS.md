# Maintainer guide

This repository contains two separate ZV-E10 access routes. Preserve that boundary: `linux/` is the normal USB service-interface route after camera Linux boots; `fastboot/` is a recovery route that requires BootROM serial injection hardware before USB fastboot exists.

## Read order

1. `README.md` for route selection and scope.
2. `linux/README.md` or `fastboot/README.md` for the chosen route.
3. The linked operation guide under that route's `docs/` directory.
4. `CONTRIBUTING.md` before changing code or published payloads.

## Layout and ownership

- `linux/host/`: host-side service transport, backup, verification, and terminal tools.
- `linux/scripts/`: reusable setup and privilege-aware launchers.
- `linux/helpers/bootrom-reader/`: temporary camera-side read-only helper.
- `fastboot/stage1/` and `fastboot/stage2/`: paired bare-metal payload sources.
- `fastboot/host/` and `fastboot/pico/`: computer-side bootstrap and injection tools.
- `fastboot/prebuilt/`: hardware-validated paired payloads; never update hashes to hide an ABI change.
- Each route's `docs/`: safety boundaries, operation steps, and validation records.

## Safety boundary

- Default to read-only operations. Camera writes require an explicit recovery task, a verified backup, the exact target partition, and the recovery guide.
- A direct USB-C cable can reach mass storage and the Linux service interface. It cannot perform the UART/CC BootROM injection required to create the fastboot device.
- Never commit firmware, BootROM dumps, backups, service keys, serials, identifiers, or raw evidence.
- Keep private outputs in ignored `linux/backups/`, `linux/sessions/`, or an external directory with restrictive permissions.
- Do not publish a new payload pair without fresh hardware validation.

## Verification

```sh
cd linux
.venv/bin/python -m unittest discover -s tests -v
sh -n scripts/*.sh

cd ../fastboot
make test PYTHON=python3
make check PYTHON=python3
```

Tests are offline unless an operation guide explicitly labels a hardware step. Hardware checks must record the camera firmware, host OS, route, read/write boundary, and outcome without device-identifying data.

## Maintenance

- Put reusable host actions in the relevant `scripts/`, `host/`, or `tools/` directory and cover them under the route's existing test suite.
- Keep English and Chinese guides aligned when paths, supported firmware, payloads, or safety limits change.
- Update this file, the route README, and its operation guide in the same change.
- Upstream issues and pull requests are research inputs. Do not merge or publish them without local review and the applicable offline/hardware gates.
