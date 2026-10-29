# Human Decision Batch Mode

When the orchestrator output includes `human_review_config`, use batch mode for efficient review of `needs-human-decision` items.

**Under `--yes` (or `--non-interactive`) nothing in this file renders.** `--yes`
implies `--agent-decide`, so `decision_mode` is always `"judge_auto_decide"` and
the guard below routes every item to the judge — no batch summary, no per-item
prompt, no 4-option cap to work around (D6 row 10). The batching described here
exists only for the attended path.

## Batch Mode Guard (Required)

Before prompting for ANY needs-human-decision item, check:

0. Read `human_review_config.decision_mode` from orchestrator output.
   If it is `"judge_auto_decide"` (set by the `--agent-decide` flag, which
   **`--yes` sets for you** — D6 row 10, so an unattended run always lands here):
   - Do NOT prompt the user at all — skip the batch summary AND any
     per-item question.
   - Go directly to the **"Let the Agent Decide" Mode** section below and
     evaluate every item autonomously.
   - This takes precedence over `batch_enabled` and `mode`.
0a. **Partition `needs_human_review` before doing anything else.** Split the items
    into two sets:
    - **Pre-marked judge set** — every item whose `group_id` appears in
      `human_review_config.judge_decide_item_ids`, **OR** that carries a per-item
      `decision_mode == "judge_auto_decide"` field. (The id list is a convenience
      index; the authoritative per-item signal is the `decision_mode` field — fall
      back to scanning that flag if an item has no stable id.)
    - **Interactive set** — all remaining items.
    Then:
    1. **Process the pre-marked judge set first, without prompting.** Run the
       **"Let the Agent Decide" Mode** section below scoped to exactly those items
       (per-item trigger — one judging subagent, or the haiku coordinator fan-out
       if >4). Do NOT ask the user about these items, and do NOT
       include them in any batch summary.
    2. **Then continue the steps below for the interactive set only** — the normal
       batch summary / individual prompts. (If the global
       `decision_mode == "judge_auto_decide"` from step 0, every item is already
       in the pre-marked set by construction, so the interactive set is empty.)
    3. This per-item path is independent of `batch_enabled` / `mode`; it is the
       per-item analogue of the global `judge_auto_decide` mode.
1. Otherwise, for the **interactive set** read `human_review_config.batch_enabled`
   from orchestrator output
2. If `batch_enabled == true`:
   - Do NOT ask the user once per item
   - Present the batch summary prompt ONCE
   - Record all decisions with the same batch context
3. If `batch_enabled == false` OR `human_review_config` is missing:
   - Fall back to asking the user once per item

## Batch Approval Flow

When there are multiple `needs-human-decision` items, present them in batches organized by importance level.

**Ask the user**:
- Question: "There are {N} items requiring human review ({X} HIGH, {Y} MEDIUM, {Z} LOW). How would you like to proceed?"
- Header: "Batch review"
- Options:
  - label: "Review each individually", description: "Traditional one-by-one flow"
  - label: "Let the agent decide", description: "The judge agent evaluates each item using its judgment"
  - label: "Approve all LOW, review others", description: "Auto-approve LOW importance, ask about rest"
  - label: "Approve all MEDIUM and LOW", description: "Auto-approve MEDIUM/LOW, ask about HIGH only"
  (A host whose ask mechanism caps the option count renders "Approve all" and "Skip all" through its overflow channel)

## "Let the Agent Decide" Mode

Trigger this mode when **any** of the following hold:
- the user selects "Let the agent decide" in the batch-approval prompt — scope: **all** `needs-human-decision` items, **or**
- the user selects "Let the agent decide" for a single item in an individual / legacy per-item prompt — scope: **just that one item**, **or**
- `human_review_config.decision_mode == "judge_auto_decide"` (the user passed
  `--agent-decide` on the command line, so no prompt is shown) — scope: **all** `needs-human-decision` items, **or**
- **reviewer pre-marked items via report override** — every item whose `group_id`
  is in `human_review_config.judge_decide_item_ids`, **or** that carries a per-item
  `decision_mode == "judge_auto_decide"` field (set via the report's "Let the agent
  decide" dropdown/checkbox) — scope: **exactly those items**. This is **distinct
  from** the global `--agent-decide` trigger above: that flag targets **all**
  needs-human items, whereas this per-item trigger targets only the items the
  reviewer pre-marked in the report. See **Batch Mode Guard** step 0a for how this
  pre-marked set is gathered and processed (partition-then-process) before the
  interactive set.

The evaluation is identical in every case; only the *set of items* it runs on differs. The per-item trigger exists so a user who is unsure about one specific item can offload just that decision to the judge agent — exactly as `--agent-decide` would have handled it — without touching the other items.

### Who owns the prompt, and where the verdict goes

**Python owns the prompt; this section is narrative, not a template.** The apply orchestrator materializes one judging task per in-scope item into `{phase}/human_decision_tasks.json` (`utils/human_decisions.py`). **For each task in that file, run `task.prompt` as a subagent, then write the JSON it returns to `task.output_path`** — the same print/persist contract every other materialized task uses, and the reason no invoker needs to assemble a judging prompt.

Always judge in a **subagent**, never inline in the main conversation — the reasoning is token-heavy and would crowd the main agent's context. The main agent stays responsible for *applying* and *recording*. Judging is complex reasoning: use the **full model**, never a cheap tier. Only a pure-orchestration fan-out coordinator (which writes no verdict) may be downgraded.

**The judge is not necessarily Claude.** It is whichever agent runs the judging tasks: the host's own agent (through its native subagent tool) on a host that has one, or the runner `driver.subagent_runner` resolves to under `--exec-subagents` — the session model on Codex when available, with `codex:gpt-6-astra` as the host fallback. An explicit `driver.subagent_runner` takes precedence. **Do not choose the judge's name yourself.** The apply orchestrator settles it when it ingests the verdicts and records it on every decision as `batch_context.judge`: the runner spec the executor's provenance proves wrote the verdict file, `<host> host agent` (e.g. `claude-code host agent`) for a verdict the host's own agent wrote, or `executor (runner unrecorded)` when neither can be established. Wherever this file writes `{judge}`, it means that recorded value — read it from `state.json`'s `human_decisions_{phase}` entries, the same records the decisions come from, and copy it verbatim (several distinct values: list each once, comma-separated, in first-seen order). Never replace it with a name of your own, such as your model id or "Claude": the console block, `summary.md` and the HTML report badge all read that field, and this summary must name the same judge they do. Never tell the user "Claude is deciding" unless Claude actually is the judge.

The rules below travel **inside** `task.prompt`, not as a pointer to this file: a headless runner may have no way to open it. They are rendered from `HUMAN_DECISION_JUDGE_RULES` in `utils/subagent_prompts.py`, which is the single source of truth — a test fails when this block and that constant diverge.

**The verdict is a file with a schema, not a shape everyone remembers.** `human_decision_batch_<n>.json` is `{"schema_version": "1.0", "judge": "<the model the judge says it is>", "verdicts": [...]}` (`judge` optional: it is what names a host-native judge's model in the report instead of "claude-code host agent"), each verdict `{group_id, decision, reason, salvaged_description, dropped}` with `decision ∈ approve|salvage|skip` and `salvaged_description`/`dropped` non-null iff `decision == "salvage"` — pinned by `schemas/human_decision_verdicts.schema.json`. The wrapper object (rather than a bare array) is what lets the ingest distinguish a truncated write from a legitimately empty verdict set. Verdicts are never returned as chat text: one that never touches disk is unrecoverable after a crash, invisible to `--resume`, and meaningless under `--detach`.

Re-invoking the apply orchestrator once the verdict files exist ingests them: each verdict is schema-validated (naming the offending file and index), mapped by stable `group_id` — never by batch or list position — recorded via `record_human_decision`, and the work set is rebuilt from the recorded decisions, with `salvaged_description` substituted into the suggestion before batching. A group with no verdict stays `needs-human-decision`; it is never silently approved or dropped. Duplicate `group_id`s are an error unless the objects are identical, in which case the first wins.

<!-- BEGIN GENERATED: judge-rules — rendered from utils/subagent_prompts.py HUMAN_DECISION_JUDGE_RULES. Edit the constant, not this block. -->

### Three outcomes

- **Approve (as-is)** — the suggestion is sound; apply it unchanged.
- **Salvage (partial)** — only *part* of the suggestion is valid or worthwhile; rewrite it down to that defensible core and apply the rewritten version. **This is the default whenever an item is partially valid — never skip a whole suggestion just because part of it is wrong.**
- **Skip** — there is nothing worthwhile to keep; drop the item entirely.

### Evaluation Criteria

Read each item's details (title, description, importance, validation_reason, confidence) and decide based on:

1. **Clear improvement vs. subjective preference**: Approve items that address genuine bugs, security issues, or correctness problems. Be cautious with purely stylistic or preference-based items.
2. **Validation reason signals**: If the validation reason indicates genuine ambiguity ("could go either way", "trade-off", "matter of preference"), lean toward skipping. If it indicates implementation uncertainty ("not sure about scope", "might affect other files"), lean toward approving.
3. **Importance as risk signal**: Be more conservative (lean skip) with HIGH importance items — they have bigger impact if wrong. Be more permissive (lean approve) with LOW importance items.
4. **Security items lean approve**: Security-type items (XSS, injection, auth bypass, data exposure) should lean toward approval.
5. **Deletion caution**: For items that involve removing code/content, require stronger confidence before approving. Deletions are harder to reverse.
6. **Model consensus**: If the `models` array shows multiple models flagged this as `needs-human-decision`, be more cautious. If only one model flagged it while others said `valid`, lean toward approving.

### Deciding Approve vs. Salvage vs. Skip

Apply the criteria above to each **distinct claim inside the suggestion**, not just the suggestion as a whole. Many `needs-human-decision` items are a mix — one solid point bundled with an overreach, a speculative extra, or an out-of-scope aside. Salvaging the worthwhile part is the **default** for such items.

1. **Identify the worthwhile core**: Which specific part(s) address a genuine bug, correctness, security, or clarity issue and survive the criteria above?
2. **Whole thing is sound** -> **Approve** as-is.
3. **Part is worthwhile, the rest is questionable / speculative / out-of-scope / low-confidence** -> **Salvage**: rewrite the description to keep only the worthwhile core and drop the rest. Salvage only ever **narrows** a suggestion — never add anything that was not in the original. The existing criteria still govern the kept part (e.g. deletion caution, security lean-approve).
4. **Nothing survives** — the item is purely subjective, speculative, redundant, or wrong -> **Skip**. Salvage only when a concrete, defensible improvement remains; do **not** manufacture value or apply a watered-down change just to avoid skipping. If there is nothing worthwhile, skip it entirely.

A salvaged item is applied like an approval, except the **rewritten** description is what gets applied — never the original.

<!-- END GENERATED: judge-rules -->

### Process

1. Run the judging tasks from `human_decision_tasks.json` as described above for the item(s) in scope (all `needs-human-decision` items for a batch/`--agent-decide` trigger; just the one selected item for a per-item trigger), writing each reply to its `task.output_path`, then re-invoke the apply orchestrator so it ingests the verdicts.
2. Present an informational summary (not a prompt — do not ask for confirmation):

```
Judge agent ({judge}) decisions for {N} needs-human-decision items:

Approved ({A}):
  - [Title] ({importance}) — {brief reason}

Salvaged ({V}):
  - [Title] ({importance}) — kept: {what was kept}; dropped: {what was dropped}

Skipped ({S}):
  - [Title] ({importance}) — {brief reason nothing was worth keeping}
```

3. Proceed directly:
   - **Approved** items → apply the original suggestion.
   - **Salvaged** items → apply the **rewritten** description (substitute it for the original when building the apply prompt / batch).
   - **Skipped** items → take no action.

### State Recording

Record each decision using the existing `record_human_decision` mechanism. A salvaged item is recorded as an **`approved`** decision (it is an approval of the rewritten suggestion) carrying a salvage marker — this keeps `--resume` and any report consumer treating it as an applied approval, while the `batch_action` / `decision_source` distinguish it.

The markers below are **identical regardless of what triggered the evaluation** — `--agent-decide`, the batch "Let the agent decide" option, or a single-item per-item "Let the agent decide" selection. Recording them the same way means `--resume`, the Markdown apply summary, and the HTML report all surface an agent-decided / salvaged item the same way, with no per-trigger special-casing.

Approve / skip:

```json
{
  "decision": "approved" or "skipped",
  "reason": "Agent decide [{judge}]: {brief reason}",
  "timestamp": "...",
  "batch_context": {
    "batch_id": "{generated}",
    "judge": "{judge}",
    "batch_action": "judge_auto_decide",
    "decision_source": "judge_auto_decide",
    "importance_at_decision": "{importance}"
  }
}
```

Salvage (note `decision` stays `"approved"`):

```json
{
  "decision": "approved",
  "reason": "Agent decide [{judge}] (salvaged): kept {what}; dropped {what}",
  "timestamp": "...",
  "batch_context": {
    "batch_id": "{generated}",
    "judge": "{judge}",
    "batch_action": "judge_auto_decide_salvage",
    "decision_source": "judge_auto_decide_salvage",
    "importance_at_decision": "{importance}",
    "salvaged_description": "{the rewritten description that was applied}",
    "dropped": "{brief note on what was intentionally left out}"
  }
}
```

## Individual Review Mode

For "Review each individually" mode, group items by importance and ask the user once per level.

For each importance level, first display the items as an informational list:

```
== {IMPORTANCE} IMPORTANCE ({count} items) ==

1. [Title]: [Brief reason for needs-human-decision]
   {context line}

2. [Title]: [Brief reason]
   {context line}
```

Then **ask the user** once per importance level:
- Question: "{IMPORTANCE} IMPORTANCE ({count} items): [{comma-separated titles}]. How would you like to handle these?"
- Header: "{IMPORTANCE} items"
- Options:
  - label: "Approve all {IMPORTANCE}", description: "Apply all {count} items at this level"
  - label: "Skip all {IMPORTANCE}", description: "Skip all {count} items at this level"
  - label: "Review individually", description: "Review each item one by one"
  - label: "Next importance level", description: "Skip to the next group"

When the user picks **Review individually**, present each item in turn using the per-item prompt in **Legacy Individual Mode** below — which includes a **Let the agent decide** option so the user can offload any single item they are unsure about to the judge agent.

## Legacy Individual Mode

For single items, when `batch_enabled == false`, or when the user chose **Review individually** above.

For each item, **ask the user**:
- Question: "How should we handle this item?"
- Header: "Review needed"
- Options:
  - "Apply/Fix this item" -> Process it (apply as-is)
  - "Skip this item" -> Skip and continue
  - "Let the agent decide" -> Offload just this item to the judge agent: run **"Let the Agent Decide" Mode** scoped to this single item (spawn one judging subagent per **Delegate the judgment to a subagent**), then apply the original (approve), apply the rewritten description (salvage), or skip per the subagent's verdict, and continue to the next item
  - "Skip all remaining" -> Exit early

The **Let the agent decide** option lets a user who is unsure about a specific item hand that one decision to the judge agent; it behaves exactly like `--agent-decide` would for that item (Approve / Salvage / Skip, with salvage preferred over skipping a partially-valid item). Record its outcome with the same `judge_auto_decide` / `judge_auto_decide_salvage` markers shown under **State Recording** so reports and `--resume` treat it identically to a flag-driven auto-decision.
