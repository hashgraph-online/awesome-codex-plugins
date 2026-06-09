---
name: brainstorming
description: "Use before any feature work — explores intent, requirements, and design. Produces HOTL contracts (intent, verification, governance) before implementation."
---

# HOTL Brainstorming

## Overview

Turn ideas into designs with explicit HOTL contracts. Ask questions one at a time. Present design for approval before any implementation.

<HARD-GATE>
Do NOT write any implementation code until the design is approved and writing-plans has generated the executable workflow.
</HARD-GATE>

## Process

1. **Explore context (cheap preflight first)**

   **Phase 1 — Cheap preflight** (Glob only, current project directory):
   - If user's message references a doc path → read it
   - Check for canonical design docs in `docs/designs/*.md`
   - Check for legacy design docs in `docs/plans/*.md`
   - Check for source code, config manifests, or project-specific config files
   - **"Relevant context" means:** design docs, source code, configuration manifests, or project-specific config. Files like `README.md`, `.gitignore`, `LICENSE`, and scaffolding boilerplate do **not** count.

   **Phase 2 — Branch on result:**
   - **Relevant local context found:** Read the most recent 1-2 design docs from canonical or legacy locations, inspect only relevant in-project files, and optionally review recent commits (only if the directory is a git repo).
   - **No relevant local context found:** State: "This appears to be a greenfield or effectively empty project, so I'm skipping deep context scanning and moving to clarifying questions." Proceed directly to step 2.

   **Hard rule:** Never scan parent directories, sibling folders, or workspace-wide paths unless the user explicitly provides a path.
2. **Determine scope** — decide between `feature`, `phase`, or `initiative` before the clarifying-questions loop. Scope shapes every downstream step: output path, contract structure, depth of inquiry.

   **Scope choices:**

   - **`feature`** — one feature, one bug fix, one refactor. Output: `docs/designs/YYYY-MM-DD-<slug>-design.md` (dated, tactical).
   - **`phase`** — one slice of a multi-phase initiative. Same output family as feature: `docs/designs/YYYY-MM-DD-phase-N-<slug>-design.md`.
   - **`initiative`** — a multi-phase project (v1/v2, platform migration, enterprise rebuild). Output: `docs/designs/<topic>.md` (undated, durable, strategic).

   **Default: feature.** If the user's initial message clearly describes a feature, proceed with `feature` scope without blocking for input. Optionally acknowledge in one line ("Treating as feature scope; say so if this should be a phase or initiative"). Do not pause the flow.

   **Ask the scope question explicitly when the request is ambiguous or multi-phase** (e.g., "migrate v1 to v2", "platform rebuild", "rework across services"). Present the three choices with `feature` as the pre-filled default and wait for the user's answer before continuing.

   **For initiative scope, load the strategic-design template once at session start.** Resolve `adapters/strategic-design.template.md` in this order (same pattern used for `document-lint.sh` and `hotl-config.sh` — see `skills/document-review/SKILL.md`):

   1. If you are working in the `hotl-plugin` repo itself, use `adapters/strategic-design.template.md`
   2. Codex native-skills install: `~/.codex/hotl/adapters/strategic-design.template.md`
   3. Codex plugin install: `~/.codex/plugins/hotl-source/adapters/strategic-design.template.md`
   4. Codex plugin cache fallback: `~/.codex/plugins/cache/codex-plugins/hotl/*/adapters/strategic-design.template.md`
   5. Cline install fallback: `~/.cline/hotl/adapters/strategic-design.template.md`
   6. Claude Code plugin fallback: `~/.claude/plugins/hotl/adapters/strategic-design.template.md`

   Read the resolved template once at session start — its section structure (problem, vision, non-goals, stakeholders, architecture, phase breakdown, risks) becomes the skeleton of the design doc you produce. Do not assume `adapters/strategic-design.template.md` exists in the repo being worked on.

   **For initiative scope, resolve the output directory via `hotl-config-resolve.sh`:**

   ```bash
   bash <resolved-hotl-config-resolve.sh> get designs_dir --default=docs/designs
   ```

   Resolve `hotl-config-resolve.sh` via the same six-location order. The default is `docs/designs` when no `.hotl/config.yml` is present; opted-in projects may override via that config.

3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria. Prefer multiple-choice when the likely answer space is known (e.g., "Which constraints apply? (a) Must not break existing API (b) Backward-compatible (c) Performance-sensitive (d) Other"). Fall back to open-ended only when the problem is unusual or exploratory.
4. **Propose 2-3 approaches** — with trade-offs and recommendation
5. **Present design in sections** — get approval after each section
6. **Define HOTL contracts** — always include all three:

### Intent Contract
```
intent: [one sentence goal]
constraints: [what must not change/break]
success_criteria: [how we know it's done]
risk_level: low | medium | high
```

### Verification Contract
```
verify_steps:
  - run tests: [test command]
  - check: [what to inspect]
  - confirm: [success signal]
```

### Governance Contract
```
approval_gates: [list of steps requiring human review]
rollback: [how to undo if something goes wrong]
ownership: [who is accountable]
```

7. **Write design doc** — path depends on scope:
   - `feature` scope: save to `docs/designs/YYYY-MM-DD-<slug>-design.md` (dated, tactical).
   - `phase` scope: save to `docs/designs/YYYY-MM-DD-phase-N-<slug>-design.md` (dated, tactical).
   - `initiative` scope: save to `<designs_dir>/<topic>.md` (undated, durable). `<designs_dir>` is the value returned by the step-2 resolver (default `docs/designs`). Follow the section structure of the strategic template loaded in step 2.

   **Always write YAML frontmatter with the HOTL marker.** Every saved design doc MUST start with frontmatter declaring at minimum:

   ```yaml
   ---
   design_type: <feature|phase|initiative>   # match the scope chosen in step 2
   created_at: YYYY-MM-DD
   ---
   ```

   The `design_type` field is the deterministic signal that opts the doc into HOTL strict lint (`document-lint.sh` SKIPs unmarked docs). Without it, the doc is treated as non-HOTL and routes through generic AI review only.
8. **Self-check the design doc** — before presenting for human approval, review the saved design doc for: missing constraints, vague success criteria, contract mismatches (do verification steps actually test the intent?), risk_level appropriateness, and scope creep. Fix any issues found. Lightweight: 1-2 passes by default, max 3 only if real issues are found. Do not ask the user to review — this is an internal quality pass.

   **Run document-lint on the saved design doc** as part of this self-check. Resolve `scripts/document-lint.sh` via the standard six-location order, then:

   ```bash
   bash <resolved-document-lint.sh> <saved-design-path>
   ```

   The lint emits two stable warning shapes for feature/phase docs:

   ```
   category=structure severity=warning design_type=<resolved>
   message="missing required section: ## <name>"

   category=implementation-leakage severity=warning design_type=<resolved> line=<n>
   message="<short description>"
   ```

   Apply the **5-step self-check behavior** to surfaced warnings:

   1. Run `document-lint.sh` on the saved design doc.
   2. Surface warnings to the user before asking for approval.
   3. Fix warnings that clearly violate the design/plan boundary.
   4. Justify a warning only when the flagged content sits inside a clearly delimited example block — a Markdown blockquote (`> Example: ...`) or a section whose heading includes the word `Example`. All other findings must be fixed.
   5. Do not block approval unless the user decides the warnings are blocking.

   **Loop bound:** This 5-step procedure runs at most once per self-check pass; the parent self-check (step 8) caps the total at 3 passes before stopping.

   Lint exits 0 even when these warnings are emitted (warning-only contract this pass). Initiative / architecture / contract / reference docs receive neither check; the lint emits no `category=structure` or `category=implementation-leakage` lines for them.
9. **Invoke writing-plans** — transition to implementation planning (feature/phase scope only; initiative designs decompose into child phase plans that each go through their own brainstorming → writing-plans cycle).

## Doc-discipline rules

For `design_type ∈ {feature, phase}` docs, write the body using these **seven required sections in fixed order**. Phase 1 lint enforces presence only; out-of-order or extra sections are not flagged this pass but the prose order below is the canonical convention:

1. `## Intent Contract`
2. `## Verification Contract`
3. `## Governance Contract`
4. `## Scope` (in / out, table form preferred)
5. `## Decisions` (# / decision / choice / rejected alternatives, table form preferred)
6. `## Surface` (APIs / storage / components / files-touched, paragraph each)
7. `## Risks & Open Questions`

Initiative / architecture / contract / reference docs are durable references; they may legitimately include deeper technical shape. The lint defers any rules for them this pass.

### Implementation-leakage anti-patterns

A design doc says **shape**; the workflow file and the code say **exact bytes**. The following patterns belong in `writing-plans` output (or in code itself), not in the design — the lint warns when they appear in feature/phase design bodies:

| Pattern | Example | Why it doesn't belong in design |
|---|---|---|
| File:line references | `cli.py:16`, `auth.ts:204` | Line numbers rot the moment code moves; pin to workflow steps instead. |
| Long fenced code blocks (>10 content lines) | a 30-line Python snippet | Design shows shape; full implementation goes in workflow tasks or code. |
| Dense flag lines (≥6 `--` tokens) | `docker run --network=none --cap-drop=ALL --read-only --tmpfs /tmp ...` | Argv assertions go in workflow steps and tests, not design surface. |

When a design doc must reference one of these (e.g., as an illustrative example), the warning is acceptable and the agent should justify it during the self-check (step 8) rather than rewrite the design.

### Doc-type detection

1. **Frontmatter is the deterministic signal.** A doc is HOTL-managed only when its frontmatter declares `design_type:` (one of `feature | phase | initiative | architecture | contract | reference`) or `hotl_managed: true`. The brainstorming skill always writes the marker; ad-hoc docs in `docs/designs/` are treated as non-HOTL by default.
2. **Filename pattern is a hint, not a classifier.** Dated `YYYY-MM-DD-*-design.md` is the conventional pattern for HOTL-authored docs, but the lint still requires a frontmatter marker before applying HOTL rules. Without a marker, `document-lint.sh` SKIPs cleanly with a clear message and exits 0.
3. **Unmarked design-folder docs route to AI review.** `hotl:document-review` runs a generic-rubric AI review on them; `document-lint.sh` skips them. To opt a hand-authored doc into HOTL strict review, add `design_type: <recognized-value>` or `hotl_managed: true` to its frontmatter.

## Key Principles

- One question at a time — prefer multiple-choice when practical
- YAGNI ruthlessly — remove unnecessary features
- Always propose alternatives before settling
- `risk_level: high` = security, auth, privacy, billing (always human-gated)
