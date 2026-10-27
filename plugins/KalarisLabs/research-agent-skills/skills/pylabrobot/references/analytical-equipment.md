# Analytical equipment

Verified against **PyLabRobot 0.2.1** on **2026-07-23**. This reference describes
APIs without connecting to or commanding instruments.

## Plate-reader frontend

Stable imports include:

```python
from pylabrobot.plate_reading import (
    CLARIOstarBackend,
    Cytation5Backend,
    PlateReader,
    PlateReaderChatterboxBackend,
)
```

`PlateReader` is a resource and requires dimensions plus a backend:

```text
PlateReader(name, size_x, size_y, size_z, backend, rotation=None,
            category="plate_reader", model=None,
            child_location=Coordinate(...), preferred_pickup_location=None)
```

Do not copy the stale constructor
`PlateReader(name="CLARIOstar", backend=CLARIOstarBackend())`; the stable
frontend requires `size_x`, `size_y`, and `size_z`.

Verified frontend methods include:

```text
open(**backend_kwargs)
close(**backend_kwargs)
read_absorbance(wavelength, wells=None, use_new_return_type=False,
                **backend_kwargs)
read_fluorescence(excitation_wavelength, emission_wavelength, focal_height,
                  wells=None, use_new_return_type=False, **backend_kwargs)
read_luminescence(focal_height, wells=None, use_new_return_type=False,
                  **backend_kwargs)
```

The old examples in this skill incorrectly treated return values as a guaranteed
NumPy `8x12` array and omitted required focal height. In 0.2.1 the annotated
return is `List[Dict]`; backend and `use_new_return_type` affect the concrete
shape. Record the exact method arguments, plate/well mapping, instrument
settings, raw response, and package/backend version before analysis.

`PlateReader` does not expose a universal `set_temperature` method in the
verified 0.2.1 frontend. Temperature, shaking, injectors, kinetics, pathlength,
read mode, and optics are backend/model-specific; do not infer them from another
reader.

## Offline interface checks

`PlateReaderChatterboxBackend` is available for software-only frontend testing.
It can exercise method calls and resource state without an instrument, but it
does not simulate optics, plate seating, thermal behavior, gain, focus,
measurement noise, or assay chemistry.

For import and method-presence checks without backend construction:

```bash
python3 skills/pylabrobot/scripts/inspect_backends.py \
  --expected-version 0.2.1 --strict
```

The inspector does not call `setup()` and makes no transport connection.

## Stable plate-reader inventory

The stable 0.2.1 supported-machines page lists:

- **BMG Labtech CLARIOstar (Plus): Full** — absorbance, fluorescence,
  luminescence.
- **Agilent/BioTek Cytation 1 and Cytation 5: Full** — absorbance,
  fluorescence, luminescence, microscopy.
- **Agilent/BioTek Synergy H1: Full**.
- **Byonoy Absorbance 96 Automate: Full**.
- **Byonoy Luminescence 96 and Luminescence 96 Automate: Full**.
- **Molecular Devices SpectraMax M5e: Full**.
- **Molecular Devices SpectraMax 384plus: Full**.
- **Molecular Devices ImageXpress Pico: Basics**.
- **Tecan Infinite 200 PRO: Mostly**.

The installed 0.2.1 package also exports
`ExperimentalTecanInfinite200ProBackend` and `ExperimentalSparkBackend`; the
`Experimental` prefix is meaningful. The 0.2.1 changelog records Infinite 200
PRO and Spark backend additions, but do not upgrade that to a generic/full
support claim.

Support is model-specific. Confirm serial/FTDI/USB/SiLA/microscopy extras,
firmware, instrument options, plate types, optics, and methods on the exact
stable page.

## Plate-reader live-run checklist

Before a separately authorized connection or read:

1. Confirm instrument model, serial/device ID, firmware, approved transport,
   exclusive control, and current calibration/QC.
2. Confirm plate manufacturer/catalog, format, material, bottom, lid/seal,
   orientation, barcode, and correct seating.
3. Confirm read mode and units: wavelength(s), focal height, gain, flashes,
   integration, shaking, temperature, kinetics, injectors, well selection, and
   read direction as applicable.
4. Check tray/door state and robot/manual transfer path; prevent closing on an
   obstruction or moving a plate while a device is active.
5. Include blanks, standards, controls, expected ranges, saturation rules, and
   acceptance criteria.
6. Save raw data and complete settings before derived analysis.

Opening/closing a tray is physical motion. Never call it merely to test
connectivity.

## Scales

Stable frontend:

```python
from pylabrobot.scales import Scale
```

Verified methods are:

```text
get_weight(**backend_kwargs) -> float
tare(**backend_kwargs)
zero(**backend_kwargs)
```

The stable README shows the model-specific backend:

```python
from pylabrobot.scales.mettler_toledo import MettlerToledoWXS205SDU
```

Do not instantiate it or call `setup()` during planning. Stable supported
machines lists the **Mettler Toledo WXS205SDU: Full**.

Before live weighing, verify:

- model, port, units, resolution, range, calibration, leveling, warm-up, and
  environmental limits;
- tare container, stability/status flags, vibration, drafts, static, and
  evaporation;
- whether returned values are stable/net/gross and how errors are represented;
- physical placement/removal route and collision clearance.

Mass is not automatically volume. Converting grams to microlitres requires a
validated density at the relevant temperature and uncertainty propagation. Do
not assume water density equals exactly `1 g/mL`.

## Coordinating liquid handlers and analytical devices

Treat each device as a separate state machine:

- never overlap motion unless the workcell has an approved interlock and
  scheduler;
- transfer ownership of a plate explicitly between deck, arm, reader, scale,
  and operator;
- verify doors/trays/buckets are in the required state;
- use unique plate IDs and record handoff timestamps;
- stop safely on partial failure; do not blindly retry a measurement or move;
- distinguish software resource assignment from physical plate location.

An async Python call does not create a physical safety interlock.

## Data integrity

For every measurement, retain:

- protocol and manifest revisions;
- PyLabRobot/backend version and instrument identity/firmware;
- plate/barcode and well map;
- complete acquisition settings and units;
- calibration/QC status, blanks/controls, timestamps, and error/status fields;
- unmodified raw output plus checksums;
- transformation code/version and rejected/out-of-range values.

Validate dimensions and well labels before joining measurement data to sample
metadata.

## Sources

Checked **2026-07-23**:

- [Stable supported machines](https://docs.pylabrobot.org/stable/user_guide/machines.html)
  — analytical inventory and support labels (page metadata surfaced
  2025-01-01; docs version 0.2.1).
- [Stable plate-reading guide](https://docs.pylabrobot.org/stable/user_guide/02_analytical/plate-reading/plate-reading.html)
  and [plate-reading API](https://docs.pylabrobot.org/stable/api/pylabrobot.plate_reading.html).
- [Stable scales guide](https://docs.pylabrobot.org/stable/user_guide/02_analytical/scales/scales.html)
  and [scales API](https://docs.pylabrobot.org/stable/api/pylabrobot.scales.html).
- [`v0.2.1` plate-reading source](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/plate_reading)
  and [scale source](https://github.com/PyLabRobot/pylabrobot/tree/v0.2.1/pylabrobot/scales)
  — exact constructors/methods; tag dated 2026-03-23.
- [0.2.1 changelog](https://github.com/PyLabRobot/pylabrobot/blob/main/CHANGELOG.md#021)
  — Tecan Infinite 200 PRO/Spark additions.
