# Selection and launch modes

The shared contract behind Hunt and Quality: how the workspace is bound, who selects work, when
the clock starts, and how several entries become one shift.

## State map

`punch-list.md` is owner-approved work active in this shift; `drafting-table.md` is known work
staged for a later shift; `parking-lot.md` holds unresolved owner decisions and the default that
kept work moving; `work-orders.md` holds timed catalog work composed through Hunt. Ordinary known
plans never become work orders. Every skill binds `$TASK_ROOT`, `$NIGHTSHIFT_WORKSPACE`, and `$NS`
itself, once, and never re-resolves them.

## Selection

- **Guided** — the owner chooses one or more catalog entries, then may add scope or approach.
- **Automatic** — the owner's sentence is binding intent. The model is the planner.

A time budget, an actionable objective, and clear direct-execution intent — regardless of
wording — are sufficient to run Automatic directly. Do not present catalog cards. Do not ask
who selects. Ask only a field that is still missing.

Automatic is not a catalog-ranking exercise and not a keyword router. Read every entry in
`shifts/` so the model knows what tools exist, then inspect the work target. Compose the
entries that support the stated objective (Product Evolution, journeys, documentation, or a
specialist shift when they fit). Quality, coverage, and dependency work do not hijack a
feature or design objective because fingerprints were easy to detect. They become the
objective only when the owner asked for that work, or when Automatic finds no stronger
stated intent — and the receipt must say so. Review-first preview is model prose.

In repository mode inspect tooling, tests, documentation, issue references available in the
workspace, and recent git history. In artifact mode that is the persistent folder's files
and any existing source manifests or reports; do not require a git history that cannot exist.
Compose, cut and arm only through the Start preflight; it refuses, and names the repair, when the
work target cannot be resolved, work-mode is missing or malformed, or `$NS/receipts` exists but is
not a usable directory. Never `git init` a notes folder to get past a refusal.
An entry is applicable only when the work target can supply its discovery surface. Skip coverage,
CI, dependency, and similar quality-debt entries when the folder has no tests, tooling, or
manifests to inspect — and the owner did not ask for that work. In artifact mode:
Skip the GitHub issue hunt when work mode is artifact, or when no proposed imports exist.
Skip the defect hunt when work mode is artifact.
Skip documentation drift when work mode is artifact.
Skip TODO and FIXME debt when work mode is artifact.
Skip coverage hunt when work mode is artifact.
Skip tooling quality-debt entries when work mode is artifact.
For each composed entry record one sentence of evidence that ties it to the owner's intent.
When packing more than one entry:

1. honor the stated objective first;
2. remove overlaps: one finding belongs to one entry;
3. run finite entries first;
4. if useful time remains, choose at most one open-ended entry to use it.

One deadline governs the whole automatic shift, and automatic mode always requires hours.

## Launch

- **Review first** — discovery is read-only. Show the evidence, selected entries, order, scope,
  endings, and hours in prose. Write and arm nothing until the owner approves. The clock starts only after
  that approval.
- **Run directly** — the owner's choice is explicit authority to discover, select, implement, and
  verify within the stated scope and time. Start the clock immediately, assemble and cut one work
  order, arm one shift, and continue selecting work that serves the stated objective until quitting time.

When the prompt already carries clear direct-execution intent, infer Run directly. Do not ask
**review first, or run directly?** Guided and incomplete Automatic still ask; that choice is
independent from Guided or Automatic.

Guided + run directly still performs the selected entry's discovery, but it does not pause after
showing the findings. Guided + review first does pause. Choosing a category is not by itself approval
to implement; the launch choice decides that.

## Tooling policy, and tonight's one question

A third independent choice, and the only question composition asks. On a complete Automatic prompt,
do not ask it: use existing-tools, no new elevation, and remembered verification from
`shift-defaults.json` when present. The owner may still name a policy or allowance in the same
sentence.

- **Existing tools only** — skip contracts whose required capabilities are unavailable and spend
  the time elsewhere. The default, including when `$NS/shift-defaults.json` is missing.
- **Review missing tools first** — one read-only consolidated plan (capability, selected tool,
  exact writes, commands, enabled shifts, risks, permissions, rollback), then wait. It writes
  nothing and the work clock has not begun.
- **Automatically add standard development tools** — authorization for eligible local development
  tooling; do not pause again to re-ask. The model inspects the package manager, chooses a
  compatible tool, installs, smokes, and records, behind the thin `provision.sh` / `provision.ps1`
  seatbelt: baseline → write-surface diff → rollback. A symlink or reparse escape is refused,
  rollback must actually run, inventory and Git stay consistent on a failed tooling commit, and
  unknown flags do not mutate. Auto-add runs only under the elevation categories tonight's policy
  allows; a missing seatbelt is a skip reason and the shift continues under existing tools.

Artifact mode refuses repository-tool policies (`auto-add`, `review-missing`) and explains why;
only existing-tools is valid there. Inventory in `$NS/capabilities.json` is a cache: re-probe each
new shift or branch. Recovery runs before Start, so a shift never opens on an unproven baseline.
Unsupported permission modes must be reported before arming.

Three files hold every setting, and no others exist. `rules.json` is the owner's permanent project
boundary — default denies, protected paths, forbidden commands, and any elevation they chose to
remember. `shift-defaults.json` remembers convenience choices (verification profile, typical hours,
tooling policy, review-first vs run-direct); it only prefills the next question, decides nothing on
its own, and never carries elevation. `shift-policy.json` is tonight's authoritative snapshot —
deadline, verification level, tooling policy, and every allowance tagged `rules` or `one-shift` —
written before arming and archived with the receipt at clock-out.

When the prompt is incomplete or Guided, composition asks exactly one question, prefilled from
`shift-policy.sh … defaults-get`: *"Same as last time: `<profile>`, `<hours>h`, `<toolingPolicy>`,
`<no elevation | allowances …>`? Yes, or change."* A change answer may name a new profile, hour
count, or tooling policy, and elevation in words — *"allow docker tonight"* becomes a one-shift
allowance in the shift policy; *"always allow docker here"* becomes a permanent `rules.json`
allowance, written while the shift is unarmed. The same question folds in the permission
preflight's gaps (`ns preflight-needs` against every selected item and Hunt order): *"Items
4 and 7 need `containers`: allow tonight, allow always, or leave them parked?"* Composition writes
the resolved policy with `shift-policy.sh … set --from-json -` before any compose, cut, or arm;
review-first writes nothing else, and run-direct arms immediately once it lands. Start never asks:
it consumes a queued policy, or arms with safe defaults when none was queued. A complete Automatic
prompt skips the question and writes those same safe defaults, plus whatever the sentence granted.

## Arming a shift

Hunt and Quality start the shift themselves rather than printing another command for the owner to
run. Both follow Start's whole preflight first — the one-shift check, state and work-target
validation, stale run-control markers, deadline handling, rules, and unattended permissions — and
report unsupported permission modes before arming, never mid-shift: Claude Code without
`bypassPermissions` (or an allowlist covering the gates), and Codex without `-a never`. A contract
that does not commit arms under `-s workspace-write`; one that commits needs the launch command on
`references/hosts/codex.md`, because under Codex's `workspace-write` sandbox `.git` is protected.
Warn and proceed.

Only then: cut the whole work order out of `work-orders.md`, put the item under `## Items`, write
the deadline, arm the gate, log the start, run the binding probe, classify the Codex session
identity, and arm the host's watchman. The marker is what starts the shift — without it the list
is written and nothing holds it. Unsupported or malformed identities refuse as Start requires;
never resume them. Hunt and Quality carry the exact commands.

## One shift contract

Any combination becomes one ordered work order, one punch list, one branch or artifact work target, one deadline where
required, and one set of receipts. In repository mode those receipts are work-target commits. In artifact mode they are files under `.nightshift/receipts/`. Never arm a separate shift per entry. The catalog entry remains
the definition of done; selection and launch modes decide who chooses it and whether discovery
pauses for approval.

A GitHub issue hunt cannot grow past the imported `Status: proposed` set the owner already
staged. Direct mode may rank inside that set; it must not search GitHub or add issues that were
not imported.
