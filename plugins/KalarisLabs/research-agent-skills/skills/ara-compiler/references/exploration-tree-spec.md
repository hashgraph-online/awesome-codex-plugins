# Exploration Tree YAML Specification

The exploration tree is the "git log" for research — a structured, traversable record of every
successful branch, failed attempt, and design decision that shaped the final result.

## Format

```yaml
# Exploration Tree — {paper_id}
# Research DAG: nested tree with cross-edges (also_depends_on) forming a DAG.
# Node types: question | experiment | dead_end | decision | pivot

tree:
  - id: N01
    type: question
    support_level: explicit
    source_refs: ["§1", "Table 2"]
    title: "{Central research question}"
    description: "{What question is being investigated}"
    children:

      - id: N02
        type: experiment
        support_level: explicit
        source_refs: ["Figure 4", "Table 2"]
        title: "{What was tried}"
        result: "{What was observed}"
        evidence: [C01, "Figure 3", "§2.2"]
        children:

          - id: N04
            type: decision
            support_level: inferred
            title: "{What was decided}"
            choice: "{The chosen approach}"
            alternatives:
              - "{Alternative 1}"
              - "{Alternative 2}"
            evidence: "{What informed this decision}"
            children:
              # ... deeper nesting

      - id: N03
        type: dead_end
        support_level: inferred
        title: "{What was tried and failed}"
        hypothesis: "{What was expected}"
        failure_mode: "{Why it failed}"
        lesson: "{What was learned; what it led to}"
        # dead_end nodes have NO children — they are leaf nodes

  # For DAG edges (node with multiple parents):
  - id: N10
    type: experiment
    support_level: explicit
    source_refs: ["Table 5"]
    title: "{Convergent experiment}"
    also_depends_on: [N07, N08]  # additional parents beyond nesting
    result: "{What was observed}"
    evidence: [C05]
```

## Node Types

### question
The root driver. What is being investigated?
- **Required fields**: `description`
- **Children**: experiments, decisions, other questions

### experiment
An attempt to answer a question or validate a decision.
- **Required fields**: `result`
- **Optional fields**: `evidence` (list of claim IDs, figure/table refs, section refs)
- **Children**: decisions, dead_ends, more experiments

### dead_end
A failed approach. THE MOST VALUABLE NODE TYPE for downstream agents.
- **Required fields**: `hypothesis`, `failure_mode`, `lesson`
- **NO children** — always a leaf node
- Dead ends save agents from rediscovering known failures

### decision
A design choice with documented alternatives.
- **Required fields**: `choice`, `alternatives`
- **Optional fields**: `evidence`
- **Children**: experiments that test the decision, further decisions

### pivot
A change in research direction.
- **Required fields**: `from`, `to`, `trigger`
- **Children**: the new research direction

## Rules

1. **Nested YAML**: Children appear inline under parent node's `children` list
2. **Valid DAG**: No cycles. All `also_depends_on` IDs must exist in the tree
3. **Minimum 8 nodes**: Cover the paper's key research trajectory
4. **Must include dead_end nodes**: At least 1 from ablations or rejected alternatives
5. **Must include decision nodes**: At least 1 documenting a design choice
6. **Every node has**: `id` (N01, N02...), `type`, `title`
7. **Every node has `support_level`**: `explicit` or `inferred`
8. **Explicit nodes should have `source_refs`**: table/figure/section references from the input material
9. **`also_depends_on`**: Only for DAG convergence (node has multiple parents beyond nesting)

## Extraction Strategy

When building from a PDF:
- **Central questions** → root nodes
- **"We tried X" / "We evaluated Y"** → experiment nodes
- **"We considered X but chose Y because..."** → decision nodes with alternatives
- **Ablation results showing X hurts** → dead_end nodes
- **"We initially pursued X but found..."** → pivot nodes
- **"This approach fails because..."** → dead_end nodes

Support-level guidance:
- Mark a node `explicit` only if the paper directly reports it
- Mark a node `inferred` if you are reconstructing a plausible research decision from the narrative structure
- Prefer omission over fabricating a highly specific inferred node

When building from experiment logs:
- Each experiment run → experiment node
- Failed runs → dead_end nodes with actual error messages as failure_mode
- Parameter sweeps → decision nodes with sweep results informing the choice
- Direction changes → pivot nodes with the triggering observation
