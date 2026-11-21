# Model Catalog

Use this file when the user asks which NTv3 checkpoint to use.

## Main production checkpoints

Pre-trained:

- `NTv3_8M_pre` (`InstaDeepAI/NTv3_8M_pre`)
- `NTv3_100M_pre` (`InstaDeepAI/NTv3_100M_pre`)
- `NTv3_650M_pre` (`InstaDeepAI/NTv3_650M_pre`)

Post-trained:

- `NTv3_100M_post` (`InstaDeepAI/NTv3_100M_post`)
- `NTv3_650M_post` (`InstaDeepAI/NTv3_650M_post`)

## Intermediate and ablation checkpoints

Use these only when the user explicitly asks for intermediate/ablation variants:

- `NTv3_8M_pre_8kb` (`InstaDeepAI/NTv3_8M_pre_8kb`)
- `NTv3_100M_pre_8kb` (`InstaDeepAI/NTv3_100M_pre_8kb`)
- `NTv3_100M_post_131kb` (`InstaDeepAI/NTv3_100M_post_131kb`)
- `NTv3_650M_pre_8kb` (`InstaDeepAI/NTv3_650M_pre_8kb`)
- `NTv3_650M_post_131kb` (`InstaDeepAI/NTv3_650M_post_131kb`)
- `NTv3_5downsample_pre_8kb` (`InstaDeepAI/NTv3_5downsample_pre_8kb`)
- `NTv3_5downsample_pre` (`InstaDeepAI/NTv3_5downsample_pre`)
- `NTv3_5downsample_post_131kb` (`InstaDeepAI/NTv3_5downsample_post_131kb`)
- `NTv3_5downsample_post` (`InstaDeepAI/NTv3_5downsample_post`)

## Selection guidance

- Choose pre-trained models for MLM outputs and embeddings.
- Choose post-trained models for species-conditioned functional tracks and genome annotations.
- Prefer the main production checkpoints unless the user needs a specific context or downsampling regime.
- For quick smoke tests or limited VRAM, start with `NTv3_8M_pre` (pre) or `NTv3_100M_post` (post).
- If the user asks for exact reproducibility with a staged experiment, use the specific `_8kb` or `_131kb` checkpoint they name.
