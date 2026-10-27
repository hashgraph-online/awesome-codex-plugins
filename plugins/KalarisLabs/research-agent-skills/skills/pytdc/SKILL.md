---
name: pytdc
description: Uses the PyTDC package (import tdc, Therapeutics Data Commons) to discover therapeutic ML tasks from tdc.metadata, plan and load approved datasets, apply task-aware splits (random, scaffold, cold_split, combination, time), run evaluator metrics, evaluate benchmark groups such as admet_group, and run bounded molecular-oracle scoring. Use when selecting a TDC task or dataset, planning a download-free split, scoring predictions with TDC evaluators, running a benchmark group evaluation, or checking dataset licenses and cache effects before downloading. Use when scoring molecules with TDC oracles like QED. Not for generic RDKit cheminformatics or training molecule generators.
license: MIT
compatibility: Requires uv, CPython 3.11, PyTDC 1.1.15, and setuptools 80.9.0 for its legacy pkg_resources runtime import. Dataset, benchmark, checkpoint, and remote-oracle operations require network/storage review and explicit user approval.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: scientific-databases
  maintainer: Kalaris Labs
  tags: therapeutics, drug discovery datasets, benchmarks, machine learning, ADMET
---

# PyTDC (Therapeutics Data Commons)

Use the official `PyTDC` distribution (`import tdc`) to discover therapeutic ML
tasks, load approved datasets, apply task-appropriate splits, evaluate predictions,
and work with curated benchmark groups. Prefer package metadata over copied dataset
lists, and plan network/storage effects before constructing any loader.

## Verified snapshot

- Research date: **2026-07-23**
- PyPI stable: **PyTDC 1.1.15**, released 2025-03-31
- Package/source repository: `mims-harvard/TDC`
- Code license: MIT
- PyPI supplies only a source distribution and declares no `Requires-Python`
- The dependency graph makes **CPython 3.11** the reproducible target used here:
  `cellxgene-census==1.15.0` excludes Python 3.12, and PyTDC's constrained
  RDKit release has no CPython 3.13 wheel
- PyTDC imports deprecated `pkg_resources` at runtime. Setuptools 82 removed that
  module; pin the verified compatibility release **setuptools 80.9.0**.
- `tdc.readthedocs.io` still identifies itself as TDC 0.4.1; use it as API
  cross-reference, not as release-version evidence
- Upstream publishes no GitHub tags/releases or maintained changelog. Treat
  undocumented migration claims as uncertainty and verify against the installed
  1.1.15 source/metadata.

See [references/sources.md](references/sources.md) for dated evidence and known
documentation conflicts.

## Installation

Use an isolated CPython 3.11 environment and pin the reviewed snapshot:

```bash
uv venv --python 3.11 .venv-pytdc
uv pip install --dry-run --python .venv-pytdc/bin/python \
  "setuptools==80.9.0" "PyTDC==1.1.15"
uv pip install --python .venv-pytdc/bin/python \
  "setuptools==80.9.0" "PyTDC==1.1.15"
```

The tested macOS ARM64 resolution installed 123 packages, including large
scientific/ML dependencies, so the environment itself can transfer and occupy
hundreds of megabytes before any dataset is downloaded. Review the dry run and
available disk first. The direct pins identify the reviewed API snapshot; generate
a platform-specific `uv.lock` in the user's project when every transitive version
must also be frozen.

For an ephemeral command:

```bash
uv run --python 3.11 \
  --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind tasks
```

To check for a newer release, inspect the PyPI release history at
<https://pypi.org/project/pytdc/>. Before changing the pin, compare its source
distribution, dependencies, official repository, task registries, and smoke tests;
do not silently substitute the separate `pytdc-nextml` package.

## Non-negotiable data and network policy

1. **Discover first.** Reading `tdc.metadata` or using
   `scripts/discover_metadata.py` does not instantiate a loader or download data.
2. **Plan second.** Record the exact task/dataset, official task page, license,
   expected size, cache directory, split, metric, and reproducibility seed.
3. **Ask the user before downloading.** Loader constructors fetch missing data.
   Some datasets and benchmark-group archives are large; model-backed oracles can
   fetch checkpoints; remote/docking oracles can transmit molecular structures.
4. **Execute only after approval.** In bundled CLIs, `--execute` acknowledges
   execution and `--download` is additionally required for MolGen corpora or
   supported oracle checkpoints.
5. **Keep outputs bounded.** Emit counts, schema, and small previews rather than
   full datasets, sequences, prediction arrays, or molecule corpora.

### Cache and cost behavior

- Ordinary loaders default to `path="./data"` and save files beneath that path.
  The bundled scripts instead default to explicit `.pytdc-*` directories.
- Core downloads use Harvard Dataverse file endpoints when a local filename is
  absent. Newer resource classes may use other upstream services.
- `admet_group(path=...)` and other benchmark-group constructors download and
  extract the group archive when `<path>/<group>` is absent.
- Download-backed `Oracle(...)` construction uses `./oracle` internally. The
  bundled oracle CLI changes into a safe runtime directory before approved calls.
- PyTDC 1.1.15 does not provide a universal cache quota, eviction policy, or
  dataset-wide checksum manifest. Use `scripts/cache_audit.py` and manage disk
  retention explicitly.
- Network transfer, local storage, decompression, parsing, feature generation,
  docking, and external service calls can all incur time or monetary cost.

The PyTDC **code** is MIT. Dataset/task licenses are heterogeneous: official task
pages include per-dataset terms ranging from Creative Commons licenses to
non-commercial restrictions or “Not Specified.” Verify the exact dataset's page and
original source terms before download, redistribution, publication, or commercial
use. Cite both TDC and the original dataset.

## Start with metadata-only discovery

From this skill directory:

```bash
uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind datasets --task ADME --limit 50

uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind benchmarks --limit 50

uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind evaluators --limit 100
```

The package API is also metadata-only:

```python
from tdc.utils import retrieve_dataset_names, retrieve_benchmark_names

adme_names = retrieve_dataset_names("ADME")
admet_benchmarks = retrieve_benchmark_names("admet_group")
```

Use exact returned names. PyTDC performs fuzzy matching internally, but explicit
matching avoids silently selecting the wrong dataset/oracle.

## Dataset workflow

Plan a split without downloading:

```bash
uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/load_and_split_data.py \
  --task ADME --dataset Caco2_Wang --method scaffold \
  --seed 42 --data-dir .pytdc-data
```

After the user approves the dataset, license, transfer, and storage:

```bash
uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/load_and_split_data.py \
  --task ADME --dataset Caco2_Wang --method scaffold \
  --seed 42 --data-dir .pytdc-data --execute
```

Verified public import patterns include:

```python
from tdc.single_pred import ADME, Tox
from tdc.multi_pred import DDI, DTI
from tdc.generation import MolGen, Reaction, RetroSyn
```

Constructors perform data access, so do not run them before approval:

```python
data = ADME(name="Caco2_Wang", path=".pytdc-data")
frame = data.get_data(format="df")
split = data.get_split(
    method="scaffold",
    seed=42,
    frac=[0.7, 0.1, 0.2],
)
# split keys are: train, valid, test
```

Read [references/datasets.md](references/datasets.md) before choosing a task or
dataset.

## Split selection without overclaiming leakage control

- `random`: default for loaders; default seed 42 and fractions 0.7/0.1/0.2.
- `scaffold`: documented generic support for molecule-based ADME, Tox, and HTS.
  PyTDC groups RDKit Bemis–Murcko scaffold strings (chirality disabled), but that
  does **not** prove absence of analog, duplicate, label, temporal, or provenance
  leakage.
- `cold_split`: multi-instance API. Pass exact dataframe columns, for example
  `method="cold_split", column_name=["Drug", "Target"]`. Multi-column splitting can
  discard cross-partition rows and need not preserve requested row fractions.
- `combination`: built-in DrugSyn combination split.
- `time`: pair-loader API requiring `time_column`; the verified built-in case is
  `BindingDB_Patent` with its `Year` column. The API spelling is `time`, not
  `temporal`.

Do not use undocumented `cold_drug_target`, `temporal`, or `stratified=True`
examples. For every split, record PyTDC version, parameters, row counts, and exact
entity overlap audits. PyTDC 1.1.15's random splitter uses the supplied seed for
test sampling but a fixed `random_state=1` for validation sampling; do not describe
all partitions as independently varying with the seed.

Detailed semantics and caveats are in
[references/utilities.md](references/utilities.md).

## Evaluators

Use exact names from the installed evaluator registry:

```python
from tdc import Evaluator

mae = Evaluator(name="MAE")(y_true, y_pred)
auroc = Evaluator(name="ROC-AUC")(y_true_binary, predicted_scores)
pcc = Evaluator(name="PCC")(y_true, y_pred)
```

`PCC` is the registered Pearson-correlation name; `Pearson` is not. Multi-class
registry names are `micro-f1`, `macro-f1`, and `kappa`. Thresholded binary metrics
default to 0.5. Metric direction and input shape are metric-specific; use the
official task/benchmark metric rather than choosing from task type alone.

## Benchmark groups

Use specialized classes. Top-level `from tdc import BenchmarkGroup` is retained
only as a deprecated compatibility path in 1.1.15.

```python
from tdc.benchmark_group import admet_group

# Run only after approval: construction may download the group archive.
group = admet_group(path=".pytdc-benchmarks")
benchmark = group.get("Caco2_Wang")
train_val = benchmark["train_val"]
test = benchmark["test"]
train, valid = group.get_train_valid_split(
    seed=1,
    benchmark=benchmark["name"],
    split_type="default",
)
```

For one run, `group.evaluate({name: test_predictions})` returns metric results.
For leaderboard aggregation, pass a **list of at least five prediction
dictionaries** to `group.evaluate_many(...)`. Do not index `group.get(...)` by
seed, and do not derive dummy predictions from test labels.

Use `scripts/benchmark_evaluation.py` to validate a bounded JSON prediction plan
before any group download. See [references/utilities.md](references/utilities.md)
for the exact JSON shape and API behavior.

## Molecular generation and oracles

PyTDC supplies molecule corpora, evaluators, and oracles; it does not train or
provide a generic molecule generator in the core workflow. Discover current names:

```bash
uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind oracles --limit 100
```

Plan bounded local QED scoring:

```bash
uv run --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/molecular_generation.py score --oracle QED --smiles CCO
```

Add `--execute` only after review. LogP and SA call the downloadable `fpscores`
artifact in 1.1.15; they and DRD2/GSK3B/JNK3/CYP3A4_Veith also require
`--download`. The helper intentionally refuses remote services, docking,
distribution, and composite oracles. It preserves input order and never assumes
score direction.

Read [references/oracles.md](references/oracles.md) before any oracle call.

## Bundled resources

### Scripts

- `scripts/discover_metadata.py` — download-free package registry discovery
- `scripts/load_and_split_data.py` — task-aware split plan/explicit execution
- `scripts/benchmark_evaluation.py` — prediction validation and explicit evaluation
- `scripts/molecular_generation.py` — bounded local/checkpoint scoring and MolGen plan
- `scripts/cache_audit.py` — read-only bounded cache manifest

Every CLI uses lazy optional imports, safe relative output/cache paths, JSON
summaries, bounded output, and no implicit dataset/model download.

### References

- [references/datasets.md](references/datasets.md) — task discovery, data access,
  cache behavior, and licensing
- [references/utilities.md](references/utilities.md) — splits, evaluators, and
  benchmark-group APIs
- [references/oracles.md](references/oracles.md) — oracle categories, side effects,
  and safe execution
- [references/sources.md](references/sources.md) — dated authoritative sources and
  unresolved upstream gaps

## Agent operating procedure

1. **Check the environment.** Confirm network access, API keys (if required) and the database's current API documentation and rate limits.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Fetch a single known record and check the response format before bulk queries.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Identifiers resolve, record counts are reported, and the database version or access date is recorded.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| HTTP 429 or 5xx errors | Respect rate limits with backoff, batch requests, and report partial results honestly. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never invent accession numbers, IDs or records; report 'not found' instead.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `deepchem`: Molecular ML with diverse featurizers and pre-built datasets.
