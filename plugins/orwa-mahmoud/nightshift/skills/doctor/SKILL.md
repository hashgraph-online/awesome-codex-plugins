---
name: doctor
description: Read-only diagnosis of the workspace, rules, markers, lease, watchman and deadline, with classified next actions.
license: MIT
---

Diagnose the host-opened project **without changing anything**. Doctor is deeper than status: it
explains what Nightshift resolved and which failures that implies. It does not arm, stop, revive,
rewrite, or delete.

The four state files and what each holds are in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/shift/state-map.md`. Report these as different categories; do not merge or move them.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/doctor/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

## 1. Run the inspector

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" doctor
```

Print its report verbatim. Do not summarise away Facts, Warnings, or Actions, and do not re-derive
anything it already resolved: the script uses the same workspace, work-mode, work-target, policy
and ownership libraries as the hooks, and both implementations print the same lines.

The report answers, in its own words: where the workspace is and whether `.nightshift-link` is
valid; the schema version and whether it is current, legacy, malformed, or newer than this plugin;
work mode and work target; the punch-list and staged-work counts; markers, session, process lease
and watchman liveness; the deadline and whether it disagrees with the shift policy; an interrupted provisioning transaction; every
`rules.json` knob it needs and the three native question-tool entries; a `resolved policy` block
naming every effective setting with its source (`built-in`, `rules`, `defaults`, `one-shift` or
`exact-plan`) and expiry (`shift`, `permanent` or `-`); and a `preflight` fact naming which items
need an elevation category the resolved policy does not grant.

Staged work is reported, never offered, while the punch list has open items. Doctor suggests
promoting a draft or a parked Hunt order only when no `- [ ]` remains under `## Items` and no shift
is armed — the same precedence Start applies. With open work, say what is staged and say plainly
that Start works the current list; do not read a count as an invitation to widen the approved
scope, and never promote anything from this read-only skill.

The `work mode` fact is `repository` or `artifact`. When `$NS/work-mode` is missing and Setup
would propose artifact, Doctor warns `work mode is unset; Setup would propose artifact` and offers
`persist the proposed artifact mode with Setup; Doctor does not write work-mode`. When work-mode is
unreadable it warns `work mode is malformed; treating the site as unusable until Setup rewrites it`,
and when the target cannot be resolved it warns
`work target could not be resolved; treating workspace as the code root`. When the record is
missing the resolver takes the workspace or its single immediate child repository.
Skip a symlink or reparse child; it is not a nested checkout.

In artifact mode the report also carries `artifact receipts N` for files under `$NS/receipts/`,
and `latest artifact receipt` with the filename only of the most recently written receipt (no
directory path). When ticked items exist and the receipts directory is empty, Doctor warns
`artifact mode has ticked items but no receipts`. When the path exists but is not a real
directory, it warns `artifact receipts path is not a usable directory` and offers to replace it
so write-receipt can land; it does not also warn empty ticks for that path.
Copies from Archive live under the archive root, `$NS/archive/<YYYY-MM-DD>/receipts/` by default
and do not replace the live files Doctor counts.
Missing or empty receipts create no dated receipts folder.

**Every Warning is a real finding — relay it, do not soften it.** A path that is not a usable file
is a planted symlink where a marker should be, not an empty night; a malformed work mode is not a
working site; a failed clock-out is not a finished shift. Say what each one means for the owner
and, when the report offers a `[confirm]` action for it, name that action.

Doctor never writes the policy file, never runs the project's own tooling, and never prints
credentials, raw evidence, rule values, or the output of a command it did not run.

## 2. Classify actions — do not execute them

The report tags every suggestion:

- `[safe]` — mechanical leftover with no live session (for example a stale watchman pid file whose
  process is already gone). Still do **not** apply it because Doctor was invoked; offer it.
- `[confirm]` — owner decision (broken link, missing setup, leftover STOP while they still want
  the night). During an **unattended active shift** (`$NS/.shift-armed` and open boxes), report that
  the recommendation should be parked with the default "leave in place until morning", but do not
  write the parking lot or ask — the Doctor invocation remains byte-identical.
- `[blocked]` — Nightshift cannot fix this here (non-resumable Codex id, malformed process lease,
  missing host binary, unverified wedge). Say so. Never guess a session id or print/edit a lease
  capability. For a stuck conversation or a fenced recorded session, name
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" stop-shift` — that pauses immediately without waiting for a Stop
  event. Do not run it from Doctor.

When the report says a terminal clock-out failed without releasing the shift, say whether the
recorded conversation can operate or whether a recovery worker still holds the lease; never tell
the owner to reopen a conversation that would stay blocked.

Invoking Doctor alone must leave the tree byte-identical. Never perform a repair merely because
Doctor was invoked.

When cross-host continuity is relevant, summarize stand-down and revival from `$NS/shift-log.md`
(no secrets), and run `continuity-handoff.sh fence-check` only when a duplicate worker or unfenced
prior owner is suspected.

## 3. After the report

Offer the classified repairs after the report. If the owner explicitly asks to apply a `[safe]`
leftover while no shift is armed, they are no longer in Doctor — follow stop/start/setup as those
skills specify. Until that explicit ask, change nothing. During an unattended shift, the offer is
informational only: continue the active work without asking or writing state.

Two repairs the report names are separate owner actions, never Doctor's own:

- Legacy schema migration, offered as `[confirm]` for unarmed legacy workspaces only —
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" migrate-state`. A future version is `[blocked]`: never downgrade a marker.
- A local rule profile. Doctor may list the shipped examples with
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" apply-profile --list`
  and preview one with `--profile <name> --mode fill` (or `--mode replace`). Preview is the
  default; only `--apply` writes, and Invoking
  Doctor never writes `rules.json`.

A senior may run the read-only project inventory after the report:
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" inventory`. It prints one table per
workspace package — package manager and lockfile, the scripts declared for test, lint, typecheck,
build and format, the config files present, and each named tool as `declared`, `runnable` or
`absent`. Those three words are the whole verdict; the report never calls a project misconfigured.
It writes and caches nothing, and Doctor never runs it — offer it, the way every other action here
is offered.

If the owner then explicitly asks to **Export support bundle**, they are no longer in Doctor.
Run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" export-support`.
Print its path, included sections, and omitted categories. Do not upload, attach, transmit, or open
the file. Invoking Doctor alone must not create `$NS/support/`.
