---
name: figma-preflight
description: >-
  Mandatory read-only gate that runs before any write to a Figma file, through figma_execute
  (figma-console MCP) or use_figma (official Figma MCP). Runs 8 checks in order (live connection,
  confirmed target node-id, metadata, variables, design system and icon search, canon references,
  state coverage, file lock) and either approves the write or returns a fix list. It never mutates the canvas. Also
  audits cross-screen flow: orphan screens, CTAs without a destination, dead ends. Use when the
  user asks to create, edit, build or instantiate anything in Figma, or asks "audit the flow",
  "audita o fluxo", "tem tela órfã?", "esse botão leva pra onde?".
license: MIT
compatibility: >-
  Gate for writes through figma-console-mcp (figma_execute, Desktop Bridge plugin in Figma
  Desktop) or through the official Figma MCP server (use_figma, Full seat, not validated by this
  repo). The file lock script needs Python 3 (standard library only). Reads the figma-canon
  skill. The optional local evidence script of figma-bridge-doctor is macOS only.
metadata:
  author: Thiago Xikota
  version: "1.2.0"
---

# figma-preflight

Mandatory pre-write checklist. Blocks the write (`figma_execute`, or `use_figma` on path B of
Check 0) until all checks pass.

This skill is a gate. It approves the write or returns a fix list. It never mutates the canvas.

## Triggers

- Auto-fires when user intent is to WRITE to Figma (create, edit, build, instantiate).
- Auto-fires before:
  - any write through the figma-console `figma_execute` tool (Desktop Bridge)
  - any write through the official Figma MCP server's `use_figma` tool
  - the canvas build phase of your project's own build skill or workflow, if any
- Does NOT fire on read-only operations (orient, inspect, audit).

## Which server each tool belongs to

- figma-console MCP server (Southleft): `figma_execute`, `figma_get_status`, and every other
  `figma_*` tool named here.
- Official Figma MCP server: `get_metadata`, `get_variable_defs`, `search_design_system`,
  `whoami`, `use_figma`.

Checks 1 to 4 name the official server's read tools. When only figma-console is connected, read
the same kind of data with its own tools. These are alternatives, not one-to-one equivalents: the
output shapes differ.

| Check | Official Figma MCP tool | figma-console alternative |
| --- | --- | --- |
| 1, 2 | `get_metadata` | `figma_get_file_data`, `figma_get_file_for_plugin`, `figma_get_selection` (for the active selection) |
| 3 | `get_variable_defs` | `figma_get_variables`, `figma_get_token_values`, `figma_get_styles`, `figma_get_text_styles` |
| 4 | `search_design_system` | `figma_search_components`, `figma_get_library_components`, `figma_get_design_system_summary` |

## The 8-check gate

Run all 8 in order (Check 0 to Check 7). Each must pass before the next runs. Fails closed
(blocks the write).

### Check 0: Live connection to Figma

Two paths pass this check. Only an MCP call proves the connection: a shell command NEVER does.

- **Path A, figma-console (the path this repo validates).** AUTHORITY: `figma_get_status` with
  `probe:true`, returning `setup.valid=true` plus the correct `connectedFile`. A shell command
  cannot attest that the plugin is paired: ports 9223 to 9232 are a pure WebSocket with no HTTP
  endpoint (field note, 2026-08). Write path: `figma_execute` through the Desktop Bridge.
- **Path B, official Figma MCP server only.** When the official server is the only live connection
  (figma-console is not installed, or its Bridge is down): a successful `whoami` plus a successful
  `get_metadata` on the target (that call also satisfies Check 2). Write path: `use_figma`. Path B
  is not validated by this repo: keep writes small, read back every change. Follow the official
  server's own instructions for `use_figma`.
- [`figma-bridge-doctor/scripts/figma-status.sh`](../figma-bridge-doctor/scripts/figma-status.sh) (in the `figma-bridge-doctor` skill's `scripts/`
  directory, macOS only; in Claude Code run it as
  `bash "${CLAUDE_SKILL_DIR}/../figma-bridge-doctor/scripts/figma-status.sh"`, which needs that skill
  installed next to this one) is LOCAL evidence only: Figma is running, servers are listening. By
  design it does not report pairing (it prints `current_file_pairing=ask_figma_get_status`). Use
  it for diagnosis, not as a verdict.
- If neither path confirms the connection, the write MUST be blocked. Bridge recovery goes through
  the `figma-bridge-doctor` skill: when figma-console is installed, try it before you fall back to
  path B.

> **Advisory pre-check A0 (optional, path A; path B already runs it):** Call `whoami` (official
> Figma MCP server) once per session if you do not know which seat the connected account holds OR
> you are writing to a file you do not own. A seat mismatch (for example a Dev seat writing to a published library) fails loudly
> with a permission error, so this is an *early feedback* convenience, not a silent
> failure preventer. **Skip for:** a solo developer on personal drafts, sessions where you already
> know the seat, or when you are on the Starter plan's MCP tool call budget. The 7 hard checks
> below cover the silent failures.

### Check 1: Target node-id confirmed

- Has the user provided a specific node-id OR is there an active Figma selection?
- "The header frame" is NOT confirmed. You need an explicit node-id.
- If ambiguous: run `get_metadata` and ask the user to disambiguate.

### Check 2: get_metadata run this session

- Has `get_metadata` been called on the target page or frame in this session?
- If NO: run `get_metadata` now and parse the structure.
- If YES: reuse the earlier result from this session.

### Check 3: get_variable_defs (if the write touches styled properties)

- Will the write set fills, strokes, spacing, typography or radii?
- If YES: `get_variable_defs` MUST have been called on the relevant scope.
- If NOT called: run it now.
- Required for token-bound writes.

### Check 4: search_design_system (if the write creates new UI)

- Will the write create a frame or component that COULD be an existing component?
- If YES: `search_design_system` MUST have been run with a relevant query.
- Block "new Button" / "new Card" / "new Input" writes if the search was not run.
- **ICONS / ILLUSTRATIONS (anti-hallucination, field note, 2026-06):** NEVER hand-draw an icon
  (`createNodeFromSvg` with invented geometry) before checking what the design ALREADY has. Two
  sources to scan FIRST:
  1. The file's icon component pages (for example an "Icons" page, whatever language it is named
     in). Instantiate those brand components. Do not redraw.
  2. The codebase's real assets. Grep the screen or component source for the actual icon: the
     `lucide-react-native` import name, a `require('../assets/icons/calendar.png')` asset, or an
     SVG file.

  Match the app's REAL icon. A tab bar that uses brand PNG icons must use those assets or their
  componentized equivalents, never a generic geometric calendar, trophy or user that you drew. If
  a needed icon has no component, use the real asset (image fill) and FLAG the library gap. Never
  substitute a look-alike you invented. Block any icon-bearing write where neither the icon
  library nor the app asset was checked.

**The WHOLE feature, not only the node you are about to write (field note, 2026-08).** The check
above is per write, and that is how one feature accumulated **dozens of hand-drawn icons under
many different names** across several sessions: each individual write looked innocent. When you enter a
feature that ALREADY EXISTS, run an adherence sweep before you start: count the nodes with an icon
name (`icon-*` or its equivalent in the file's language, for example `icone-*` in Portuguese;
`spinner-*`; a glyph in a TEXT node) that are NOT a library instance. If the number is not zero,
that is debt to report at the start, not to discover when the designer points at it. The same
sweep closes the work: zero ad hoc icons on the page is the proof. "I replaced N icons" is not.

### Check 5: figma-canon refs loaded

- Required refs per context (files under [`figma-canon/references/`](../figma-canon/references)):
  - Any write: `plugin-api-core.md` + `figma-execute-atomicity.md` + `auto-layout-canon.md`
  - Write touches tokens, variables, annotations or images: + `plugin-api-data.md`
  - Write hits edge cases (sections, connectors, masters, image fills, rate limits):
    + `plugin-api-anomalies.md` (for a 429 lockout it points on to `rate-limit-recovery.md`)
  - New screen: the refs above + `state-coverage.md` + `ai-slop-signatures.md` +
    `naming-canon.md`
  - Handoff prep: the refs above + `handoff-format.md`
- If not loaded: load now before proceeding.

### Check 6: State coverage planned (if creating a screen)

- For new screen creation: which states are required (for example Empty / Loading / Error /
  Success / Edge; the decision table gives the full set per screen class)?
- Use the decision table in [`figma-canon/references/state-coverage.md`](../figma-canon/references/state-coverage.md).
- If the states are not explicitly planned: ask the user OR stop and clarify.

### Check 7: Figma file lock claimed (single-driver invariant)

One Figma file has one writer at a time. The lock script is
[`scripts/figma_lock.py`](scripts/figma_lock.py) in this skill (Python 3, standard library only).
The commands below call it as `"${CLAUDE_SKILL_DIR}/scripts/figma_lock.py"`. Claude Code replaces
`${CLAUDE_SKILL_DIR}` with this skill's directory (the folder that holds this file) when it loads
the skill. Other agents: if the text still shows `${CLAUDE_SKILL_DIR}`, put the absolute path of
that folder in its place; never run a command with the variable empty.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" claim <fileKey> --agent <agent> --task <task> [--ttl 1800]
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" check <fileKey>
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>
python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" sweep
```

How the script behaves:

- File-based: one JSON lock per `fileKey` under `~/.cache/figma-maxxing/locks/` (override with
  `FIGMA_LOCK_DIR`). Every session on the machine must use the same lock directory. A session
  with a different `FIGMA_LOCK_DIR` does not see the others' locks.
- The lock is advisory: it only protects sessions that check it.
- The lock is TTL based (`--ttl` in seconds, default 1800), with no PID tracking. A lock tied to
  the PID of a transient tool shell dies immediately (agent tool shells exit right after every
  command), which is why this lock is TTL based (field note, 2026-08).
- Every command prints one JSON object. Exit code 0 on success, 1 on conflict or when the lock
  directory stays busy (`{"error": "lock directory is busy"}`), 2 on a usage error (a `fileKey`
  that is not 1 to 64 letters, digits, `_` or `-`; a `--ttl` that is not positive; `release`
  without a task). A usage error prints the argparse message, not JSON.
- `check` prints `{"held": false}` or
  `{"held": true, "agent": ..., "task": ..., "claimed_at": ..., "expires_at": ...}`. It always
  exits 0 and never reserves the file.
- `claim` prints `{"claimed": true, "renewed": false, ...}` on a fresh claim. A `claim` by the
  same agent and task renews the lock (`"renewed": true`). A `claim` on a lock held by someone
  else exits 1 and prints the holder: `{"claimed": false, "held": true, "agent": ..., ...}`.
  Expired locks are treated as free.
- `release` prints `{"released": true, "held": false}`. If someone else holds the lock it exits 1
  and prints the holder. If nothing is held it prints `{"released": false, "held": false}` and
  exits 0.
- `sweep` deletes expired lock files and prints `{"swept": <count>}`. It is housekeeping only:
  an expired lock is already treated as free.
- `--agent` defaults to the environment variable `FIGMA_LOCK_AGENT`, then to the literal `agent`.
  `--task` defaults to `FIGMA_LOCK_TASK`. A `claim` with no task at all gets a generated
  `adhoc-<uuid>` task that you would have to copy from the claim output to release. Always pass
  an explicit `--agent` (for example `claude-code`) and `--task`.
- `release --force` releases a lock held by another task. It exists for the human, not for the
  agent. Never use it yourself.

The gate:

- Resolve the `fileKey` from the Figma URL, `figma_get_status`, or the `figma-map.md` written by
  `figma-orient` (default `docs/figma-map.md`, or the agent's own memory system).
- Diagnosis only: `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" check <fileKey>`. A free check does not reserve
  the file. Only a successful claim authorizes you to proceed.
- If `held=false`: claim it with
  `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" claim <fileKey> --agent <agent> --task <task> --ttl 1800`.
- If `held=true` and you ARE the holder (`agent` and `task` match): proceed.
- If `held=true` and you are NOT the holder: BLOCK the write. Surface who holds it and tell the
  user to either wait until `expires_at` or release the conflicting lock manually. Do NOT bypass.
- Release in cleanup or `finally`, on success and on failure alike. In a shell script, use
  `trap`. Keep exactly the same `--agent` and `--task` as the claim (or the same
  `FIGMA_LOCK_AGENT` and `FIGMA_LOCK_TASK`). An abrupt death without cleanup depends on TTL
  expiry. Never release the lock of another task.
- Release after the write completes:
  `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>`.
- One isolated script error (for example `{"error": "lock directory is busy"}`) does not declare
  the gate broken. Re-test. Only proceed without a lock when
  [`figma-bridge-doctor/scripts/figma-status.sh`](../figma-bridge-doctor/scripts/figma-status.sh) shows `other_sessions_count=0`, and flag it in
  your reply. That script is macOS only, and it tells this session's MCP server apart from the
  others through the agent's process tree (environment variable `FIGMA_AGENT_PROCESS`, default
  `claude`; see the script's header). Where it cannot run or cannot show
  `other_sessions_count=0`, do not write without a lock: report the script error to the user and
  stop.

#### Narrow exception: disjoint pages

A lock held by someone else normally blocks the write. This exception applies only when BOTH are
true:

1. The holder is another live agent session.
2. You PROVE that its writes and yours land on different pages. The proof has three parts:
   `figma_get_status` shows the plugin's `currentPage` on the holder's page, the `task` of the
   lock names the holder's subject, and every one of your targets is addressed by node-id on
   another page.

Who may override:

- With the designer in the conversation: the designer decides. Ask ONE multiple-choice question
  (override now, recommended; wait for the lock; or the designer releases it if the other session
  has finished).
- With no way to ask (autonomous run): you may override, under all of these conditions:
  - write by node-id only
  - NEVER call `setCurrentPageAsync`
  - at the end of the batch, run the rival-write audit of the `figma-bridge-doctor` skill
    (section "After reconnecting in a WRITE session: rival-write audit", full text in
    [`figma-bridge-doctor/references/rival-write-audit.md`](../figma-bridge-doctor/references/rival-write-audit.md))
    on the section you wrote, and report the result
  - state the override in your reply so it stays in the transcript, including the sentence
    "I wrote under a lock override"

Same page, or no proof that the pages are disjoint, stays BLOCKED. This is NOT a new default of
the gate. It codifies two field cases, and the designer can revoke it.

## Output

### Pass

```text
PASS figma-preflight: all 8 checks clear. Proceeding to write.

- Connection: path A, Bridge connected (port 9223) | path B, official MCP (writes via use_figma)
- Target: <node-id> (<name>)
- Metadata: cached <Nm ago>
- Variables: <N> tokens loaded
- DS search: <N> components found
- Canon loaded: <ref list>
- States planned: <state list>
- File lock: held by <agent> task=<task> until <expires_at>
```

### Fail

```text
FAIL figma-preflight: <N> gap(s) before write can proceed:

1. <gap description> -> <fix action>
2. ...

Run the fixes, then re-invoke figma-preflight.
```

## Override

The user can override with an explicit:

- "skip preflight" (or the same request in the user's language)
- "I confirm target is X, proceed"

State the override in your reply, in one line ("preflight skipped on request"), so it stays in
the transcript.

## Post-approval: write execution rules

After the preflight OK, BEFORE generating any JS for `figma_execute` (or `use_figma` on path B):

1. Load the refs required by Check 5 (the single list lives there), plus
   [`figma-canon/references/naming-canon.md`](../figma-canon/references/naming-canon.md) if there is a new layer.
2. When the write finishes (or aborts): release the lock with
   `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>`. Forgetting to
   release blocks future sessions until the TTL expires.
3. Never send the known failing patterns: a sync `figma.currentPage = X` assignment, a missing
   `await` on an async call, `figma.notify()`, `setPluginData`, `createConnector`. The optional
   precheck hook (`hooks/figma-canon-precheck.py` at the root of the figma-maxxing repo, opt-in)
   flags these patterns. If it fires:
   read the message, fix it at the source, do NOT retry blindly.
4. **Check the ancestor chain for `locked` (field note, 2026-08).** In one large bind sweep
   through the figma-console bridge, a handful of binds under a GROUP with `locked: true` did not
   take, with no error, while each node read `locked: false`. Figma's typings say `locked` does
   not affect plugin writes, and the cause is not established. The check is cheap: in a write that
   sweeps a tree, check the chain (`for (let p=n; p; p=p.parent) if (p.locked) ...`), not only the
   target, and rely on the read-back in rule 5 either way.
5. **Post-write verification reads the PROPERTY YOU CHANGED, never a proxy.** In that same batch
   the read-back checked color and opacity and came back green on the nodes that were never
   written: color and opacity really had not changed, precisely because nothing happened. If you
   bound a variable, read `boundVariables[prop][i]`. If you created a node, read its id in the
   parent. An independent count AFTER the batch, compared against the expected number, is the
   only closure that counts.

## Cross-screen flow

For a NEW SCREEN write (not an edit), after the per-screen checks, answer these before the write:

1. Which flow the screen belongs to.
2. Which CTA of which existing screen brings the user here: a real node-id, or a "predecessor to
   build" stated in your reply so it stays in the transcript. A screen with no entry is born
   unreachable: refuse it.
3. Every interactive element on the new screen has a destination (node-id), a "plan to build"
   stated in your reply, or "out of scope" with a specific reason.

### Audit mode

Read-only. Use it on requests such as "audit the flow", "is there an orphan screen?", "where does
this button lead?".

Build the graph of the scope:

- device-sized frames = nodes
- `reactions[]` = wired edges
- CTA text = implicit edges. For example "Filter" implies a Filter screen and "See all" implies a
  list screen. Match the CTA text in whatever language the file uses, ignoring case and
  diacritics.

Emit a punch list. Never mutate the canvas.

- ORPHANS: a screen with no incoming edge (unreachable).
- DEAD ENDS: a screen that has CTAs but zero outgoing wired edges.
- DANGLING CTAs: an interactive element whose text implies a destination that is missing in the
  scope. Always quote the CTA text.
- WIRED-BUT-BROKEN: a reaction that points to a deleted or missing node.
- SEMANTIC MISMATCH: a wired reaction, inside the scope, whose target does not match the CTA text.
- CYCLES: informational, not a bug.

### Hard rules (paid for in production)

- NEVER auto-create a missing screen: half of the "missing" ones are out of scope on purpose.
  Surface it, list the candidates, the human decides. After that, the build belongs to your
  project's own build skill or workflow, if any.
- A wire that leads to a screen that does not match its CTA text is a SEMANTIC MISMATCH, not a
  "misroute". Check the project's product documentation (spec, flow map, handoff doc), if any,
  before you recommend a re-wire (field note, 2026-05: on one project a session reverted a wire
  based on a doc claim and the designer had to undo it).
- A project's glossary of implicit destinations (product terms that imply a specific screen)
  lives in the project's repo, not here. Apply it only inside that project's file.
- Back-navigation cycles are healthy. Do not report them as a problem.

## Composes with

- `figma-canon`: this gate reads the relevant refs as part of Check 5.
- figma-console `figma_execute` (Desktop Bridge) and official `use_figma`: preflight runs BEFORE
  any Figma write.
- `figma-bridge-doctor`: owns Bridge recovery when Check 0 fails on path A.
- `figma-orient`: preflight uses the orient output as input for Checks 1 and 2.
- `figma-click-flow`: the visual arrow overlay is a separate skill. The audit here only analyzes
  the graph in memory.
