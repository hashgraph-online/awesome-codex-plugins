# I/O, tokenization, caches, evaluation, and security

Research snapshot: 2026-07-23. API claims below use official documentation,
PyPI metadata, and the `geniml` v0.8.4 release source. Where current docs and
release code disagree, the discrepancy is stated explicitly.

## Release and dependency facts

`geniml==0.8.4` was released on 2026-01-14. PyPI metadata:

- does not set `Requires-Python`;
- classifies Python 3.10, 3.11, 3.12, 3.13, and 3.14;
- provides `ml` and `test` extras;
- ships a pure-Python wheel, but dependencies include native packages;
- uses Trusted Publishing with a Sigstore provenance link to tag `v0.8.4`.

Release files:

```text
geniml-0.8.4-py3-none-any.whl
sha256 ac0fc520cde6f6461120aee6b40d3cbf20e1e3d8bdb95a3a45345724eee545b5

geniml-0.8.4.tar.gz
sha256 6f429c7c89d06a4c2c378e349d14b3a2d984dc441440ada38473772fce6addb1
```

The stable release requires `gtars>=0.2.5` without an upper bound. The
2026-07-23 verified base smoke resolved `gtars==0.9.2` and successfully
imported Geniml 0.8.4, `geniml.io.RegionSet`, and
`gtars.tokenizers.Tokenizer`. Gtars 0.9.2 was released 2026-06-17 and requires
Python >=3.10.

Pin both direct packages and retain an `uv.lock`; upstream transitive
requirements are mostly lower bounds.

## BED coordinates and validation

BED is normally 0-based, half-open `[start, end)`. A valid BED3 row requires:

- nonempty contig;
- integer `start >= 0`;
- integer `end > start`;
- `end` no greater than the declared contig length;
- values within bounded integer limits.

Do not confuse BED with 1-based closed VCF/GFF coordinates. BED columns beyond
BED3 have their own constraints; preserve them rather than guessing.
BED3 carries no strand. When BED6 strand exists, preserve `+`, `-`, or `.`
unless a documented assay conversion says otherwise.

Assembly compatibility requires more than matching `chr` prefixes. BEDbase
describes chromosome-name sensitivity (XS), out-of-bounds regions (OOBR), and
sequence fit (SF) as separate criteria. Record a concrete assembly/accession
and chromosome-sizes digest. Reject unknown alt/decoy contigs rather than
dropping them silently.

Run:

```bash
python skills/geniml/scripts/bed_validator.py \
  --input data/peaks.bed \
  --assembly GRCh38 \
  --chrom-sizes refs/GRCh38.chrom.sizes
```

The script emits aggregate errors and a normalization plan. It never rewrites
coordinates or performs liftover.

## Region and RegionSet APIs

### Gtars API for new workflows

```python
from gtars.models import Region, RegionSet

region = Region("chr1", 100, 200, None)
regions = RegionSet("data/peaks.bed")
print(len(regions))
regions.to_bed("work/peaks.copy.bed")
```

Gtars 0.9.2 exposes operations including `sort`, `reduce`, `coverage`,
`count_overlaps`, `jaccard`, `nearest_neighbors`, `to_bed`, `to_bed_gz`, and
`to_bigbed`. Do not assume these operations validate assembly or coordinate
semantics. Validate before constructing the object and after writing output.

Official Gtars constructors can accept URLs. This skill restricts them to
validated local regular files by default.

### Legacy Geniml I/O

```python
from geniml.io import BedSet, Region, RegionSet

region = Region("chr1", 100, 200)  # third field is named stop
regions = RegionSet("data/peaks.bed", backed=False)
```

`geniml.io.RegionSet(regions, backed=False)` accepts a path/URL or a list of
legacy Regions. With `backed=True`, it streams the BED, supports iteration and
length, and does not support indexing. Other release classes include `BedSet`,
`Maf`, `SNP`, `TokenizedRegionSet`, and `RegionSetCollection`, though only
`Region`, `RegionSet`, and `BedSet` are exported from `geniml.io`.

The 0.7.0 changelog says RegionSet use switched toward Gtars. Avoid mixing
legacy and Gtars Region objects accidentally: field names and accepted types
differ.

## Tokenization

### Current Gtars tokenizer

```python
from gtars.models import RegionSet
from gtars.tokenizers import Tokenizer

tokenizer = Tokenizer.from_bed("refs/universe.bed")
encoded = tokenizer(RegionSet("data/peaks.bed"))
input_ids = encoded["input_ids"]
```

Gtars also documents `Tokenizer.from_config` and
`Tokenizer.from_pretrained`. The latter can access Hugging Face; do not call it
without explicit network approval, revision pinning, cache bounds, and
expected hashes.

With Gtars 0.9.2, a two-region universe produced `len(tokenizer) == 9` because
seven special tokens are included. Preserve:

- universe bytes, row order, and assembly;
- Gtars version;
- `special_tokens_map` and every special-token ID;
- tokenizer length;
- token-corpus schema and checksum.

Run the local compatibility planner:

```bash
python skills/geniml/scripts/tokenizer_compatibility.py \
  --model-dir models/region2vec \
  --universe refs/universe.bed \
  --assembly GRCh38
```

### Legacy hard tokenization

The stable file `geniml.tokenization.main` defines:

```python
hard_tokenization_main(
    src_folder,
    dst_folder,
    universe_file,
    fraction=1e-9,
    file_list=None,
    num_workers=10,
    bedtools_path="bedtools",
)
```

It invokes an external Bedtools executable and multiprocessing. The
`fraction` is passed to interval intersection logic; it is **not a statistical
p-value**. The package `geniml.tokenization.__init__` comments out its public
exports, so `from geniml.tokenization import hard_tokenization` and the
installed `geniml tokenize` dispatcher are unreliable in 0.8.4.

Do not use an arbitrary `bedtools` found on `PATH`. If reproducing the legacy
path, pin and checksum the binary, pass an explicit absolute path, validate
argv, bound workers, use a fresh output directory, and compare synthetic
results with the Gtars tokenizer.

The current preferred token corpus is a bounded Parquet file with one
list-valued `tokens` column. Upstream issue #14 proposes deprecating one
`.gtok` file per cell.

## BBClient and cache behavior

```python
from geniml.bbclient import BBClient

client = BBClient(cache_folder="/absolute/project/.bbcache")
```

Release defaults:

- endpoint: `BEDBASE_API` or `https://api.bedbase.org`;
- cache root: `BBCLIENT_CACHE` or `~/.bbcache`;
- BEDs under `bedfiles/`;
- BED sets under `bedsets/`;
- token cache in `tokens.zarr`.

`load_bed`, `load_bedset`, `add_bed_tokens_to_cache`, and corresponding
`cache-*` CLI commands may use the network. `add_bed_to_s3` and
`get_bed_from_s3` accept cloud credentials and endpoints; do not use them
without an explicit upload/download request and a separate credential review.
Never read or print the environment broadly. Only consult `BEDBASE_API` and
`BBCLIENT_CACHE` when the user approves those overrides.

Local-oriented CLI:

```text
geniml bbclient seek ID --cache-folder CACHE
geniml bbclient inspect-bedfiles --cache-folder CACHE
geniml bbclient inspect-bedsets --cache-folder CACHE
geniml bbclient rm ID --cache-folder CACHE
```

`rm` mutates cache state; confirm the exact resolved target first. Inspection
can still expose BED IDs and local paths, so redact output in shared logs.

Before an approved download:

1. approve endpoint and exact IDs;
2. set a project-scoped cache and byte quota;
3. reject redirects to unapproved hosts where tooling permits;
4. verify compressed and expanded size;
5. checksum downloaded bytes;
6. validate BED and assembly;
7. record provenance and retrieval time.

No bundled skill script performs BBClient or Hub downloads.

## Model loading and artifact safety

Modern local classes:

```python
from geniml.region2vec.main import Region2VecExModel
from geniml.scembed.main import ScEmbed

r2v = Region2VecExModel.from_pretrained("models/region2vec")
sce = ScEmbed.from_pretrained("models/scembed")
```

These classmethods use local bundle paths. Constructors with
`model_path="organization/model"` call Hugging Face Hub and download
`checkpoint.pt`, `universe.bed`, and `config.yaml`.

Geniml's loader uses `torch.load(..., weights_only=True)` and YAML
`safe_load`. This is safer than unrestricted pickle, but artifacts can still
cause resource exhaustion or exploit parser/native-library vulnerabilities.
Gensim `.model`, pickle, joblib, TorchScript, shared libraries, and external
binaries require even stronger distrust.

Inspect without importing Torch or deserializing:

```bash
python skills/geniml/scripts/model_artifact_inspector.py \
  --model-dir models/region2vec \
  --verify-manifest models/region2vec/SHA256SUMS
```

The inspector reads bounded metadata formats, hashes bytes, flags risky
extensions, rejects URLs/symlinks/traversal, and never loads model objects.

## Embedding evaluation

The `geniml eval` release CLI has:

```text
gdst     Genome distance scaling test
npt      Neighborhood preserving test
ctt      Cluster tendency test
rct      Reconstruction test
bin-gen  Generate binary embeddings
```

Examples:

```bash
geniml eval gdst \
  --model-path /absolute/project/model \
  --embed-type region2vec \
  --num-samples 10000 \
  --seed 42

geniml eval npt \
  --model-path /absolute/project/model \
  --embed-type region2vec \
  --K 10 \
  --num-samples 1000 \
  --seed 42 \
  --num-workers 4
```

The official tutorial's `BaseEmbeddings` and `bin-gen` workflows use pickle
for binary embedding objects. Generate them locally and never load an
untrusted pickle. Bound samples/workers and record random seeds. Evaluate on
patients/donors excluded from universe selection and training.

Primary source: Zheng et al. (2024), *Methods for evaluating unsupervised
vector representations of genomic regions*,
doi:[10.1093/nargab/lqae086](https://doi.org/10.1093/nargab/lqae086).

## BEDshift

The integrated Bedshift CLI is:

```text
geniml bedshift --help
```

It can use a local chromosome-length file or resolve a Refgenie genome through
`refgenconf`. Prefer an explicit, checksummed local chromosome-sizes file to
avoid implicit lookup/network behavior. Set a seed, output bound, and
perturbation policy matching the null hypothesis. Validate randomized
coordinates exactly like originals.

Primary source: Gu et al. (2021), *Bedshift: perturbation of genomic interval
sets*, doi:[10.1186/s13059-021-02440-w](https://doi.org/10.1186/s13059-021-02440-w).

## Privacy and bounded reporting

Potentially sensitive:

- BED coordinates and filenames;
- sample, donor, patient, treatment, diagnosis, and tissue metadata;
- cell barcodes and rare labels;
- embeddings that permit membership or nearest-neighbor inference;
- local cache paths and BEDbase identifiers.

Default reports should contain only aggregate counts, schema names, checksums,
software versions, and redacted file IDs. Cap error examples; never dump
entire malformed rows or metadata values. Store full provenance manifests in
the protected project, not chat output.

## Migration and deprecation ledger

- 0.4.0: tokenizers renamed to `TreeTokenizer` and `AnnDataTokenizer`.
- 0.7.0: RegionSet use moved toward Gtars and encoding changed.
- 0.8.0: Atacformer added.
- 0.8.1: BEDspace fixed according to the changelog.
- 0.8.4: latest stable; release notes contain only the version bump.
- Current Gtars API: use the unified `gtars.tokenizers.Tokenizer`.
- `.gtok`: proposed for deprecation in upstream issue #14; prefer Parquet.
- `embedding_size`: backward-compatible config key; use `embedding_dim`.
- Top-level Region2Vec/scEmbed/tokenization exports shown by old docs are
  absent/commented in the 0.8.4 wheel.
- Official `geniml assess` examples are stale; use
  `geniml assess-universe`.

## Dated authoritative sources

Package and source:

- [PyPI: geniml 0.8.4](https://pypi.org/project/geniml/0.8.4/) — released
  2026-01-14; accessed 2026-07-23.
- [PyPI JSON: geniml 0.8.4](https://pypi.org/pypi/geniml/0.8.4/json) —
  artifact hashes, dependencies, extras, and null `Requires-Python`; accessed
  2026-07-23.
- [GitHub release v0.8.4](https://github.com/databio/geniml/releases/tag/v0.8.4)
  — commit `5e8dd14126c45d14917df74de4fb405f383afb61`; released
  2026-01-14; accessed 2026-07-23.
- [Geniml changelog](https://docs.bedbase.org/geniml/changelog/) — through
  0.8.1 on the rendered page; accessed 2026-07-23.
- [PyPI: gtars 0.9.2](https://pypi.org/project/gtars/0.9.2/) — released
  2026-06-17; accessed 2026-07-23.

Official API/ecosystem documentation:

- [Geniml documentation](https://docs.bedbase.org/geniml/) — accessed
  2026-07-23.
- [Geniml I/O API](https://docs.bedbase.org/geniml/api-reference/io/) —
  accessed 2026-07-23.
- [Gtars RegionSet](https://docs.bedbase.org/gtars/regionSet) — accessed
  2026-07-23.
- [Gtars tokenizers](https://docs.bedbase.org/gtars/tokenizers) — accessed
  2026-07-23.
- [BEDbase reference-genome compatibility](https://docs.bedbase.org/bedbase/user/reference-genome-compatibility/)
  — accessed 2026-07-23.
- [BEDbase BBClient and caching](https://docs.bedbase.org/bedbase/user/bbclient/)
  — accessed 2026-07-23.
- [Geniml evaluation tutorial](https://docs.bedbase.org/geniml/tutorials/evaluation/)
  — accessed 2026-07-23.
- [Official citation map](https://docs.bedbase.org/citations) — accessed
  2026-07-23.

Primary papers:

- [Gharavi et al. 2021, Region2Vec](https://doi.org/10.1093/bioinformatics/btab439)
- [Gu et al. 2021, BEDshift](https://doi.org/10.1186/s13059-021-02440-w)
- [Gharavi et al. 2024, BEDspace](https://doi.org/10.3390/bioengineering11030263)
- [LeRoy et al. 2024, scEmbed](https://doi.org/10.1093/nargab/lqae073)
- [Rymuza et al. 2024, consensus universes](https://doi.org/10.1093/nar/gkae685)
- [Zheng et al. 2024, embedding evaluation](https://doi.org/10.1093/nargab/lqae086)
