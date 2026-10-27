---
name: pathml
description: 'Covers local, research-only computational pathology with PathML 3.0.5: loading and tiling whole-slide images (OpenSlide, Bio-Formats), preprocessing and QC pipelines run via SlideData.run(), .h5path data management, multiplex image quantification, spatial graph construction (KNN, RAG, HACT), and bounded local ONNX model inference planning. Use when loading or tiling slides, building tissue-mask or stain pipelines, managing .h5path files and patient-level splits, quantifying CODEX or Vectra multiplex images, or building cell and tissue graphs. Not for clinical diagnosis or patient care decisions.'
license: MIT
compatibility: PathML 3.0.5 is the latest PyPI release and targets Python 3.10-3.12; installation needs uv plus platform libraries for OpenSlide, BLAS/LAPACK, and Java/Bio-Formats. Bundled Python 3.10+ CLIs are local, bounded, dependency-free, and network-free.
allowed-tools: Read Write Edit Bash Glob
metadata:
  version: '1.2'
  category: clinical-and-health
  maintainer: Kalaris Labs
  tags: computational pathology, whole slide images, digital pathology, medical imaging
---

# PathML

## Scope and safety boundary

Use PathML for **local computational pathology research**. It is beta research
software, not a validated medical device, diagnostic system, clinical decision
support tool, or substitute for a pathologist. Do not use outputs to diagnose,
grade, stage, or treat a patient.

Pathology files may contain faces, labels, accession numbers, patient identifiers,
DICOM tags, filenames, or linked clinical data. Before processing:

1. Confirm authorization, consent/waiver, data-use terms, and institutional policy.
2. De-identify pixels and metadata; keep the re-identification key outside the
   analysis workspace.
3. Use pseudonymous `patient_id`, `slide_id`, and `specimen_id` values. Do not put
   direct identifiers in filenames, logs, `.h5path` labels, model cards, or reports.
4. Keep inputs, intermediates, and outputs on approved local encrypted storage.
5. Split by patient (then slide) before tiling or fitting any preprocessing step.

## Version baseline, verified 2026-07-23

- **Installable stable release:** PyPI `pathml==3.0.5`, published 2026-03-24.
- The v3.0.5 release notes state Python **3.10-3.12** and sunset 3.9.
  PyPI does not declare `Requires-Python` and still has a stale 3.8 classifier, so
  use the release statement and test the exact environment.
- GitHub releases v3.0.6 (2026-04-14) and v3.0.7 (2026-07-09) exist, but PyPI has
  no artifacts for them as of this review. v3.0.7 updates Torch/TorchVision/
  torch-geometric and ONNX export code. Do not mix those source dependencies with
  the 3.0.5 wheel.
- ReadTheDocs `/latest` identifies itself as 3.0.5. Examples here were checked
  against the v3.0.5 tag and PyPI wheel metadata, not unversioned snippets.
- This skill is MIT-licensed. PathML itself is GPL-2.0 with upstream commercial
  licensing options; review upstream terms before redistribution.

## Reproducible installation

Use Python 3.11 unless the project has tested another supported interpreter:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install "pathml==3.0.5"
python -c "import importlib.metadata as m; print(m.version('pathml'))"
```

PathML 3.0.5 declares no package extras: do **not** use `pathml[all]`. Its base
distribution pins a large scientific/ML stack, including Torch 2.8.0, ONNX 1.17.0,
ONNX Runtime 1.17.x, OpenSlide Python 1.3.1, python-bioformats 4.1.0, and
python-javabridge 4.0.4.

Install native prerequisites before the uv command:

```bash
# Debian/Ubuntu
sudo apt-get install openslide-tools gcc g++ libblas-dev liblapack-dev openjdk-17-jdk

# macOS
brew install openslide openjdk@17

# Windows OpenSlide option documented upstream
vcpkg install openslide
```

Java/Bio-Formats is needed for the broad multidimensional format backend.
OpenSlide handles common brightfield WSI formats more efficiently. CUDA is
optional and must match the pinned PyTorch build; follow PyTorch's platform
selector rather than guessing a CUDA wheel. See `references/image_loading.md`.

## Stable minimal workflow

PathML 3.0.5 uses slide convenience classes and `SlideData.run()`. It does not
provide `SlideData.from_slide()`, and `Pipeline` does not have `run()`:

```python
from pathml.core import HESlide
from pathml.preprocessing import BoxBlur, Pipeline, TissueDetectionHE

slide = HESlide("data/pseudonymous_slide.svs", backend="openslide")
pipeline = Pipeline(
    [
        BoxBlur(kernel_size=5),
        TissueDetectionHE(mask_name="tissue", min_region_size=5000),
    ]
)
slide.run(
    pipeline,
    distributed=False,
    tile_size=512,
    tile_stride=512,
    level=0,
    tile_pad=False,
)
slide.write("derived/pseudonymous_slide.h5path")
```

Start with a bounded manual sample before a full run:

```python
from itertools import islice

for tile in islice(slide.generate_tiles(shape=512, stride=512, level=0), 8):
    pipeline.apply(tile)
    assert tile.masks["tissue"].shape[:2] == tile.image.shape[:2]
```

Tiles use `(i, j)` = `(row, column)` coordinates at the selected pyramid level.
For OpenSlide, PathML maps them to level-0 coordinates internally. Record the
level and downsample; convert to `(x, y)` or micrometres explicitly downstream.

## Research workflow

1. **Inventory locally.** Validate the manifest, reject URLs/symlinks, inspect only
   allowlisted technical metadata, and remove identifiers.
2. **Freeze splits.** Assign every patient and all their slides to one split before
   generating overlapping tiles, graphs, normalization references, or features.
3. **Plan bounds.** Estimate tile count, RAM, output size, and pipeline stages.
4. **Pilot preprocessing.** Inspect tissue masks, whitespace/artifact labels,
   stain behavior, edge padding, and empty-mask cases on representative training
   slides. Do not tune from test slides.
5. **Run and preserve coordinates.** Keep tile level, `(i, j)`, downsample, MPP,
   mask names, QC decisions, and failed/skipped tiles.
6. **Build spatial data deliberately.** Validate channel order, physical units,
   instance labels, node-feature alignment, graph edges, and cell-to-tissue
   assignments.
7. **Infer in bounded batches.** Verify model provenance and checksum without
   loading unknown pickle checkpoints. Keep predictions linked to slide/tile
   coordinates and stitch overlaps with a documented rule.
8. **Report provenance and limits.** Include package lock, source hashes, scanner,
   stain, parameters, seeds, split manifest, model card, exclusions, and QC.

## No-network default and explicit consent gate

Do not instantiate download-capable classes or set dataset `download=True` unless
the user explicitly opts in after receiving the endpoint and disclosure:

- `SegmentMIFRemote` downloads an ONNX file from
  `https://huggingface.co/pathml/test/resolve/main/mesmer.onnx` at construction,
  then runs inference locally. Stable source does **not** upload image pixels.
  The request still discloses network metadata such as IP address and headers and
  creates `temp.onnx`; there is no built-in checksum or offline flag.
- Deprecated `SegmentMIF` imports local DeepCell Mesmer, but DeepCell model
  initialization may need separately provisioned weights. It is not a PathML
  extra and is not the preferred stable API.
- `RemoteTestHoverNet` downloads a model from Hugging Face.
- `PanNukeDataModule(download=True)` contacts Warwick; `DeepFocusDataModule`
  contacts Zenodo. Both default to `download=False`.

Before any future hosted prediction call, state the exact destination, pixel
channels/regions, metadata, identifiers, retention, legal basis, and safeguards;
obtain explicit consent; and never send PHI by default. Prefer reviewed,
checksummed local model artifacts and local inference.

## Model-code security

- PyTorch `model.eval()` means **evaluation mode** for modules; it is not Python's
  dangerous built-in evaluator. Never use Python dynamic evaluation or execution.
- Do not name local files `pathml.py`, `torch.py`, `onnx.py`, or after standard
  libraries; shadow modules can silently change imports.
- PathML's `EntityDataset` loads `.pt` objects with `weights_only=False`. Never
  open an untrusted graph/checkpoint. Treat pickle-based pipelines and `.pt` files
  as executable code.
- ONNX is safer than pickle but not inherently trusted. Verify source, SHA-256,
  expected input/output schema, file size, and runtime limits; use isolation for
  third-party models.

## Bundled local CLIs

All helpers reject URLs and symlinks, cap inputs/work, use strict JSON, avoid
network access, and require no PathML import for `--help`:

```bash
python scripts/slide_manifest.py validate --manifest manifest.csv --root .
python scripts/slide_manifest.py inspect --slide data/example.svs --root .
python scripts/plan_pipeline.py --width 100000 --height 80000 --tile-size 512 --stride 512
python scripts/image_qc.py synthetic --width 256 --height 256
python scripts/validate_spatial_schema.py graph --input graph.json --root .
python scripts/validate_spatial_schema.py multiplex --input cells.csv --root .
python scripts/plan_inference.py --tile-count 4000 --batch-size 16 --height 256 --width 256
```

The inference planner reads numbers or a bounded JSON model card only; it never
imports a model framework or opens a checkpoint.

## Detailed references

- `references/image_loading.md` — slide classes, backends, formats, levels,
  coordinates, technical metadata, and privacy.
- `references/preprocessing.md` — stable transforms, masks/QC, stain processing,
  pipeline execution, and leakage prevention.
- `references/data_management.md` — `.h5path`, manifests, datasets, provenance,
  splits, and safe downloads.
- `references/multiparametric.md` — multidimensional layout, CODEX/Vectra,
  quantification, AnnData, DeepCell/Mesmer, and network disclosure.
- `references/graphs.md` — instance maps, feature alignment, KNN/RAG/HACT graphs,
  spatial units, schemas, and validation.
- `references/machine_learning.md` — HoVer-Net/HACTNet, local ONNX inference,
  batching, checkpoint trust, evaluation, and model provenance.

## Primary sources

All checked 2026-07-23:

- PyPI metadata: https://pypi.org/project/pathml/3.0.5/
- Stable source tag: https://github.com/Dana-Farber-AIOS/pathml/tree/v3.0.5
- Releases: https://github.com/Dana-Farber-AIOS/pathml/releases
- Stable documentation: https://pathml.readthedocs.io/en/stable/
- Rosenthal et al. (2022), PathML toolkit:
  https://doi.org/10.1158/1541-7786.MCR-21-0665
- Omar et al. (2025), multiplex workflows:
  https://doi.org/10.1016/j.labinv.2025.104220

## Agent operating procedure

1. **Check the environment.** Confirm data access permissions, de-identification status and the governing regulations or protocols.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Work on a de-identified sample or synthetic data first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check outputs against clinical guidelines and reporting standards; have a qualified human review clinical content.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Data appears to contain identifiable patient information | Stop and ask the user before processing further. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Outputs are decision support for qualified professionals, not medical advice; never present them as diagnoses or orders.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `histolab`: Extracts tiles and preprocesses H&E whole slide images with the histolab Python library (OpenSlide), covering slide inspection, tissue mask…
- `clinical-decision-support`: Prepare and validate research-only clinical decision-support evaluation, evidence-profile, cohort, survival, biomarker/model, privacy, and…
- `ray-data`: Scalable data processing for ML workloads.
