# Variant and Interpretation

Use this file when the user asks for Borzoi variant effects or sequence attributions.

## Variant scoring (`latest/score_variants`)

Command entry points:

```bash
conda activate borzoi_py310
cd ~/borzoi/tutorials/latest/score_variants
./score_expr_sed.sh
./score_expr_sad.sh
./score_polya.sh
./score_splice.sh
```

Notebook runner:

```bash
jupyter notebook run_variant_scripts.ipynb
```

Score semantics:

- `score_expr_sed.sh`: gene-specific expression (`logSED`, exon-intersected `logD2`)
- `score_expr_sad.sh`: gene-agnostic expression (`logD2` over full track)
- `score_polya.sh`: gene-specific polyadenylation (`COVR`)
- `score_splice.sh`: gene-specific splicing (`nDi`)

Latest tutorial note:

- Uses Mini Borzoi from tutorial training flow and is weaker than published pretrained Borzoi.
- For fast-tier real inference outside tutorial reproduction, prefer `mini/human_gtex` for generic human RNA tasks; use `k562_*` only when K562 is explicitly requested.

Legacy tutorial difference:

- Uses published pretrained Borzoi and includes old-transform activation flag (`-u`) in script flows.

## Coordinate and variant conventions

Use explicit coordinate conventions in answers and outputs:

- VCF SNP position is 1-based.
- Python sequence indexing into fetched windows is 0-based.
- Record both input sequence window and model output window (post-cropping) when reporting track positions.

When users provide rule-based edits (for example, "mutate to G, if ref is G mutate to T"), resolve reference base first and then derive ALT deterministically.

## Fast-tier output contract for single-site prediction

For direct real prediction tasks, recommend writing:

- `trackplot` figure (`.png`)
- variant effect table (`.tsv`)
- raw prediction arrays (`.npz` or `.h5`)
- run metadata (`.json`) including model name, assembly, window coordinates, and resolved REF/ALT

See `references/real-inference-fastpath.md` for a concrete lightweight execution pattern.

## Sequence interpretation gradients

Latest path:

```bash
conda activate borzoi_py310
cd ~/borzoi/tutorials/latest/interpret_sequence
./run_gradients_expr_HBE1.sh
```

Legacy examples:

- `run_gradients_expr_CFHR2.sh`
- `run_gradients_polya_CD99.sh`
- `run_gradients_splice_GCFC2.sh`

Grounded caveats:

- Track transform parameters are often set by script flags (`--track_scale`, `--track_transform`, `--clip_soft`) and can override target-file assumptions.
- Legacy splicing gradient example may choose one exon randomly in current script behavior.

## Routing guidance

- For full paper-grade benchmark replication at scale, point users to `borzoi-paper`.
- For SegmentBorzoi nucleotide-resolution segmentation APIs in the Nucleotide Transformer ecosystem, use `segment-nt` instead of this skill.
