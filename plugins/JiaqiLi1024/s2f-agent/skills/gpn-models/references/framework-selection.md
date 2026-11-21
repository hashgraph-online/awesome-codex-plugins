# Framework Selection

Use this file first when the request says "GPN" but does not specify which model family.

## Family summary

| Family | Inference requirement | Best fit |
| --- | --- | --- |
| `GPN` | Unaligned genomes | Single-sequence genomic language modeling |
| `GPN-MSA` | Aligned genomes | Alignment-based inference, but deprecated in favor of `GPN-Star` |
| `PhyloGPN` | No alignment required at inference | Phylogenetic transfer learning and zero-shot deleteriousness prediction |
| `GPN-Star` | Aligned genomes | Newer phylogeny-aware alignment model |

## Use these rules

- Choose `GPN` when the user has raw genome sequence and no whole-genome alignment at inference time.
- Choose `GPN-MSA` only when the user explicitly needs the multispecies alignment model and has aligned genomes available for inference.
- Prefer `GPN-Star` over `GPN-MSA` for new alignment-based workflows unless the user specifically asks for `GPN-MSA`.
- Choose `PhyloGPN` when the user wants a model trained with phylogenetic structure but used without alignment at inference or fine-tuning time.

## Grounded starter checkpoints

- `songlab/gpn-brassicales`
- `songlab/gpn-animal-promoter`
- `songlab/gpn-msa-sapiens`
- `songlab/PhyloGPN`
- `songlab/gpn-star-hg38-p243-200m`
- `songlab/gpn-star-hg38-v100-200m`
- `songlab/gpn-star-hg38-m447-200m`
- `songlab/gpn-star-mm39-v35-85m`
- `songlab/gpn-star-galGal6-v77-85m`
- `songlab/gpn-star-dm6-i124-85m`
- `songlab/gpn-star-ce11-n135-25m`
- `songlab/gpn-star-tair10-b18-25m`

Use only checkpoints named in the README unless you verify others independently.
