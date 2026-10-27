# Material handling, pumps, and environmental devices

Verified against **PyLabRobot 0.2.1** on **2026-07-23**. Every operation in
this domain can create physical motion, pressure, heat, or stored energy. The
snippets below identify APIs only; they do not connect to devices.

## Pumps

Stable frontend and one stable backend export:

```python
from pylabrobot.pumps import MasterflexBackend, Pump
```

Verified `Pump` methods:

```text
run_revolutions(num_revolutions)
run_continuously(speed)
run_for_duration(speed, duration)
halt()
```

The stale methods `start`, `stop` as a pumping command, `pump_volume`, and
`calibrate(duration=..., speed=..., volume=...)` are not the verified universal
0.2.1 frontend shown above. `stop()` belongs to machine lifecycle; `halt()` is
the pump-motion command.

`MasterflexBackend(com_port)` is transport-specific. Do not instantiate it
during discovery. Stable supported machines labels Cole-Parmer Masterflex
L/S listed models and Agrowtek Pump Array as **Full**.

### Pump safety

Before a separately authorized run, verify:

- exact pump/head/tubing model, material, inner diameter, direction, occlusion,
  fittings, valves, clamps, and destination;
- calibrated relationship among command speed/revolutions/time and delivered
  volume for the current fluid, tubing age, backpressure, and temperature;
- prime/purge route, bubbles, siphoning, dead volume, residual volume, maximum
  pressure/flow, leak containment, and waste capacity;
- chemical/biological compatibility, cross-contamination controls, and tubing
  change policy;
- an accessible stop and safe behavior on disconnect, timeout, or partial
  delivery.

A time/speed command is not a measured volume. Record the calibration and
uncertainty; use a validated scale/flow sensor if closed-loop confirmation is
required.

## Heater shakers and shakers

Stable frontend imports:

```python
from pylabrobot.heating_shaking import (
    HamiltonHeaterShakerBackend,
    HeaterShaker,
    InhecoThermoshakeBackend,
)
from pylabrobot.shaking import Shaker
```

The stable class is `InhecoThermoshakeBackend` (lowercase `s` in
`Thermoshake`), not the stale `InhecoThermoShakeBackend`.

Verified `HeaterShaker` methods:

```text
set_temperature(temperature, passive=False)
get_temperature()
shake(speed, duration=None, **backend_kwargs)
stop_shaking(**backend_kwargs)
lock_plate(**backend_kwargs)
unlock_plate(**backend_kwargs)
```

The old names `set_shake_rate` and `set_temperature(None)` are not the verified
0.2.1 frontend signatures. Use the exact device page for deactivation/cooling
and do not substitute zero/`None` unless documented for that backend.

`HeaterShaker` construction requires `name`, dimensions, backend, and a
`child_location`. Backend construction is also device topology-specific:
`HamiltonHeaterShakerBackend(index, interface)` and
`InhecoThermoshakeBackend(index, control_box)` require approved shared
interfaces/controllers.

Stable supported machines lists:

- Inheco Thermoshake and Thermoshake AC: **Full**
- Opentrons Thermoshake: **Full**
- Hamilton Heater Shaker: **Full**
- QInstruments BioShake: **Full**

### Heater/shaker safety

Confirm plate compatibility, mass, balance, lid/seal, locking, condensation,
spillage containment, orbit/speed limits, thermal limits, ramp/equilibration,
sensor calibration, and safe unlock temperature. Never unlock or move a plate
while shaking. Treat a requested setpoint as a command, not proof that the
sample has reached that temperature.

## Temperature controllers

Stable frontend:

```python
from pylabrobot.temperature_controlling import TemperatureController
```

Verified methods:

```text
set_temperature(temperature, passive=False)
get_temperature()
deactivate()
```

Stable support includes Inheco CPAC (**Full**) and Opentrons Temperature Module
(**Mostly** in the complete stable table). Validate active cooling, condensation,
plate/adapter contact, setpoint range, ramp, sensor placement, overshoot, and
sample-versus-block temperature.

## Centrifuges

Stable imports:

```python
from pylabrobot.centrifuge import Access2Backend, Centrifuge, VSpinBackend
```

Verified frontend:

```text
open_door()
close_door()
lock_door()
unlock_door()
spin(g, duration, **backend_kwargs)
```

The stable method takes relative centrifugal force `g`, not the stale
`speed=...` RPM argument. Converting RPM to RCF requires the correct rotor
radius; never guess it.

Stable supported machines labels:

- Agilent VSpin: **Mostly**
- Agilent VSpin Access2 Loader: **Full**

`VSpinBackend(device_id=None)` and `Access2Backend(device_id, timeout=60)` are
device-specific. Do not use placeholder IDs in a live script.

The current changelog lists HighRes Biosolutions MicroSpin under
**Unreleased**. Although development `main` may expose `MicroSpin`, it is not a
stable 0.2.1 API and must not be imported in pinned examples.

### Centrifuge safety

Require human verification of rotor/bucket/adapter model, plate rating,
orientation, balance, maximum RCF, duration, acceleration/deceleration, lid/door
interlocks, loading position, clearance, maintenance, and emergency procedure.
Never open/unlock while rotating or issue movement merely to test a connection.
On timeout or disconnect, assume the rotor may still be moving until physically
verified safe.

## Storage/incubation

The stable machine inventory includes multiple Thermo Fisher/Heraeus Cytomat
models as **Full**, and Inheco Incubator Shaker/SCILA as **Mostly**. Their APIs
are model-specific; do not use stale generic examples such as
`from pylabrobot.incubation import Incubator` without verifying that exact
symbol in the pinned wheel.

Storage moves require explicit plate identity, slot mapping, occupancy state,
door/hatch/interlock state, orientation, environmental setpoints, and recovery
from an interrupted handoff. Software occupancy is not physical detection.

## Multi-device orchestration

Do not independently `gather()` hardware operations just because frontends are
async. Safe concurrency requires approved workcell interlocks and a scheduler
that owns:

- device and plate state;
- collision zones and transfer ownership;
- door/tray/bucket/lock preconditions;
- timeouts, retries, idempotency, and partial-completion handling;
- emergency stop and restart/reconciliation behavior.

Default sequence:

1. Validate manifests and transfers offline.
2. Generate a non-executable simulation plan.
3. Exercise software-only frontends where available.
4. Review every handoff with the operator.
5. Obtain explicit confirmation for the exact live protocol.
6. Commission one device/move at a time under site procedures.

## No-connection inspection

```bash
python3 skills/pylabrobot/scripts/inspect_backends.py \
  --expected-version 0.2.1 --strict
```

This checks a fixed set of frontend symbols and methods without constructing
devices or calling `setup()`.

## Sources

Checked **2026-07-23**:

- [Stable supported machines](https://docs.pylabrobot.org/stable/user_guide/machines.html)
  — pumps, centrifuges, heater shakers, storage, and temperature controllers
  with model-specific labels (page metadata surfaced 2025-01-01).
- [Stable pumps guide](https://docs.pylabrobot.org/stable/user_guide/00_liquid-handling/pumps/_pumps.html)
  and [pumps API](https://docs.pylabrobot.org/stable/api/pylabrobot.pumps.html).
- [Stable heating/shaking guide](https://docs.pylabrobot.org/stable/user_guide/01_material-handling/heating_shaking/heating_shaking.html)
  and [heating/shaking API](https://docs.pylabrobot.org/stable/api/pylabrobot.heating_shaking.html).
- [Stable centrifuge guide](https://docs.pylabrobot.org/stable/user_guide/01_material-handling/centrifuge/_centrifuge.html)
  and [centrifuge API](https://docs.pylabrobot.org/stable/api/pylabrobot.centrifuge.html).
- [`v0.2.1` pumps](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/pumps),
  [heating/shaking](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/heating_shaking),
  and [centrifuge](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/centrifuge)
  source — exact methods/classes; tag dated 2026-03-23.
- [Changelog `Unreleased`](https://github.com/PyLabRobot/pylabrobot/blob/main/CHANGELOG.md#unreleased)
  — development-only MicroSpin.
