# Research Log

Chronological record of research decisions and actions. Append-only.

| # | Date | Type | Summary |
|---|------|------|---------|
| | | | |

<!-- Entry types:
  bootstrap    — initial scoping, literature search, hypothesis formation
  inner-loop   — experiment run and result
  outer-loop   — synthesis, reflection, direction decision
  pivot        — change in research direction
  report       — progress presentation generated
  conclude     — decision to finalize and write paper

Example entries:
| 1 | 2026-03-15 | bootstrap | Searched Semantic Scholar + arXiv for efficient transformer architectures. Found 8 relevant papers. Gap: no systematic comparison of GLU variants on small models. Formed 3 hypotheses. Baseline: NanoGPT 5-min run, val_loss=4.82. |
| 2 | 2026-03-15 | inner-loop | H1 run_001: swapped ReLU for SwiGLU in FFN. 5-min training run. val_loss=4.61 (baseline 4.82, delta -0.21). Kept. |
| 3 | 2026-03-15 | inner-loop | H1 run_002: increased FFN hidden dim from 4x to 5.3x to match SwiGLU param count. val_loss=4.58 (-0.03 vs run_001). Marginal — SwiGLU benefit mostly from gating, not extra params. |
| 4 | 2026-03-15 | inner-loop | H1 run_003: tried GEGLU instead of SwiGLU. val_loss=4.63. Slightly worse than SwiGLU. SwiGLU wins for this scale. |
| 5 | 2026-03-15 | inner-loop | H2 run_004: replaced learned positional embeddings with RoPE. val_loss=4.55 (-0.06 vs SwiGLU baseline). Promising — stacks with SwiGLU. |
| 6 | 2026-03-15 | inner-loop | H2 run_005: RoPE + SwiGLU combined. val_loss=4.41 (-0.41 vs original baseline). Best so far. |
| 7 | 2026-03-16 | outer-loop | Reviewed 5 runs. Pattern: gating mechanisms (SwiGLU) and rotary embeddings (RoPE) give independent gains that stack. Combined improvement ~9%. But WHY do they stack? Hypothesis: they operate on orthogonal aspects (FFN expressiveness vs positional encoding). Direction: DEEPEN — test if adding RMSNorm also stacks independently. |
| 8 | 2026-03-16 | inner-loop | H3 run_006: replaced LayerNorm with RMSNorm. val_loss=4.39 (-0.02). Small gain. Stacks but diminishing returns on normalization. |
| 9 | 2026-03-17 | outer-loop | 8 runs complete. Optimization plateau around val_loss=4.38. The easy architectural wins (SwiGLU, RoPE) are captured. Searched literature on training dynamics — found papers on warmup schedules at small scale. Direction: BROADEN — shift from architecture to training recipe. |
| 10 | 2026-03-17 | report | Generated progress-001.html with trajectory plot showing 9% improvement from architectural changes. |

Example entries (discovery-type research — understanding grokking):
| 1 | 2026-03-20 | bootstrap | Searched literature on grokking and delayed generalization. Found Nanda et al. progress measures, Grokfast spectral filtering. Gap: no connection to memory consolidation theory from neuroscience. 3 hypotheses formed. |
| 2 | 2026-03-20 | inner-loop | H1 run_001: trained modular addition transformer to memorization (100% train acc, 0% test). Steps to memorize: 1200. Baseline established. |
| 3 | 2026-03-20 | inner-loop | H1 run_002: continued training with standard weight decay. Grokking at step 48000. Measured progress measure throughout — sharp transition at step 44000. |
| 4 | 2026-03-20 | inner-loop | H1 run_003: inserted "sleep phase" at step 20000 (elevated weight decay + oscillatory LR for 500 steps). Grokking now at step 31000. 35% acceleration. |
| 5 | 2026-03-20 | inner-loop | H1 run_004: sleep phase at step 10000. Grokking at step 27000. Earlier sleep = earlier grokking. |
| 6 | 2026-03-20 | inner-loop | H1 run_005: sleep phase at step 5000 (before full memorization). Grokking at step 38000. Too early hurts — model hadn't memorized enough for consolidation to work. |
| 7 | 2026-03-21 | outer-loop | Reviewed 5 runs. Clear pattern: sleep phases accelerate grokking but only AFTER memorization is complete. This matches memory consolidation theory exactly — you need memories formed before consolidation can reorganize them. Searched for neural slow-wave sleep literature. The weight decay + oscillatory LR during sleep phases mimics synaptic downscaling. Direction: DEEPEN — sweep sleep timing relative to memorization completion. |
| 8 | 2026-03-21 | inner-loop | H1.1 run_006-010: swept sleep insertion at 80%, 100%, 120%, 150%, 200% of memorization step. Sweet spot at 110-120%. Consistent across 3 seeds. |
| 9 | 2026-03-22 | outer-loop | 10 runs complete. The story is clear: neural networks "dream to learn" just like brains — consolidation after encoding, not during. Grokfast achieves similar acceleration through a different mechanism (gradient spectral filtering). Next: compare gradient spectra during our sleep phases vs Grokfast filtering to see if they converge on the same signal. Direction: BROADEN. |
| 10 | 2026-03-22 | report | Generated progress-001.html with sleep timing vs grokking step plot. Key visual: sweet spot curve mirrors neuroscience memory consolidation window. |
-->
