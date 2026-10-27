# Provenance Tracking System

## Why Provenance Matters

In a human-AI collaborative research process, the origin of each piece of knowledge determines
its epistemic status. A claim the user explicitly stated has different weight than one the AI
inferred from code output. Provenance tracking ensures:

1. **Auditability**: Reviewers/collaborators can trace every assertion to its source
2. **Trust calibration**: AI suggestions are clearly marked as unconfirmed
3. **Correction flow**: When users revise AI suggestions, the revision history is preserved
4. **Accountability**: AI actions (code written, tests run) are attributed correctly

## Provenance Tags

### `user` — User Confirmed/Input

The user explicitly stated, typed, or confirmed this information.

**When to apply:**
- User directly says something: "The learning rate should be 3e-4"
- User confirms an AI suggestion: "yes, log that" / "correct"
- User provides a decision: "Let's go with approach A"
- User states a research question: "Can we reduce memory by 50%?"

**Examples:**
```markdown
## C01: Attention is sufficient for sequence modeling
- **Statement**: Self-attention alone, without recurrence, achieves SOTA on translation
- **Provenance**: user
```

```yaml
- id: N05
  type: decision
  provenance: user
  title: "Use GQA instead of MHA"
  choice: "GQA reduces KV cache by 8x with <1% quality loss"
```

### `ai-suggested` — AI Inference (Unconfirmed)

The AI inferred, proposed, or hypothesized this based on context. The user has NOT
explicitly confirmed it.

**When to apply:**
- AI observes a pattern in code/output and proposes an interpretation
- AI suggests a research direction
- AI infers a claim from experimental results
- AI proposes a classification for an observation
- AI suggests what a decision's alternatives might have been

**Examples:**
```markdown
## C07: The overhead-aware refiner prevents QoE collapse under sustained bursts
- **Statement**: Without the refiner, preemption overhead accumulates and degrades QoE
- **Provenance**: ai-suggested
<!-- AI inferred this from the ablation results; user has not confirmed -->
```

```yaml
- id: O03
  provenance: ai-suggested
  content: "Training instability above batch_size=64 may be caused by gradient norm explosion"
  context: "Observed NaN losses during hyperparameter sweep"
```

**Upgrade path**: When user confirms → change to `user` or `user-revised`

### `ai-executed` — AI Action

The AI performed a concrete action: wrote code, ran a command, created a file,
executed a test.

**When to apply:**
- AI wrote or modified a source file
- AI ran a benchmark or test suite
- AI created an ARA entry
- AI generated experimental results

**Examples:**
```yaml
- type: ai-action
  action: "Wrote src/scheduler_v2.py implementing greedy knapsack"
  provenance: ai-executed
  files_changed: [src/scheduler_v2.py]
```

```yaml
- id: N12
  type: experiment
  provenance: ai-executed
  title: "Ran BurstGPT benchmark with overhead-aware refiner"
  result: "97% requests achieve QoE >= 0.95"
```

### `user-revised` — AI Suggested, User Modified

The AI made a suggestion, and the user modified it rather than accepting or rejecting outright.

**When to apply:**
- User says "not exactly, it's more like..."
- User corrects a detail: "the threshold is 90%, not 85%"
- User refines scope: "that's true but only for dense models"
- User provides nuance: "yes but the real reason is..."

**Examples:**
```markdown
## H03: Batch size search space pruning
- **Provenance**: user-revised
<!-- AI initially suggested pruning to [1, B_max]. User corrected:
     "No, B_min is also bounded — below B_min, TDS > r_user for all requests" -->
```

**Track the revision:**
```yaml
- id: O05
  provenance: user-revised
  content: "KV cache watermark threshold should be 90%, not 85%"
  revision_history:
    - original: "ai-suggested watermark at 85%"
    - revised: "user corrected to 90% based on profiling data"
```

## Provenance in Different File Types

### Markdown Files (claims.md, heuristics.md, etc.)

Use the `Provenance` field in the structured entry:

```markdown
## C{XX}: {title}
- **Provenance**: user | ai-suggested | user-revised
```

For inline notes within longer text, use HTML comments:

```markdown
The system achieves 97% QoE coverage <!-- provenance: ai-executed (from benchmark run) -->
under bursty load conditions <!-- provenance: user (stated requirement) -->.
```

### YAML Files (exploration_tree, sessions, staging)

Use the `provenance:` field on each node/entry:

```yaml
- id: N05
  type: decision
  provenance: user
```

### Mixed-Provenance Entries

Some entries have mixed provenance (e.g., AI ran experiment, user interpreted result):

```yaml
- id: N12
  type: experiment
  provenance: ai-executed        # AI ran the benchmark
  result: "97% QoE >= 0.95"     # Factual output
  interpretation:                # User's reading of the result
    provenance: user
    content: "This confirms our hypothesis — overhead awareness is critical"
```

## Provenance Aggregation in Session Records

Session records aggregate provenance statistics:

```yaml
provenance_summary:
  user_confirmed: 5          # Events with provenance: user
  ai_suggested: 3            # Unconfirmed AI suggestions
  ai_executed: 7             # AI actions taken
  user_revised: 1            # User corrections to AI suggestions
  confirmation_rate: 0.625   # user / (user + ai-suggested)
```

This helps track how much of the research knowledge is human-confirmed vs. AI-inferred,
providing a trust signal for the overall artifact quality.

## Rules for Provenance Integrity

1. **Never auto-upgrade**: `ai-suggested` → `user` requires explicit user confirmation
2. **Preserve history**: When upgrading, keep the original provenance in a comment or revision field
3. **Default conservative**: When unsure, use `ai-suggested`
4. **Compound events**: If user asked AI to run something, the action is `ai-executed` but the interpretation may be `user` or `ai-suggested`
5. **Silence is not confirmation**: If you suggest something and the user doesn't respond, it stays `ai-suggested`
