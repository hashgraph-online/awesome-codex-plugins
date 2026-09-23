# Import Track — Authored Sources into Native Documents

Plugin runtime asset. Loaded by the `init` skill (`/archcore:init`): a plain init
runs `import.assess` and, when authored sources exist, the later gates; the
`import` mode runs the whole track at all five discovery levels. Gate records and
track state follow `skills/_shared/gate-contract.md`; interview mechanics follow
`skills/_shared/elicitation-contract.md`. Source levels, records, verdicts, and
the gate measures: `skills/init/lib/sources.md`. Extraction, clustering, type
fit, composition, and the fidelity check:
`skills/_shared/grounding/convert-routing.md`. Decision record:
`init-import-mode.adr`.

## Track behavior

- Stages: `import.assess` → `import.discover` → `import.triage` → `import.plan`
  → `import.convert` → `import.verify` → `import.retire` → `import.discharge`.
- The unit of work is the target document. Sources are clustered by topic; one
  cluster becomes one document of the type its content fits.
- No document is created that the user has not seen in a confirmed preview or a
  confirmed import plan. A source found during conversion waits as a `proposed`
  row for the end-of-wave confirm.
- A created document carries no import mark. The source-to-target map lives only
  in the import plan, and the plan is removed at `import.discharge`.
- Import has no depth. The size tier and the waves balance the volume.
- The init skill MUST change a `.archcore/` document only through
  `update_document`, including a correction the `verify` gate or the CLI hook
  asks for; a file-editing tool never touches `.archcore/`.
- The init skill MUST NOT edit a source file before `import.retire`, and
  `import.retire` edits agent-instruction files (level L1) only.
- Each `budget` knob is the per-gate maximum. A confirm, an `edit`, and a
  `cancel` are gate controls, not interview questions, and draw no budget.
- Content voice for produced documents: `skills/_shared/precision-rules.md`
  Rule 6.

## Size tiers and waves

| Tier | Target documents | Execution |
|---|---|---|
| `S` | ≤ 8 | one preview, one confirm, no plan document; every target converts now |
| `M` | 9–40 | the confirm creates the import plan; every wave runs in this session |
| `L` | > 40 | the confirm creates the import plan and runs wave 1; a later `/archcore:init import` resumes |

[assumption] The thresholds await calibration by `test/behavioral/import-bench.sh`.

Rows are ordered by kind — rule, decision, contract, procedure, reference — then
by `last_change`, newest first. Wave 1 holds the `rule` rows of L1 and the
`decision` rows of L2. Each later wave holds up to 12 rows in plan order. On a
plain init, tiers `M` and `L` both stop after wave 1, because a plain init takes
one confirm; its closing message names `/archcore:init import`.

## Track state and the import plan

The import plan is one `plan` document at the `.archcore/` root: `filename=import`,
no `directory`, `tags=['import-plan']`, `status='draft'`. It is the only carrier of track state
and holds the `archcore:track` block. Its Tasks section holds one row per target:

`- [ ] <n>. <type>: <title> → <directory>/<filename> — spans: <path §heading>; … — wave <w> — <state>`

Row states: `confirmed`, `proposed`, `done`, `dropped` (with a reason). Every row
that `import.plan` writes at the first confirm starts as `confirmed` — the user
saw it in the preview. `proposed` marks only a row found or changed during
`import.convert`, after that confirm; it waits for the end-of-wave checkpoint. Its Acceptance Criteria name the closing
conditions of this track; its Dependencies name the conflicts list. Tier `S`
creates no plan: an interrupted `S` run restarts at `import.assess`, and
`import.convert` Step 5.9 of `convert-routing.md` keeps the rerun free of
duplicates.

WHEN `/archcore:init import` starts and a local `plan` tagged `import-plan`
exists, the init skill resumes per the resume rules of `gate-contract.md` at the
first `confirmed` or `proposed` row, and skips `import.assess` through `import.plan`.
Skip `done` and `dropped` rows. If only closed rows remain, resume the first
unfinished closing gate. For tier `S`, use the import exception in
`gate-contract.md`: keep row results in the session without a plan or state block.

### gate: import.assess

- Purpose: Measure the authored backlog — the target estimate, the size tier,
  the covered hotspot modules, and the levels found — without reading a file
  body.
- Entry conditions:
  - skip_when: a local `plan` tagged `import-plan` exists; the run resumes at
    `import.convert`.
  - The repository root is resolved, and `init_project` has run.
- Elicitation knobs:
  - trigger: none — the executing skill MUST NOT ask questions at this gate.
  - taxonomy: none.
  - budget: 0
- Produces: none — the gate returns `targets_est`, `tier`, `coverage_set`, and
  `levels_found` per `skills/init/lib/sources.md` to the init skill.
- Exit checks:
  - blocking: every size was computed after stripping the archcore managed
    block.
  - blocking: a plain init assessed levels L1 and L2 only, and listed L3–L4
    for presence without a size or a verdict; the `import` mode assessed all
    five levels.
  - blocking: an empty `levels_found` returned `targets_est` 0 and the tier
    `none`; no skip class was lowered to reach a target.
  - advisory: the report states which levels were off and why — a shallow
    clone or a repository without history turns L5 off.
- Next: `import.discover` when `levels_found` is not empty; exit when it is
  empty — a plain init or a refresh runs the code seed with an unchanged pool,
  and the `import` mode prints the no-source report of
  `skills/init/lib/sources.md` and creates nothing.

### gate: import.discover

- Purpose: List every authored source as a source record with exactly one
  level.
- Entry conditions:
  - skip_when: `import.assess` found no source.
  - The path subject, when given, names an existing repository path.
- Elicitation knobs:
  - trigger: none — the executing skill MUST NOT ask questions at this gate.
  - taxonomy: none.
  - budget: 0
- Produces: none — a later gate produces the documents.
- Exit checks:
  - blocking: every record carries `path`, `level`, `bytes`, and `headings`.
  - blocking: no record lies under `.archcore/`, `.git/`, a dependency
    directory, or a build output.
  - blocking: a deleted file from L5 is listed only when the code still
    confirms its decision.
  - advisory: `last_change` is filled for every record when git history is
    available.
- Next: `import.triage` when one or more records exist; exit when a path
  subject matched no source — print the no-source report of
  `skills/init/lib/sources.md` for that path and create no plan.

### gate: import.triage

- Purpose: Give each source record exactly one verdict with a one-line reason.
- Entry conditions:
  - skip_when: `import.discover` listed no record.
  - Source records from `import.discover` exist.
- Elicitation knobs:
  - trigger: none — an undecided audience takes the verdict `mine`, and the
    body read decides.
  - taxonomy: none.
  - budget: 0
- Produces: none — a later gate produces the documents.
- Exit checks:
  - blocking: every record carries one verdict of `convert`, `mine`,
    `reference`, `skip`.
  - blocking: every `skip` names a skip class of `skills/init/lib/sources.md`.
  - blocking: every L4 site yields one planned `reference` fact.
- Next: `import.plan`.

### gate: import.plan

- Purpose: Show the sources and the planned target documents in one preview and
  take the confirm that licenses creation.
- Entry conditions:
  - skip_when: a local `plan` tagged `import-plan` exists.
  - Every source record carries a verdict.
- Elicitation knobs:
  - trigger: the domain or topic directory of a target cannot be decided from
    the corpus and the code layout.
  - taxonomy: Terminology & Consistency from
    `skills/_shared/coverage-taxonomy.md`.
  - budget: 1
- Produces:
  - type: plan
  - status: draft
  - relations: none
- Exit checks:
  - blocking: the preview listed every source with its level, verdict, and
    reason, and every planned target with its type and wave.
  - blocking: no `create_document` call fired before the user typed `confirm`.
  - blocking: tier `S` created no plan document; tier `M` or `L` created the
    import plan before the first target document.
  - advisory: the preview stated the tier, the wave count, and an estimated
    token cost per wave.
- Next: `import.convert` on `confirm`; exit on `cancel` — create nothing.

Before the confirm the targets are planned from paths and headings alone, so a
row may split or merge once bodies are read. A row that changes after the
confirm becomes `proposed` and waits for the checkpoint of `import.convert`. On
a plain init this preview is a block inside the init preview, and the init
confirm is this gate's confirm.

### gate: import.convert

- Purpose: Convert the confirmed rows of the current wave into documents and
  relations, one target per cluster.
- Entry conditions:
  - skip_when: every row is `done` or `dropped`.
  - The user confirmed a preview or an import plan that lists the rows.
- Elicitation knobs:
  - trigger: a resumed plan holds `proposed` rows, or a wave ends with them.
  - taxonomy: none.
  - budget: 1
- Produces:
  - type: the target type of each row, chosen per
    `skills/_shared/grounding/convert-routing.md`
  - status: draft
  - relations: per the relations table of
    `skills/_shared/grounding/convert-routing.md`
- Exit checks:
  - blocking: no created document carries an `imported` tag, a `source:` tag, a
    pointer line, or an `imported-` filename prefix.
  - blocking: no `proposed` row was converted before the user confirmed it.
  - blocking: when an import plan exists, one `update_document` call saved
    the wave's row states, including each finished row as `done`.
  - blocking: for tier `S`, finished rows are `done` in the session only;
    no plan or state block was written to persist row states.
  - blocking: every contradiction with the code or between sources is on the
    conflicts list, not in a document.
  - advisory: a row whose `create_document` call failed stays `confirmed` and
    is named in the report.
- Next: `import.convert` when the tier is `M`, the run is `/archcore:init
  import`, and `confirmed` rows remain; `import.verify` otherwise.

On resume, resolve `proposed` rows at the checkpoint before converting any row.
At the end of a wave, run the same checkpoint for new `proposed` rows.
List the rows and ask the user to confirm, drop, or edit them.
On confirm, set those rows to `confirmed` and convert them in the current wave.
On drop, set those rows to `dropped` with the user's reason.
If a resumed source path no longer exists, set its row to `dropped` and report it.
On cancel, stop conversion and keep finished documents. If a plan exists,
save finished rows as `done` and keep unresolved rows as `proposed` in its wave update.

### gate: import.verify

- Purpose: Check the documents of this run against their contracts and their
  sources.
- Entry conditions:
  - skip_when: this run created no document.
  - One or more rows reached `done` in this run.
- Elicitation knobs:
  - trigger: none — the executing skill MUST NOT ask questions at this gate.
  - taxonomy: none.
  - budget: 0
- Produces: none — the gate reports findings and changes no document.
- Exit checks:
  - blocking: the fidelity check of
    `skills/_shared/grounding/convert-routing.md` ran over every created `rule`
    and `adr`.
  - blocking: every cited `@path` exists.
  - advisory: no created document exceeds its line cap.
  - advisory: the closing report lists the conflicts, the fidelity departures,
    and the rows still open.
- Next: `import.retire` when every row is `done` or `dropped` and one or more
  L1 sources were converted; `import.discharge` when every row is closed and no
  L1 source was converted; exit when rows remain open — the closing message
  names `/archcore:init import`.

### gate: import.retire

- Purpose: Offer to remove from agent-instruction files the sections that the
  created documents now cover, so the agent does not read the same text twice.
- Entry conditions:
  - skip_when: no L1 source was converted, or the user declined retirement
    earlier in this run.
  - Every row is `done` or `dropped`.
- Elicitation knobs:
  - trigger: one or more L1 files hold covered sections.
  - taxonomy: none.
  - budget: 1
- Produces: none — the gate edits source files, never a document.
- Exit checks:
  - blocking: the preview showed, per file, each covered section and the
    document that covers it, before any edit.
  - blocking: no file outside level L1 was edited.
  - blocking: every archcore managed block is unchanged.
  - blocking: a file with uncommitted changes, and a file in an `@import` chain
    the skill could not resolve, was excluded and named.
  - advisory: the report tells the user that `git checkout -- <file>` restores
    a retired file.
- Next: `import.discharge`.

### gate: import.discharge

- Purpose: Remove the import plan, so the corpus holds no record of the import.
- Entry conditions:
  - skip_when: no import plan exists — a tier `S` run.
  - Every row is `done` or `dropped`.
- Elicitation knobs:
  - trigger: none — the executing skill MUST NOT ask questions at this gate.
  - taxonomy: none.
  - budget: 0
- Produces: none — the gate removes the import plan with `remove_document`.
- Exit checks:
  - blocking: the closing report listed the `dropped` rows and the open
    conflicts before the plan was removed.
  - blocking: `list_documents` with the tag `import-plan` returns no local
    document.
- Next: exit.
