# Family Selection

Use this file when the user asks for a segmentation model but has not chosen a backbone.

## SegmentNT

Choose `SegmentNT` when the user wants:

- segmentation with the Nucleotide Transformer backbone
- inference on sequences around 30 kb, with possible extension to 50 kb
- `segment_nt` or `segment_nt_multi_species`
- awareness that `segment_nt_multi_species` is a checkpoint family choice, not a runtime species-conditioning token
- explicit control of `rescaling_factor` for long-sequence extrapolation
- feature names read from `config.features`

## SegmentEnformer

Choose `SegmentEnformer` when the user wants:

- Enformer-based segmentation
- the documented inference shape based on `196_608` bp inputs
- `hk.transform_with_state(...)` inference with explicit state handling

## SegmentBorzoi

Choose `SegmentBorzoi` when the user wants:

- Borzoi-based segmentation
- the documented inference shape based on `524_288` bp inputs
- `hk.transform_with_state(...)` inference with explicit state handling

## Feature scope

The docs describe segmentation at single-nucleotide resolution across gene and regulatory elements, including:

- protein-coding genes
- lncRNAs
- UTRs
- exons and introns
- splice sites
- polyA signal
- promoters
- enhancers
- CTCF-bound sites

## Quick routing guidance

- If the user starts from NT checkpoints and asks about 30-50 kb behavior, default to SegmentNT.
- If the user asks for Enformer/Borzoi parity with segmentation heads, choose the matching family directly.
- If user constraints are unclear, ask for target input length and preferred backbone, then pick one family and proceed.
