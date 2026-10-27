# Research Findings

## Research Question

<!-- What are we trying to discover? One clear sentence. -->

## Current Understanding

<!-- Updated after each outer loop cycle. What do we know so far?
     What patterns explain our results? What's the mechanism?
     This section should read like the core argument of a paper. -->

## Key Results

<!-- Significant experimental findings. Include metrics, comparisons, and
     brief interpretation. Link to experiment directories for full details. -->

## Patterns and Insights

<!-- What emerges across multiple experiments? What types of changes
     consistently work or fail? Why? -->

## Lessons and Constraints

<!-- Specific actionable learnings that should guide future experiments.
     Things you tried that didn't work and WHY, so you don't repeat them.
     Constraints you discovered about the problem space.

     Examples:
     - Weight decay > 0.1 causes training instability at 125M param scale
     - SwiGLU and RoPE improvements stack because they're orthogonal (FFN vs positional)
     - Baseline only reproduces published numbers with batch_size=64, not 32
     - Sleep phases before memorization completion hurt — model needs memories to consolidate -->

## Open Questions

<!-- What remains unanswered? What would strengthen or challenge
     our current understanding? -->

## Optimization Trajectory

<!-- Summary of inner loop progress. How has the metric evolved?
     Note inflection points and what caused them. -->
