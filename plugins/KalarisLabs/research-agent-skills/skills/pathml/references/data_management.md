# Data management, h5path, manifests, datasets, and provenance

This reference targets **PathML 3.0.5 stable** and a local, de-identified research
workflow.

## Data boundaries

Separate four classes of data:

1. **Source slides** — immutable, access-controlled originals.
2. **Linkage data** — direct identifiers and the pseudonym mapping, held outside
   the analysis workspace by an authorized custodian.
3. **Analysis data** — pseudonymous manifests, tiles, masks, counts, graphs, and
   features.
4. **Reports/models** — potentially identifying derived artifacts that still
   require governance.

Do not assume derived images or embeddings are anonymous. Rare morphology,
scanner metadata, dates, or cohort combinations can re-identify a participant.
Apply the minimum-necessary principle and institutional retention policy.

## Manifest first

Use one row per slide. Recommended columns:

```text
slide_id,patient_id,specimen_id,path,split,stain,backend,site,scanner
```

Rules:

- IDs are pseudonyms, not MRNs, accessions, initials, dates, or names.
- `slide_id` is unique.
- one `patient_id` maps to exactly one split;
- one slide path maps to one slide ID;
- paths are local, relative to a declared root where possible;
- URLs and symlinks are rejected;
- split values are a fixed allowlist such as `train`, `validation`, `test`;
- serial sections, rescans, and multiple blocks from one patient remain together.

Validate before PathML:

```bash
python scripts/slide_manifest.py validate \
  --manifest metadata/manifest.csv \
  --root .
```

The validator checks strict CSV structure, duplicate IDs/paths, missing local
files, unsafe paths, supported suffixes, and patient/slide leakage. It does not
upload data or inspect arbitrary clinical fields.

## h5path format

PathML processes slides into an HDF5-based `.h5path` file. Stable documentation
describes:

```text
root/
├── fields/
│   ├── labels/          # slide-level attributes
│   └── slide_type/      # stain/platform flags
├── masks/               # slide-level masks
├── counts/              # AnnData-like counts storage
└── tiles/
    ├── attributes       # tile_shape, tile_stride
    └── "(i, j)"/
        ├── array
        ├── masks/
        ├── labels/
        └── attributes   # coords, name
```

Write and reopen through public APIs:

```python
from pathml.core import SlideData

slide.write("derived/slide-001.h5path")
reopened = SlideData("derived/slide-001.h5path")
```

There is no stable `to_hdf5()`, `from_hdf5()`, or
`load_tiles_from_hdf5()` API. `SlideDataset.write(directory, filenames=None)`
calls each slide's `write()`.

Stable documentation states HDF5 datasets are stored as `float16`; confirm dtype
for the exact arrays your workflow writes. Quantitative marker intensities can
lose precision if silently cast. Record and test expected dtype, range, NaN/Inf,
compression, and round-trip tolerance.

## h5path trust boundary

Treat `.h5path` as a structured binary input, not harmless data:

- HDF5 parsers have a large attack surface; open third-party files in isolation.
- PathML 3.0.5 `TileDataset` dynamically interprets the stored `tile_shape`
  attribute as a Python expression. Never open an untrusted `.h5path`.
- Labels can contain sensitive values. Do not copy direct identifiers into HDF5.
- A malformed file can request large allocations. Check file size and schema
  before loading.
- Do not edit HDF5 concurrently from multiple processes unless the access pattern
  is explicitly designed and tested.

Use a sidecar JSON manifest for provenance rather than relying on arbitrary HDF5
labels. Keep the JSON strict, bounded, pseudonymous, and versioned.

## PyTorch tile dataset

The canonical stable import is:

```python
from pathml.datasets import TileDataset
from torch.utils.data import DataLoader

tiles = TileDataset("derived/slide-001.h5path")
loader = DataLoader(
    tiles,
    batch_size=8,
    shuffle=False,
    num_workers=0,
)
```

Each item is:

```text
(tile_image, tile_masks, tile_labels, slide_labels)
```

Shapes:

- RGB/multichannel 3-D input becomes `(C, H, W)`.
- 5-D PathML input `(i, j, z, c, t)` becomes `(T, C, Z, W, H)` in stable
  source; verify axis semantics before use.
- masks are stacked as `(n_masks, tile_height, tile_width)` when present.
- label dictionaries are user-defined and may need a custom `collate_fn`.

Do not assume mask dictionary order carries semantics. Persist ordered mask names
in a separate schema and assert them when loading.

`pathml.ml.TileDataset` is also exported in 3.0.5, but
`pathml.datasets.TileDataset` is the documented dataset API.

## SlideDataset

`SlideDataset(slides)` accepts a list of already constructed `SlideData` objects:

```python
from pathml.core import HESlide, SlideDataset

slides = [
    HESlide("data/slide-001.svs", backend="openslide"),
    HESlide("data/slide-002.svs", backend="openslide"),
]
cohort = SlideDataset(slides)
cohort.run(pipeline, distributed=False, tile_size=512, level=0)
cohort.write("derived")
```

It does not accept a glob/path list plus tiling arguments as a constructor.
Preserve a deterministic manifest order and map output filenames explicitly.

## Public data modules

Stable `pathml.datasets` exports:

```python
from pathml.datasets import DeepFocusDataModule, PanNukeDataModule
```

### PanNuke

```python
pannuke = PanNukeDataModule(
    data_dir="approved_data/pannuke",
    download=False,
    shuffle=True,
    nucleus_type_labels=True,
    split=1,
    batch_size=8,
    hovernet_preprocess=True,
)
```

- 7,901 256-pixel patches, 19 tissue types, five nucleus categories plus
  background.
- `download=False` is the safe default.
- `download=True` downloads three ZIPs from Warwick and extracts them.
- `split` must be 1, 2, 3, or `None`; each integer rotates the three published
  folds across train/validation/test.
- `split=None` exposes the whole dataset; do not use it for performance
  estimation.

Published folds are not a substitute for verifying patient/source-slide
independence for the intended claim.

### DeepFocus

```python
deepfocus = DeepFocusDataModule(
    data_dir="approved_data/deepfocus",
    download=False,
    shuffle=True,
    batch_size=8,
)
```

- focus classification patches derived from four slides/patients and four stains;
- `download=True` contacts Zenodo;
- stable code checks the downloaded HDF5 file against a fixed MD5 value.

MD5 here is an upstream integrity check, not a modern provenance guarantee.
Record a SHA-256 and dataset license/source separately.

PathML 3.0.5 does **not** export `TCGADataModule`. Use a separately governed data
acquisition process for TCGA/GDC and document its API/version/consent terms.

## Download consent

Before changing any `download` flag to `True`, tell the user:

- exact host and expected dataset;
- approximate size (stable docs report PanNuke ~37.33 GB and DeepFocus ~10 GB);
- destination and available disk;
- dataset license/terms and citation;
- whether the environment logs outbound IP/account metadata; and
- that no local slide or clinical data will be uploaded.

Require explicit opt-in. Never place downloaded archives inside the repository.

## Graph datasets and unsafe `.pt` files

`pathml.datasets.EntityDataset` assembles cell graphs, tissue graphs, and
assignment matrices. Stable source opens `.pt` files using PyTorch object
deserialization with unrestricted object loading.

Consequences:

- only load artifacts created by the trusted project;
- never load an emailed/downloaded `.pt` file merely to inspect it;
- verify SHA-256, producer, code revision, PyTorch/PyG versions, and schema;
- prefer non-executable interchange formats for exchange;
- run legacy artifacts in a disposable, network-disabled environment if review is
  unavoidable.

The bundled inference planner and graph validator never load `.pt`, `.pth`,
`.ckpt`, pickle, ONNX, or other model/graph binaries.

## Split design and leakage

Create the split column once, before tiling:

```text
patient → specimen/block → slide/rescan/serial section → region → tile
```

Everything below a patient follows the patient's split unless the scientific
design explicitly requires a stricter grouping.

Common leakage paths:

- overlapping tiles from one slide in different splits;
- serial sections or rescans assigned separately;
- stain reference fitted on all slides;
- QC threshold chosen after viewing test failures;
- normalization/scaling fit before split;
- graph neighborhoods crossing a split boundary;
- duplicated public patches;
- institution/scanner confounding;
- selecting a checkpoint on the test metric.

The manifest validator reports patient and slide leakage, but it cannot discover
unknown biological relatedness. Document grouping assumptions.

## Provenance sidecar

Recommended strict JSON fields:

```json
{
  "schema_version": "1.0",
  "pathml_version": "3.0.5",
  "source_sha256": "hex-digest",
  "slide_id": "slide-001",
  "patient_id": "patient-001",
  "split": "train",
  "backend": "openslide",
  "level": 0,
  "downsample": 1.0,
  "mpp_x": null,
  "mpp_y": null,
  "tile_size_ij": [512, 512],
  "tile_stride_ij": [512, 512],
  "tile_pad": false,
  "pipeline_id": "he-v1",
  "code_revision": "project-commit",
  "created_utc": "RFC3339 timestamp"
}
```

Do not put a direct identifier in these fields. Add:

- ordered transform parameters and fitted stain arrays;
- mask/label schema;
- QC counts and exclusion reasons;
- dependency lock hash;
- model artifact SHA-256 and license;
- random seed manifest;
- coordinate units and conversion;
- output hashes and software/hardware details.

Use SHA-256 for provenance:

```python
import hashlib
from pathlib import Path

def sha256_file(path: Path, chunk_bytes: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

Hash only authorized local files and expect full-slide hashing to be I/O-heavy.
Do not print paths containing identifiers.

## Storage and lifecycle checklist

- Estimate raw, temporary, `.h5path`, mask, count, graph, and model storage.
- Write to a same-filesystem temporary destination, validate, then atomically
  rename where possible.
- Do not overwrite source slides.
- Use private permissions and encrypted storage/backups.
- Verify output counts, shapes, dtypes, coordinates, and hashes.
- Record partial failures and retry policy.
- Test disaster recovery and retention/deletion.
- Do not commit slide data, model binaries, linkage files, or manifests with PHI.

## Sources, accessed 2026-07-23

- Stable h5path guide:
  https://pathml.readthedocs.io/en/stable/h5path.html
- Stable datasets guide:
  https://pathml.readthedocs.io/en/stable/datasets.html
- Stable datasets API:
  https://pathml.readthedocs.io/en/stable/api_datasets_reference.html
- Stable `TileDataset`/`EntityDataset` source:
  https://github.com/Dana-Farber-AIOS/pathml/blob/v3.0.5/pathml/datasets/datasets.py
- Stable PanNuke source:
  https://github.com/Dana-Farber-AIOS/pathml/blob/v3.0.5/pathml/datasets/pannuke.py
- Stable DeepFocus source:
  https://github.com/Dana-Farber-AIOS/pathml/blob/v3.0.5/pathml/datasets/deepfocus.py
- PanNuke extension paper: https://arxiv.org/abs/2003.10778
- DeepFocus paper: https://doi.org/10.1371/journal.pone.0205387
