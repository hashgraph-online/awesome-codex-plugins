# Command-line interface (`gtars-cli==0.9.0`)

Verified from the published crate and `v0.9.0` tagged source on **2026-07-23**.
The package is `gtars-cli`; the installed binary is `gtars`.

## Trust, installation, and features

Cargo installation compiles native code and may run transitive build scripts.
Review the official crate/source, lock resolution, license, and build environment
before:

```bash
cargo install gtars-cli --version 0.9.0 --locked
gtars --version
gtars --help
```

The v0.9.0 GitHub release also publishes platform archives plus `.sha256`
sidecars. Verify the archive checksum before extraction and do not execute an
untrusted binary. The bundled `artifact_inspector.py` hashes/classifies an
artifact without extracting or executing it.

Default CLI features are:

```text
scoring uniwig bbcache igd fragsplit overlaprs genomicdist refget
```

To build a reduced binary:

```bash
cargo install gtars-cli --version 0.9.0 --locked \
  --no-default-features --features "overlaprs,genomicdist"
```

Feature availability controls subcommand availability. There is no 0.9.0 CLI
`tokenizers` feature/subcommand. Do not copy an old `--all-features` binary's
command assumptions into a reduced binary.

## Global behavior

```bash
gtars --help
gtars --version
gtars <command> --help
```

Tagged source defines no global `--threads`, `--memory-limit`, `--buffer-size`,
`--verbose`, `--quiet`, `--strict`, `--continue-on-error`, or `--log-file`
options. Concurrency is command-specific.

Before every real command, run the exact installed `--help`. This reference is
pinned to 0.9.0; unversioned web documentation can drift.

## `overlaprs`

```bash
gtars overlaprs \
  --query query.bed \
  --universe universe.bed \
  --backend bits
```

Options:

- `-q/--query PATH` (required);
- `-u/--universe PATH` (required);
- `-e/--backend bits|ailist` (handler default: `bits`);
- `--streaming` is parsed but ignored by the v0.9.0 handler.

Output is BED3 universe-hit coordinates to stdout, one row per overlap. It is not
a count table and does not retain query IDs. See `overlap.md`.

## `igd`

Create from a **folder** of BED files:

```bash
gtars igd create \
  --filelist approved-bed-directory \
  --output index-directory \
  --dbname reference_index
```

Search with a BED/BED.GZ query:

```bash
gtars igd search \
  --database index-directory \
  --query query.bed
```

Current subcommands are `create` and `search`, not `build`, `query`, or `count`.
The `--filelist` help text calls the input a path to a list but specifies a
folder; validate installed behavior on a synthetic directory before scaling.

## `uniwig`

Batch BigWig:

```bash
gtars uniwig \
  --file sorted.bed.gz \
  --filetype bed \
  --chromref assembly.chrom.sizes \
  --smoothsize 5 \
  --stepsize 1 \
  --fileheader output/sample_ \
  --outputtype bw \
  --counttype core \
  --threads 4
```

BAM QC:

```bash
gtars uniwig bamqc \
  --input aligned.bam \
  --output bamqc.tsv \
  --threads 1
```

BED streaming adds `--streaming` and supports only WIG/bedGraph output. Read
`coverage.md` for all flags, sorting/bounds, BAM behavior, and resource limits.

## `consensus`

```bash
gtars consensus \
  --beds a.bed b.bed c.bed \
  --min-count 2 \
  --output consensus.bed
```

- `--beds` requires at least two paths;
- `--min-count` defaults to 1;
- output defaults to stdout and is BED4 (`chr start end count`).

Consensus counts input sets overlapping a reduced union component; it is not
per-base support segmentation. See `overlap.md`.

## `ranges`

`ranges` exposes interval algebra:

```text
gtars ranges reduce      --input BED [--output OUT]
gtars ranges trim        --input BED --chrom-sizes SIZES [--output OUT]
gtars ranges promoters   --input BED [--upstream 2000] [--downstream 200] [--output OUT]
gtars ranges setdiff     -a BED_A -b BED_B [--output OUT]
gtars ranges pintersect  -a BED_A -b BED_B [--output OUT]
gtars ranges concat      -a BED_A -b BED_B [--output OUT]
gtars ranges union       -a BED_A -b BED_B [--output OUT]
gtars ranges jaccard     -a BED_A -b BED_B
gtars ranges shift       --input BED --offset N [--output OUT]
gtars ranges flank       --input BED --width N [--start|--both] [--output OUT]
gtars ranges resize      --input BED --width N [--fix start|end|center] [--output OUT]
gtars ranges narrow      --input BED [--start N] [--end N] [--width N] [--output OUT]
gtars ranges disjoin     --input BED [--output OUT]
gtars ranges gaps        --input BED --chrom-sizes SIZES [--output OUT]
gtars ranges intersect   -a BED_A -b BED_B [--output OUT]
```

Operations without `--output` write to stdout. `promoters` is anchored on region
starts in core behavior; do not assume strand-aware TSS handling.

## `fscoring` fragment counts

File-by-peak matrix:

```bash
gtars fscoring "fragments/sample01.fragments.tsv.gz" consensus.bed \
  --mode atac \
  --output counts.csv.gz
```

Arguments are positional:

```text
gtars fscoring <fragments> <consensus> [--mode atac|chip] [--output PATH]
```

- `fragments` is interpreted by `FragmentFileGlob`; a single explicit local file
  is safest. Shell globs can expose unintended files, while quoted globs are
  expanded by the library.
- default mode is `atac`;
- default output is `fscoring.csv.gz`;
- `atac` uses cut-site scoring semantics; `chip` uses fragment overlap semantics.

Sparse barcode mode:

```bash
gtars fscoring sample.fragments.tsv.gz consensus.bed \
  --barcode \
  --output output/sample01
```

This writes:

```text
output/sample01_matrix.mtx.gz
output/sample01_barcodes.tsv.gz
output/sample01_features.tsv.gz
```

The fragment file must carry valid coordinates and barcodes. Do not expose raw
barcodes in logs or reports; cap cells, peaks, nonzeros, memory, and output.

## `pb` pseudobulk splitting

The current command name is `pb`, not `fragsplit`:

```bash
gtars pb sample.fragments.tsv.gz barcode_to_cluster.tsv \
  --output pseudobulk-output
```

Positional arguments are fragments then mapping; default output is `out/`.
This writes cluster-specific files. Validate mapping uniqueness, unknown
barcodes, safe cluster names, output collisions, file-count bounds, and patient
split policy first.

## `genomicdist`

Minimal call:

```bash
gtars genomicdist \
  --bed regions.bed \
  --chrom-sizes assembly.chrom.sizes \
  --bins 250 \
  --output distribution.json
```

Optional inputs/features:

- `--gtf GTF` for partitions and derived TSS distances;
- `--tss BED` to override GTF-derived TSS;
- `--signal-matrix TSV`;
- `--fasta FASTA|FAB` for GC content;
- `--dinucl-freq` and `--dinucl-raw-counts`;
- `--ignore-unk-chroms`;
- `--promoter-upstream`, `--promoter-downstream`;
- `--compact`.

Supplying chromosome sizes makes region-distribution bins comparable across
files and enables bounds-related operations. Omitting them derives scale from
observed ends and is unsuitable for cross-file comparison.

## `prep`

```text
gtars prep --gtf genes.gtf.gz [--output genes.gda]
gtars prep --signal-matrix matrix.tsv.gz [--output matrix.bin]
gtars prep --fasta reference.fa [--output reference.fab]
```

`prep` serializes local inputs into Gtars-specific binary formats. Treat these
artifacts as versioned native data: hash inputs/outputs, record 0.9.0, reject
untrusted serialized files, and bound expansion/memory.

## `refget`

```bash
gtars refget build reference.fa reference-alt.fa.gz \
  --output refget-store \
  --jobs 1
```

Other options are `--file-list/-f`, `--raw`, and `--force`; `--jobs 0` means
automatic concurrency. There are no current CLI `digest`, `verify`, or remote
query subcommands. See `refget.md`.

## `bbcache`

```text
gtars bbcache cache-bed       --identifier VALUE [--cache-folder DIR]
gtars bbcache cache-bedset    --identifier VALUE [--cache-folder DIR]
gtars bbcache seek            --identifier VALUE [--cache-folder DIR]
gtars bbcache inspect-bedfiles                 [--cache-folder DIR]
gtars bbcache inspect-bedsets                  [--cache-folder DIR]
gtars bbcache rm              --identifier VALUE [--cache-folder DIR]
```

Client construction creates cache directories. Cache/download calls can contact
BEDbase or arbitrary URL hosts and write SQLite/cache files. `rm` deletes local
content. The tagged source has a likely ID-only download mismatch described in
`refget.md`; do not guess a workaround.

## Threading and resource controls

There is no global thread flag:

- batch uniwig `--threads/-p` defaults to 6;
- `uniwig bamqc --threads/-t` defaults to 1; values above 1 need a BAM index;
- `refget build --jobs/-j` defaults to 0 (auto);
- other commands expose no documented thread setting.

Set command-specific values explicitly. Also bound input bytes/records/files,
glob matches, hit pairs/nonzeros, stdout, memory, temporary disk, cache, and
wall time externally.

## Safe dry-run planning

```bash
python3 -B scripts/execution_plan.py --help
python3 -B scripts/coverage_preflight.py --help
```

These helpers produce fixed argv templates only. They do not invoke `gtars`,
expand globs, download data, create caches, or write outputs.

## Removed stale command forms

Do not use:

```text
gtars igd build/query/count
gtars overlaprs overlap/count/filter/subtract
gtars uniwig generate
gtars scoring score/batch
gtars fragsplit split/cluster-split/filter
gtars refget digest/verify
gtars --threads/--memory-limit/--verbose
```

## Official sources (accessed 2026-07-23)

- [gtars-cli 0.9.0 crate](https://crates.io/crates/gtars-cli)
- [Gtars v0.9.0 release](https://github.com/databio/gtars/releases/tag/v0.9.0)
- [CLI main parser at v0.9.0](https://github.com/databio/gtars/blob/v0.9.0/gtars-cli/src/main.rs)
- [CLI feature manifest at v0.9.0](https://github.com/databio/gtars/blob/v0.9.0/gtars-cli/Cargo.toml)
- [Official CLI guide](https://docs.bedbase.org/gtars/cli/)
- [Official versioning policy](https://docs.bedbase.org/gtars/versioning/)
