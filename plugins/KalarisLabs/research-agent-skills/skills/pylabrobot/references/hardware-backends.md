# Hardware backends and supported robots

Verified against **PyLabRobot 0.2.1** on **2026-07-23**. Support labels below
come from the stable supported-machines page, not from marketing claims.

## Architecture

PyLabRobot separates:

- a frontend such as `LiquidHandler`, which validates and records standard
  operations;
- a backend, which translates those operations for one device family;
- a resource/deck tree, which supplies geometry and state.

A common frontend does not guarantee identical channels, tools, operations,
parameters, calibration, error semantics, timing, or firmware support.
Backend-specific kwargs must be reviewed against the exact stable model page.

## Verified stable liquid-handler names

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import (
    EVOBackend,
    LiquidHandlerChatterboxBackend,
    OpentronsOT2Backend,
    STARBackend,
    VantageBackend,
)
```

Do not use stale names from older skill text:

- `STAR` is not the stable high-level backend name; use `STARBackend`.
- `TecanBackend` is not the 0.2.1 EVO backend; use `EVOBackend`.
- `OpentronsBackend` is stale; use `OpentronsOT2Backend`.
- `ChatterboxBackend` has incorrect naming/capitalization for the recommended
  generic liquid-handler testing backend; use
  `LiquidHandlerChatterboxBackend`.
- `ChatterBoxBackend` (capital `B`) is a separate exported legacy-named class.
  Avoid it when the stable docs specifically call for
  `LiquidHandlerChatterboxBackend`.

## Stable liquid-handling support levels

- **Hamilton STAR(let): Full.** Stable class `STARBackend`; deck definitions
  include `STARDeck` and `STARLetDeck`.
- **Hamilton Vantage: Mostly.** Stable class `VantageBackend`; verify unsupported
  commands and installed options.
- **Hamilton Prep: WIP.**
- **Hamilton Nimbus: WIP.**
- **Tecan Freedom EVO: Basic.** Stable class `EVOBackend`; do not describe it as
  full or backend-equivalent to STAR.
- **Opentrons OT-2: Mostly.** Stable class `OpentronsOT2Backend(host, port=31950)`;
  network/API/firmware compatibility is model-specific.

Upstream defines:

- **WIP**: work in progress;
- **Basics/Basic**: core functionality is integrated and documented;
- **Mostly**: most capabilities are available but known commands are missing;
- **Full**: upstream considers at least 90% of hardware/firmware capabilities
  supported with extensive documentation.

These labels do not validate a particular firmware, attachment, computer,
transport, or protocol.

## Offline backend

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources.hamilton import STARLetDeck

lh = LiquidHandler(
    backend=LiquidHandlerChatterboxBackend(num_channels=8),
    deck=STARLetDeck(),
)
await lh.setup()
try:
    # Build resources and exercise planned operations only.
    ...
finally:
    await lh.stop()
```

This backend prints operations and updates software state. It does not connect
to a robot and does not model robot physics. Keep the backend construction
literal; never choose a live class from a string, plugin, environment variable,
or untrusted config.

## Capability/version inspection without connection

```bash
python3 skills/pylabrobot/scripts/inspect_backends.py \
  --expected-version 0.2.1 --strict
```

The inspector:

- imports a fixed allowlist of stable classes only after argument parsing;
- reads installed distribution metadata;
- inspects class signatures/method presence;
- creates zero backend instances;
- never calls `setup()`;
- performs no serial, USB, HID, FTDI, Modbus, or network operation.

Method presence is not proof that a model implements the operation; some
backends deliberately raise `NotImplementedError`.

## Extras and transports

Base `PyLabRobot==0.2.1` keeps hardware dependencies optional. Stable
installation documentation lists extras including:

- `serial`
- `usb`
- `ftdi`
- `hid`
- `modbus`
- `opentrons`
- `sila`
- `microscopy`
- `pico`
- `all`

Install only the exact reviewed extra for a named device and keep the top-level
pin:

```bash
# Example form only; do not run until the device and transport are approved.
uv pip install "PyLabRobot[serial]==0.2.1"
```

`all` intentionally does not include microscopy in stable 0.2.1 because of its
separate NumPy/SDK constraints. Optional transport packages can enumerate or
communicate with devices; installation does not authorize their use.

## Live-run gate

Do not instantiate a live backend or call `setup()` until a trained operator has
explicitly confirmed:

1. Backend class, exact robot model/serial number, firmware, options, and
   transport.
2. Vendor/organization permission, warranty implications, maintenance state,
   access controls, and exclusive control of the device.
3. Deck definition, carriers/adapters, resources, coordinates, orientation,
   clearances, and collision/motion review.
4. Calibration, teaching, tip/head compatibility, channel mapping, units,
   heights, rates, liquid classes, and all backend kwargs.
5. Source/dead/destination volumes, physical liquid identity, tip state,
   contamination policy, waste, lids/seals, tubing/cables, and operator steps.
6. Guards/doors, emergency stop readiness, PPE, containment, dry-run plan,
   abort path, and recovery/resume rules.

Never make a live run conditional only on `USE_HARDWARE=true`, a CLI flag, or an
IP/serial value. Confirmation must be tied to the reviewed protocol and current
physical setup.

## Backend-specific cautions

### Hamilton STAR/Vantage

These are direct firmware drivers. Upstream states that PyLabRobot is not
endorsed or supported by robot manufacturers and that firmware-driver use may
affect warranty. Review USB permissions, device selection, cover/arm/head
configuration, firmware ranges, liquid-level detection, channels, CO-RE tips,
and all device-specific errors.

### Tecan EVO

Stable status is **Basic**, not full. Use `EVOBackend`; verify which LiHa/RoMa
commands, arms, tips, carriers, and firmware paths are implemented. Never infer
Hamilton behavior or liquid classes.

### Opentrons OT-2

`OpentronsOT2Backend` communicates with an explicitly configured host over
HTTP. Do not scan a network or probe a robot. Confirm robot software/API
compatibility and unsupported operations; stable source explicitly rejects
some features such as a 96 head and robotic-arm methods.

## Stable versus development

The stable pin/tag is `v0.2.1`. Repository `main` continued changing through
2026-07-22 during this review. Development docs and `CHANGELOG.md`'s
`Unreleased` section may describe classes not in the wheel. For example,
HighRes MicroSpin support is unreleased and must not be presented as a stable
0.2.1 capability.

When considering a later release:

1. Confirm it exists on PyPI and is not a prerelease.
2. Compare `Requires-Python`, extras, tag, changelog, and source.
3. Run import/signature and software-only tests in an isolated environment.
4. Revalidate each target model/firmware and repeat commissioning.

## Sources

Checked **2026-07-23**:

- [Stable supported machines](https://docs.pylabrobot.org/stable/user_guide/machines.html)
  — model/status tables and status definitions (page metadata surfaced
  2025-01-01; docs version 0.2.1).
- [Stable liquid-handling API](https://docs.pylabrobot.org/stable/api/pylabrobot.liquid_handling.html)
  — abstract, hardware, serializing, and testing backends.
- [Stable installation](https://docs.pylabrobot.org/stable/user_guide/_getting-started/installation.html)
  — optional extras and stable/source distinction.
- [`v0.2.1` backend source](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/liquid_handling/backends)
  — exact classes and limitations; tag commit dated 2026-03-23.
- [Project README](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1#readme)
  — supported robot families and manufacturer/warranty disclaimer.
- [Changelog](https://github.com/PyLabRobot/pylabrobot/blob/main/CHANGELOG.md)
  — stable 0.2.1 versus development-only `Unreleased`.
