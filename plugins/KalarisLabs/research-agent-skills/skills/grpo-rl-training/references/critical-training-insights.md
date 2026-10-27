# Critical Training Insights

### 1. Loss Behavior (EXPECTED PATTERN)
- **Loss starts near 0 and INCREASES during training**
- This is CORRECT - loss measures KL divergence from initial policy
- Model is learning (diverging from original behavior to optimize rewards)
- Monitor reward metrics instead of loss for progress

### 2. Reward Tracking
Key metrics to watch:
- `reward`: Average across all completions
- `reward_std`: Diversity within groups (should remain > 0)
- `kl`: KL divergence from reference (should grow moderately)

**Healthy Training Pattern:**
```
Step   Reward    Reward_Std   KL
100    0.5       0.3          0.02
200    0.8       0.25         0.05
300    1.2       0.2          0.08  ← Good progression
400    1.5       0.15         0.12
```

**Warning Signs:**
- Reward std → 0 (model collapsing to single response)
- KL exploding (> 0.5) (diverging too much, reduce LR)
- Reward stuck (reward functions too harsh or model capacity issue)

### 3. Common Pitfalls and Solutions

| Problem | Symptom | Solution |
|---------|---------|----------|
| **Mode collapse** | All completions identical | Increase `num_generations`, add diversity penalty |
| **No learning** | Flat rewards | Check reward function logic, increase LR |
| **OOM errors** | GPU memory exceeded | Reduce `num_generations`, enable gradient checkpointing |
| **Slow training** | < 1 it/s | Enable `use_vllm=True`, use Unsloth, reduce seq length |
| **Format ignored** | Model doesn't follow structure | Increase format reward weight, add incremental rewards |

---
