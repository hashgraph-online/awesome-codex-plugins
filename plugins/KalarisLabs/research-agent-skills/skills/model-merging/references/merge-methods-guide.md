# Merge Methods Guide

### Linear Merge

**Best for**: Simple model combinations, equal weighting

```yaml
merge_method: linear
models:
  - model: WizardLM/WizardMath-7B-V1.1
    parameters:
      weight: 0.4
  - model: teknium/OpenHermes-2.5-Mistral-7B
    parameters:
      weight: 0.3
  - model: NousResearch/Nous-Hermes-2-Mistral-7B-DPO
    parameters:
      weight: 0.3
dtype: bfloat16
```

### SLERP Merge

**Best for**: Two models, smooth interpolation

```yaml
merge_method: slerp
slices:
  - sources:
      - model: mistralai/Mistral-7B-v0.1
        layer_range: [0, 32]
      - model: teknium/OpenHermes-2.5-Mistral-7B
        layer_range: [0, 32]
parameters:
  t: 0.5  # 0.0 = first model, 1.0 = second model
dtype: bfloat16
```

**Layer-specific SLERP:**

```yaml
merge_method: slerp
slices:
  - sources:
      - model: model_a
        layer_range: [0, 32]
      - model: model_b
        layer_range: [0, 32]
parameters:
  t:
    - filter: self_attn    # Attention layers
      value: 0.3
    - filter: mlp          # MLP layers
      value: 0.7
    - value: 0.5           # Default for other layers
dtype: bfloat16
```

### Task Arithmetic

**Best for**: Combining specialized skills

```yaml
merge_method: task_arithmetic
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: WizardLM/WizardMath-7B-V1.1  # Math
    parameters:
      weight: 0.5
  - model: teknium/OpenHermes-2.5-Mistral-7B  # Chat
    parameters:
      weight: 0.3
  - model: ajibawa-2023/Code-Mistral-7B  # Code
    parameters:
      weight: 0.2
dtype: bfloat16
```

### TIES-Merging

**Best for**: Many models, resolving conflicts

```yaml
merge_method: ties
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: WizardLM/WizardMath-7B-V1.1
    parameters:
      density: 0.5  # Keep top 50% of parameters
      weight: 1.0
  - model: teknium/OpenHermes-2.5-Mistral-7B
    parameters:
      density: 0.5
      weight: 1.0
  - model: NousResearch/Nous-Hermes-2-Mistral-7B-DPO
    parameters:
      density: 0.5
      weight: 1.0
parameters:
  normalize: true
dtype: bfloat16
```

### DARE Merge

**Best for**: Reducing redundancy

```yaml
merge_method: dare_ties
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: WizardLM/WizardMath-7B-V1.1
    parameters:
      density: 0.5    # Drop 50% of deltas
      weight: 0.6
  - model: teknium/OpenHermes-2.5-Mistral-7B
    parameters:
      density: 0.5
      weight: 0.4
parameters:
  int8_mask: true  # Use int8 for masks (saves memory)
dtype: bfloat16
```
