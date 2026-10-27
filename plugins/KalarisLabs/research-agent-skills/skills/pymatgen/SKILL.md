---
name: pymatgen
description: Analyzes, validates, converts, and transforms crystal structures and molecules with pymatgen. It covers CIF/POSCAR/XYZ/JSON conversion, symmetry-tolerance sweeps, local phase diagrams from computed entries, VASP and Q-Chem I/O, band structure and DOS parsing, and bounded Materials Project (mp-api) queries. Use when validating a CIF or checking disorder and oxidation states. Use when assigning space groups and testing symprec sensitivity. Use when converting structure files and checking for representation loss. Use when building a convex hull from total energies. Use when querying Materials Project with explicit fields and limits. Not for general molecular dynamics or non-materials cheminformatics.
license: MIT
compatibility: Python 3.11+ with uv. The verified snapshot uses pymatgen 2026.5.4, pymatgen-core 2026.7.16, and mp-api 0.46.4. Bundled help and planning CLIs use only the standard library; local scientific execution lazily requires the pinned pymatgen packages. Materials Project access additionally requires explicit network approval and the single named secret MP_API_KEY.
allowed-tools: Read Write Bash Glob Python
metadata:
  version: '1.3'
  category: physical-sciences
  maintainer: Kalaris Labs
  last-reviewed: '2026-07-23'
  tags: materials science, crystal structures, computational materials, VASP, physics
---

# pymatgen

Use pymatgen for explicit, provenance-preserving work with compositions,
molecules, periodic structures, computed entries, symmetry, phase diagrams,
electronic structures, and electronic-structure-code files. Treat every parse,
conversion, symmetry assignment, transformation, and database result as
method- and parameter-dependent.

The MIT frontmatter license covers this skill. `pymatgen` and
`pymatgen-core` are MIT; `mp-api` declares BSD-3-Clause-LBNL. Materials Project
data is generally CC BY 4.0, while contributed data remains owned by its
contributors. Check the exact artifact and data terms before redistribution.

## Verified snapshot (2026-07-23)

- `pymatgen==2026.5.4` is the latest stable wrapper release (2026-05-04).
  Package metadata requires Python 3.11+ and directly requires
  `pymatgen-core>=2026.4.16`.
- `pymatgen-core==2026.7.16` is the latest stable core release (2026-07-16).
  It now contains core objects, symmetry/lattice operations, and the I/O layer,
  all under the existing `pymatgen.*` namespace.
- `mp-api==0.46.4` is the latest stable Materials Project client
  (2026-06-15), requires Python 3.11+, and depends on
  `pymatgen>2024.2.20`.
- The current API site is built from 2026.7.16 core documentation. Pinning both
  distributions prevents `pymatgen==2026.5.4` from silently resolving to a
  different future core.
- Pymatgen uses date-based versions. PyPI renders the date with dots; do not
  infer semantic-version compatibility from the numbers.

Create a project lock for reproducibility:

```bash
uv init --python 3.11
uv add "pymatgen==2026.5.4" "pymatgen-core==2026.7.16" "mp-api==0.46.4"
uv lock
uv sync --frozen
```

For a disposable reviewed environment:

```bash
uv venv --python 3.11 .venv-pymatgen
uv pip install --python .venv-pymatgen/bin/python \
  "pymatgen==2026.5.4" "pymatgen-core==2026.7.16" "mp-api==0.46.4"
```

Direct pins do not freeze all transitive wheels. Preserve `uv.lock`, platform,
Python version, package versions, and artifact hashes.

## Required workflow

1. State whether the object is a non-periodic `Molecule` or periodic
   `Structure`; record lattice and periodic boundary conditions.
2. State units. Pymatgen commonly uses Å, degrees, eV, eV/atom, amu, and
   g/cm³, but each API's documented contract is authoritative.
3. State coordinate mode. `Structure` coordinates are fractional unless
   `coords_are_cartesian=True`; `Molecule` coordinates are Cartesian.
4. Inspect every parser warning. For CIF, preserve occupancy, site-merging,
   stoichiometry, and correction warnings; do not silently accept fixes.
5. Report disorder/partial occupancies and oxidation-state decoration. Never
   guess oxidation states implicitly.
6. Run validation before symmetry, neighbor, transformation, conversion, or
   thermodynamic analysis.
7. Sweep symmetry tolerances and report `symprec` in Å and
   `angle_tolerance` in degrees with every assignment.
8. Treat transformations as new artifacts. Preserve the input, parameters,
   software versions, warnings, and parent/child checksums.
9. Before conversion, identify representation loss. Write only to a new path
   and round-trip-check scientifically relevant properties.
10. Build phase diagrams only from compatible total energies and correction
    schemes. A computed hull is conditional on the supplied entry set.
11. Keep all database access off by default. Disclose endpoint, filters,
    fields, result limit, cache behavior, output, license, and citation before
    an explicit execution step.
12. Preserve an artifact manifest. Never use pickle or load an untrusted
    general object graph; use schema-validated JSON and explicit constructors.

## Core objects

Use the public convenience imports:

```python
from pymatgen.core import Composition, Element, Lattice, Molecule, Structure

composition = Composition("LiFePO4", strict=True)
iron = Element("Fe")

lattice = Lattice.cubic(5.64)  # Å
structure = Structure(
    lattice,
    ["Na", "Cl"],
    [[0, 0, 0], [0.5, 0.5, 0.5]],
    coords_are_cartesian=False,
    validate_proximity=True,
)

molecule = Molecule(
    ["O", "H", "H"],
    [[0.0, 0.0, 0.0], [0.758, 0.0, 0.504], [-0.758, 0.0, 0.504]],
    charge=0,
    spin_multiplicity=1,
)
```

`Structure` and `Molecule` are mutable; use `IStructure`/`IMolecule` or an
explicit copy when mutation would compromise provenance. See
[core classes](references/core_classes.md).

## Safe local structure intake

Prefer the bundled validator, which captures CIF and Python warnings and
reports units, occupancy, disorder, oxidation states, periodicity, coordinate
mode, and minimum distances:

```bash
python scripts/composition_structure_validator.py composition "Fe2O3"
python scripts/composition_structure_validator.py structure structure.cif
python scripts/structure_analyzer.py structure.cif --symmetry
```

For direct CIF work, use the current parser method and inspect both warning
channels:

```python
import warnings
from pymatgen.io.cif import CifParser

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    parser = CifParser("input.cif", check_cif=True)
    structures = parser.parse_structures(
        primitive=False,
        check_occu=True,
        on_error="raise",
    )

parser_messages = list(parser.warnings)
python_messages = [str(item.message) for item in caught]
```

Do not parse untrusted files in a privileged process. A critical malicious-CIF
code-execution flaw affected pymatgen through 2024.2.8 and was fixed in
2024.2.20; the pinned release is newer, but parsers still process attacker
controlled input. Use isolation and CPU/RAM/disk/time limits.

## Symmetry

Space-group assignment depends on tolerances and structure quality:

```python
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

analyzer = SpacegroupAnalyzer(
    structure,
    symprec=0.01,          # Å
    angle_tolerance=5.0,   # degrees
)
symbol = analyzer.get_space_group_symbol()
number = analyzer.get_space_group_number()
```

The Materials Project pipeline commonly uses `symprec=0.1 Å`, while pymatgen's
documented default is `0.01 Å`; these can produce different assignments.
Generate a sensitivity report instead of changing tolerance until a preferred
answer appears:

```bash
python scripts/symmetry_sensitivity_report.py structure.cif \
  --symprec 0.001,0.01,0.1 --angle-tolerance 1,5
```

See [analysis modules](references/analysis_modules.md).

## Conversion and parser/writer I/O

Plan first; the planner does not open files or import pymatgen:

```bash
python scripts/io_conversion_plan.py \
  --input input.cif --input-format cif \
  --output POSCAR.new --output-format poscar \
  --periodic --coordinate-mode direct
```

Then convert to a new path with explicit loss acknowledgement:

```bash
python scripts/structure_converter.py input.cif POSCAR.new \
  --output-format poscar --coordinate-mode direct --allow-lossy \
  --acknowledge-parser-warnings
```

CIF, POSCAR, XYZ, and JSON do not preserve the same semantics. Check lattice,
periodicity, coordinate mode, species ordering, selective dynamics, site
properties, oxidation states, labels, and disorder after every conversion.
See [I/O formats](references/io_formats.md).

## Transformations and provenance

Transform a copy and preserve history:

```python
from pymatgen.alchemy.materials import TransformedStructure
from pymatgen.transformations.standard_transformations import (
    SubstitutionTransformation,
    SupercellTransformation,
)

tracked = TransformedStructure(structure.copy(), [])
tracked.append_transformation(SupercellTransformation([2, 2, 2]))
tracked.append_transformation(SubstitutionTransformation({"Na": "K"}))
derived = tracked.final_structure
history = tracked.history
```

One-to-many ordering, doping, slab, and magnetic transformations can expand
combinatorially or invoke optional executables. Bound candidates, sites,
supercell size, runtime, and output count. See
[transformations and workflows](references/transformations_workflows.md).

## Local phase diagrams

The bundled generator is offline and accepts only a strict JSON schema with
total eV per entry and provenance:

```json
{
  "schema_version": "1.0",
  "energy_unit": "eV",
  "energy_basis": "total_per_entry",
  "provenance": {
    "source": "reviewed local calculations",
    "method": "one compatible energy/correction scheme"
  },
  "entries": [
    {
      "entry_id": "local-Li",
      "composition": "Li",
      "energy_eV": -1.0,
      "provenance": {"source": "calculation manifest sha256:..."}
    }
  ]
}
```

```bash
python scripts/phase_diagram_generator.py entries.json --analyze Li2O
```

Elemental endpoints and all competing phases must be present. Do not mix raw
energies from different functionals, pseudopotentials, magnetic states, or
correction conventions. Computed on-hull status is not experimental stability.

## Band structures, DOS, VASP, and Q-Chem

Parse only the data needed:

```python
from pymatgen.io.vasp import Vasprun

run = Vasprun(
    "vasprun.xml",
    parse_dos=True,
    parse_eigen=True,
    parse_projected_eigen=False,
    parse_potcar_file=False,
)
band_structure = run.get_band_structure(line_mode=True)
band_gap = band_structure.get_band_gap()
complete_dos = run.complete_dos
```

Projected eigenvalues can require extreme memory. Verify convergence, k-path,
spin/SOC settings, Fermi-level conventions, smearing, and projection basis
before interpreting gaps or DOS. A parser success is not a converged
calculation.

Current Q-Chem interfaces are `pymatgen.io.qchem.inputs.QCInput` and
`pymatgen.io.qchem.outputs.QCOutput`:

```python
from pymatgen.io.qchem.inputs import QCInput

job = QCInput(
    molecule,
    rem={"job_type": "sp", "method": "wb97x-v", "basis": "def2-svpd"},
)
text = str(job)
```

Pymatgen writes inputs and parses outputs; it does not grant a VASP or Q-Chem
license or establish method validity. POTCAR files are VASP-licensed and are
not distributed by pymatgen. Never redistribute them or scan unrelated
directories for them. Optional tools such as enumlib, Bader, packmol, ffmpeg,
and Zeo++ are native/external executables: review provenance, licenses, argv,
working directory, and resource limits before a separate explicit invocation.

## Materials Project: plan before network

Use only:

```python
from mp_api.client import MPRester
```

The client reads `MP_API_KEY` when constructed. Supply only that named
environment variable through the user's shell or secret manager. Do not accept
the key as a CLI argument, traverse `.env` files, dump environment variables,
or print exception data without redaction.

Dry-run planning is the default:

```bash
python scripts/mp_query.py \
  --chemsys Li-Fe-O \
  --energy-above-hull 0 0.05 \
  --fields formula_pretty,energy_above_hull,band_gap,origins \
  --limit 25
```

Only `--execute` permits one bounded summary query and requires a new output:

```bash
python scripts/mp_query.py \
  --material-id mp-149 \
  --fields formula_pretty,structure,origins,last_updated \
  --limit 1 --output mp-149.json --execute
```

The CLI sets `num_chunks=1`, requires explicit fields and filters, caps results,
does not implement an implicit result cache, and never overwrites output.
`MPRester` initialization also performs compatibility/heartbeat metadata
requests; the plan discloses these, disables the platform-detail user agent and
local database-version notification log, and records the returned database
version. The summary workflow does not request full-dataset cache downloads.
`mp-api` 0.46.4 retries HTTP 429/502/504 according to its own configured policy
and respects `Retry-After`; do not invent a numeric service quota or add an
unbounded retry loop.

Materials Project core values are computed, method-dependent data—not
experimental truth. PBE commonly overestimates lattice parameters and
systematically underestimates band gaps; aggregated values can change across
database releases. Preserve retrieval time, query, fields, material/task
origins, database release when available, client versions, CC BY attribution,
and the canonical plus property-specific citations. See
[Materials Project API](references/materials_project_api.md).

## Bundled CLIs

All CLIs have dependency-free `--help`, lazy scientific imports, bounded JSON,
and no implicit network:

- `scripts/composition_structure_validator.py` — strict composition/structure
  checks; optional oxidation-state guessing is explicit and bounded.
- `scripts/structure_analyzer.py` — bounded lattice, sites, symmetry, distance,
  and optional CrystalNN report.
- `scripts/symmetry_sensitivity_report.py` — tolerance-grid space groups.
- `scripts/io_conversion_plan.py` — dependency-free representation-loss plan.
- `scripts/structure_converter.py` — one-file conversion to a new path.
- `scripts/phase_diagram_generator.py` — strict local computed-entry hull.
- `scripts/mp_query.py` — dry-run MP query plan and opt-in bounded client.
- `scripts/artifact_manifest.py` — checksums, versions, sources, and provenance.

Use:

```bash
python scripts/artifact_manifest.py \
  --artifact input.cif --artifact analysis.json \
  --workflow "local symmetry sensitivity" --output manifest.json
```

## References

- [Core classes](references/core_classes.md)
- [I/O formats, VASP, and Q-Chem](references/io_formats.md)
- [Analysis, symmetry, phase diagrams, bands, and DOS](references/analysis_modules.md)
- [Transformations and workflows](references/transformations_workflows.md)
- [Materials Project API, provenance, license, and limits](references/materials_project_api.md)

## Sources (verified 2026-07-23)

- [pymatgen 2026.5.4 on PyPI](https://pypi.org/project/pymatgen/)
- [pymatgen-core 2026.7.16 on PyPI](https://pypi.org/project/pymatgen-core/)
- [pymatgen API documentation](https://pymatgen.org/)
- [pymatgen changelog](https://pymatgen.org/CHANGES.html)
- [mp-api 0.46.4 on PyPI](https://pypi.org/project/mp-api/)
- [Materials Project API getting started](https://docs.materialsproject.org/downloading-data/using-the-api/getting-started)
- [Materials Project query guide](https://docs.materialsproject.org/downloading-data/using-the-api/querying-data)
- [Materials Project FAQ and computed-data caveats](https://docs.materialsproject.org/frequently-asked-questions)
- [Materials Project citation page](https://materialsproject.org/about/cite)
- [Official tutorial series endorsed by pymatgen](https://github.com/computron/pymatgen_tutorials)

## Agent operating procedure

1. **Check the environment.** Confirm library versions, units, coordinate systems and data formats (FITS, CIF, HDF5, netCDF).
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run on a small grid, region or subset and check physical plausibility.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check units and dimensional consistency, conservation laws or known limits, and numerical convergence.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Results violate known physical limits | Check units, boundary conditions and solver tolerances before reporting. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Report uncertainties and numerical tolerances with every quantitative result.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `molfeat`: Converts SMILES strings or RDKit/datamol molecules into numerical features using molfeat (0.11.0), which provides calculators, scikit-learn…
- `protocolsio-integration`: Reads, validates, and exports protocols.io data using the documented REST v3/v4 endpoints and the official MCP endpoint, and builds non-exe…
