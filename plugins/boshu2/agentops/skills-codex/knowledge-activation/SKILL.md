---
name: knowledge-activation
description: 'Activate mature .agents knowledge.'
---
# Knowledge Activation

Turn a mature `.agents` corpus into operator-ready knowledge surfaces.

## What This Skill Does

Use this skill when the problem is no longer "capture more knowledge," but:

- promote the strongest recurring claims into a belief system
- turn healthy topics into reusable playbooks
- compile a small goal-time briefing for future work
- surface thin topics and promotion gaps before they silently calcify

`$compile` remains the hygiene loop. `knowledge-activation` owns corpus operationalization.

## Where this sits in the flywheel

Knowledge activation is the **fourth step** in the global-corpus workflow.
Use the skills in order:

1. `$harvest` — gather artifacts from many rigs into `~/.agents/learnings/`
2. `$compile` — synthesize raw artifacts into the interlinked wiki at `.agents/compiled/`
3. _(optional)_ `$dream` overnight — bounded compounding loop on top of the compiled corpus
4. `$knowledge-activation` — lift compiled knowledge into playbooks, a belief book, and runtime briefings that future sessions read at bootstrap

## Which skill do I need?

See [docs/skills-decision-tree.md](../../docs/skills-decision-tree.md) for
the full "which skill next?" decision table covering harvest, compile,
dream, knowledge-activation, and quickstart.

## Preconditions

This skill assumes the current workspace already has:

- a `.agents/` directory
- workspace-local builders under `.agents/scripts/`
- packet, topic, playbook, and briefing surfaces that can be refreshed mechanically

Read [references/script-contracts.md](references/script-contracts.md) for the required builder inventory and command ownership.

## Preconditions

This skill assumes the current workspace already has:

- a `.agents/` directory
- packet refresh builders under `.agents/scripts/` when `ao knowledge activate` needs to rebuild source manifests, topics, promoted packets, and chunk bundles from custom workspace logic
- or `.agents/harvest/latest.json`, which `ao knowledge activate` can use as a native fallback to turn the latest harvest catalog into a `harvested-praxis` topic packet, promoted packet, and chunk bundle
- packet, topic, playbook, and briefing surfaces that can be refreshed mechanically

Read [references/script-contracts.md](references/script-contracts.md) for the required builder inventory and command ownership.

## Command Contract

The stable product surface is the `ao knowledge` command family:

```bash
ao knowledge activate --goal "turn agents into usable information"
ao knowledge beliefs
ao knowledge playbooks
ao knowledge brief --goal "fix auth startup"
ao knowledge gaps
```

The skill owns routing, sequencing, interpretation, and next-step recommendations. The builders do the heavy lifting.

`ao lookup` and `ao codex start` consume these outputs as operator context. Matched knowledge briefings are the preferred dynamic startup surface, while selected beliefs and healthy playbooks provide bounded supporting guidance.

## Execution Steps

### Step 1: Preflight

Verify that `.agents/` exists. When you plan to run `ao knowledge activate`, verify that at least one evidence substrate is present:

- packet builders: `source_manifest_build.py`, `topic_packet_build.py`, `corpus_packet_promote.py`, `knowledge_chunk_build.py`
- harvest fallback: `.agents/harvest/latest.json`
- native operator surfaces: `ao knowledge beliefs`, `ao knowledge playbooks`, `ao knowledge brief`, `ao knowledge gaps`

### Step 2: Consolidate Evidence

Run the packet layers in order:

1. source manifests
2. topic packets
3. promoted packets
4. historical chunk bundles

Read [references/dag.md](references/dag.md) for the full DAG and its trust gates.

### Step 3: Distill Operator Surfaces

Refresh the promoted operator layers:

```bash
ao knowledge beliefs
ao knowledge playbooks
```

These should materialize the consumer surfaces under `.agents/knowledge/` and `.agents/playbooks/`.

### Step 4: Compile A Goal-Time Briefing

When there is an active objective, compile a bounded startup aid:

```bash
ao knowledge brief --goal "your goal here"
```

The briefing should stay small, cite its source surfaces, and include warnings when a selected topic is thin.

### Step 5: Surface Gaps

Run:

```bash
ao knowledge gaps
```

This reports thin topics, missing promotions, weak claims needing review, and the next recommended mining work.

### Step 6: Full Outer Loop

If you want the complete pass in one step, run:

```bash
ao knowledge activate --goal "your goal here"
```

That command sequences evidence consolidation, belief/playbook refresh, optional briefing compilation, and a gap summary.

## Trust Rules

- packetization is substrate, not the product
- beliefs, playbooks, and briefings are the real operator surfaces
- thin topics stay discovery-only until evidence improves
- every generated surface should name its consumer
- repeated unchanged runs should stay structurally deterministic

Read [references/output-surfaces.md](references/output-surfaces.md) for the canonical output surfaces and trust boundaries.

## Output Surfaces

The consumer-facing outputs are:

- `.agents/knowledge/book-of-beliefs.md`
- `.agents/playbooks/index.md`
- `.agents/playbooks/<topic>.md`
- `.agents/briefings/YYYY-MM-DD-<goal>.md`
- `.agents/retros/`

The substrate surfaces remain:

- `.agents/packets/`
- `.agents/topics/`
- `.agents/packets/chunks/catalog.jsonl`

## Examples

**Activate the full outer loop for an active goal**

```bash
$knowledge-activation
ao knowledge activate --goal "productize knowledge activation"
```

**Refresh only the belief and playbook promotion layers**

```bash
ao knowledge beliefs
ao knowledge playbooks
```

**Check whether the corpus is safe to promote**

```bash
ao knowledge gaps
```

## References

- [references/dag.md](references/dag.md)
- [references/script-contracts.md](references/script-contracts.md)
- [references/output-surfaces.md](references/output-surfaces.md)
