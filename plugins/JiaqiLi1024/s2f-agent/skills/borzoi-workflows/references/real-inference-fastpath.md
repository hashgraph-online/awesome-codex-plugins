# Real Inference Fastpath

Use this reference when users ask for real Borzoi prediction output but local runtime/network constraints make full published-model setup impractical.

## When to choose fastpath

Choose fastpath when:

- user needs real track/variant outputs, not tutorial-only explanation
- published model + full hg38 download is too heavy for current machine/session
- a mini-model approximation is acceptable with clear labeling

Do not present fastpath as paper-grade replication.

## Default model selection

For human (`hg38`) requests:

- default: `gs://seqnn-share/borzoi/mini/human_gtex/`
- alternative: `gs://seqnn-share/borzoi/mini/human_all/` (broader modalities)
- K562-specific: `gs://seqnn-share/borzoi/mini/k562_*` only when explicitly requested

Fetch one replicate (for example `f0/model0_best.h5`) plus matching `params.json` and `hg38/targets.txt`.

## Minimal asset fetch pattern

```bash
mkdir -p output/borzoi_fast/model output/borzoi_fast/hg38
curl -L --fail https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/f0/model0_best.h5 -o output/borzoi_fast/model/model0_best.h5
curl -L --fail https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/params.json -o output/borzoi_fast/params.json
curl -L --fail https://storage.googleapis.com/seqnn-share/borzoi/mini/human_gtex/hg38/targets.txt -o output/borzoi_fast/hg38/targets.txt
```

Prefer resume-capable flags (`-C -` or `wget -c`) for unstable networks.

## Sequence retrieval strategy

For lightweight interval/single-site tasks, retrieve only required hg38 regions (for example via UCSC sequence API) instead of downloading whole-genome FASTA.

Always record:

- requested genomic interval
- model input window used
- post-crop output window and stride

## Variant handling checklist

1. Resolve reference base at requested locus first.
2. Apply user mutation rule deterministically.
3. Save resolved `REF`, `ALT`, and coordinate convention in metadata.

## Output contract

Write outputs under a dedicated folder (for example `output/borzoi/`):

- `*_trackplot.png`
- `*_variant.tsv`
- `*_tracks.npz`
- `run_metadata.json`

Metadata should include: model ID, species, assembly, sequence length, stride, input/output windows, and variant details.
