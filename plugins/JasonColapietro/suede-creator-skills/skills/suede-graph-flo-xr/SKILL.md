---
name: suede-graph-flo-xr
description: "Use when asked \"compare implementation plans before building\" for one multi-file repository change. Suede AI runs Suede Thought Graph shipping search: it searches, scores, prunes and refutes plans, selects one winner, then builds in an isolated worktree with a sandboxed gate and handoff. Halts on hazards, collisions or exhausted budget. NOT FOR: bulk worker tasks, existing-diff review (use suede-code), CI wiring (use suede-ci-gate), or copy-only work (use suede-ship-copy)."
metadata:
  display-name: "Suede AI Graph Flo XR Skills"
---

# Suede AI Graph Flo XR Skills

Use the bundled `workflows/suede-graph-flo-xr.js` workflow to search competing plans for
one multi-file repository change. It makes an evidence-backed selection before
any implementation lane mutates the worktree.

## Compatibility

Bundled execution requires Claude Code Workflow on macOS, sandbox-exec, Node.js, Git and the six registered agent profiles. Other hosts can read the orchestration contract but must use direct implementation rather than claim Workflow execution.

## Intake and budget gate

Before launch, require all three inputs:

- **Repo**: an absolute repository path. Relative paths and `~` fail closed.
- **Scope**: the requested multi-file change, including any protected paths or
  constraints.
- **Budget**: `light`, `standard`, or `deep`.

Also detect and pass optional context when available: `deploys` (whether the
repo has a deploy surface), `liveUrl` (the read-only production surface), and
`vault` (the external decision/handoff context path). Their absence does not
block a non-deploying repository, but do not silently discard known values.

When the user names a model for the workers (`workerModel`: `sonnet`, `opus`,
`haiku`, or `fable`), pass it: every worker call then runs on that model while
orchestration stays on the session model. Omitted, workers inherit the session
model silently; if the session sits on an expensive model and the user did not
choose it for workers, say so before launch instead of letting the default
decide. A run can spend up to 200 worker calls, so an unchosen inherited model
is a cost decision nobody made.

If repo or scope is missing, halt. Report the missing input in one line, offer
to provide the repo path, describe the desired change, or route a one-file edit
to direct implementation, then wait for the user's choice.

State the selected range and projected worst-case calls before launching:
`light` projects and permits **55**, `standard` projects and permits **110**, and
`deep` projects and permits **200** total agent calls. Do not infer a budget from
scope or silently raise a ceiling. If the user has not chosen one, ask and wait.

## Runtime prerequisites

The bundled JavaScript workflow is a Claude Code workflow for macOS. It requires
`sandbox-exec` and the six registered `suede-graph-flo-xr-*` agent profiles. Install the
full `suede-skills` plugin, the `suede-agent-workflows` plugin, or use this
repository's `install.sh`, which copies the profiles into `~/.claude/agents`.

Claude Workflow exposes no Node `process` global, so the workflow cannot infer
its package namespace. The calling skill must derive it from how this skill was
invoked and pass it on every launch. When the invoked name carries a plugin
prefix, `agentNamespace` is that prefix verbatim: `suede-skills` from the full
plugin, `suede-agent-workflows` from the focused orchestration plugin. A bare
invoked name with no prefix, installed by `install.sh` or copied by hand, takes
the empty string. This is runtime context, not a user choice. A missing or
unknown value fails before the first agent call.

The workflow also cannot locate its own bundled helper scripts. Pass `helperDir`:
the absolute path of the invoked skill's `workflows/helpers` directory (for this
install, `<skill base directory>/workflows/helpers`). The clamped Bash commands
run these `.cjs` helpers: the per-spawn clamp cannot verify a rule that is
multi-line or longer than roughly 400 characters, so inline `node -e` payloads
are not usable. A missing or whitespace-containing path fails before the first
agent call; a missing helper file surfaces as the Scout setup failure.
Payload-carrying helper invocations are admitted by pinned prefixes (helper
path plus worktree, temp root, or base SHA) rather than exact strings; each
helper validates its remaining argv, and the diff attestations, not the clamp,
remain the check that what was applied matches the selected bundle.

The selected patch reaches the applier as bounded base64 chunks staged into the
run's private temp root, because the clamp verifier cannot parse a command
carrying a multi-kilobyte inline payload. Each append carries its offset and an
FNV-1a checksum, and `--apply` verifies total length and payload checksum before
decoding, so a mistyped chunk fails fast with a retry instruction instead of
producing a corrupt patch.

A skill-folder-only install, a generic skills-CLI install, and the Codex plugin do
not by themselves register or execute Claude Workflow agent profiles. In those
environments, treat this file as the orchestration contract and route the change
to direct implementation; do not claim the bundled workflow ran. To enable it in
Claude Code after a manual single-skill copy, also copy the skill's bundled
`agents/suede-graph-flo-xr-*.md` files into `~/.claude/agents` and restart Claude Code.

The requested Scout setup command probes `/usr/bin/sandbox-exec` as its first
subprocess, before fetch or worktree creation. If that command is invoked and
the probe fails, Scout reports failure before its setup mutation. The returned
Scout evidence is still a model attestation, not a host execution receipt. Gate
also holds on any later reported sandbox rejection. Never retry an acceptance
command outside the sandbox to turn that hold into a pass.

## Run the graph search

Invoke:

```js
Workflow({
  scriptPath: "skills/suede-graph-flo-xr/workflows/suede-graph-flo-xr.js",
  args: { repo, scope, agentBudget, agentNamespace, helperDir, workerModel, deploys, liveUrl, vault }
})
```

The workflow executes these operations in dependency order:

1. **Generate** independent implementation plans from the scout and research
   evidence.
2. **Score** each plan for coverage, evidence, feasibility, safety, and
   efficiency.
3. **KeepBestN** deterministically prunes the scored beam.
4. **Refute** attacks the surviving plans with evidence-backed objections.
5. **Improve** repairs plans whose refutations are not fatal.
6. **Aggregate** combines compatible surviving lanes without merging conflicting
   file ownership.
7. **Select** chooses one deterministic winner.

Only the plan selected by **Select** may mutate files. Rejected, pruned, and
unselected thoughts remain evidence only; never build them speculatively.

## Boundaries

The workflow halts before the next agent call or entire mutating batch when its
budget is exhausted; it does not undo mutations that completed earlier. It
halts before any mutation unless an independent read-only verifier confirms a
clean, registered origin/main worktree at one direct `${REPO}.worktrees/ship-*`
child with the same Git common directory and non-symlink candidate files whose
realpaths remain inside it. Case-folded or Unicode-normalized path aliases fail
closed before graph search. It also halts for
a tracked secret, a live target worktree, a protected-WIP collision, a duplicate
file owner, an overflowed safety manifest, or no selectable plan. Scout parses
NUL-delimited Git porcelain so both sides of renames remain protected, parses
`lsof -Fn` CWD fields with path-component boundaries, and never discards fresh
dirty or live claims merely because committed history was cherry-landed. A
selected Build or Fix result that is blocked, missing context, fails, or reports
no changed path also halts before the next verification stage; a result that is
done with stated concerns proceeds, and its concerns travel into the review
stage and the handoff. Patch authors receive the whole scope checklist as
contract context, so a name another lane pins is imported, not guessed. On a halt, name the
blocker in one line and offer 2–4 applicable
resolutions (for example: narrow scope, exempt protected WIP, resolve the
collision, choose a higher budget, or provide missing context), and wait. Do
not relaunch or mutate while halted.

### Reading a search halt

An empty search used to report `no safe graph winner` however it ended, so an
infrastructure flake and a genuine evidence conflict printed the same line. The
halt output now names which happened, and `haltDetail` carries the counts behind it:

| Reason | What it means |
|---|---|
| `every candidate lost its score to an agent failure` | No thought in the run was ever scored. Infrastructure, not evidence: rerun. |
| `no candidate reached Select` | The search emptied upstream for some other reason; read `graph.dropped`. |
| `every finalist lost its score before Select` | Finalists existed and were pruned as unscored. |
| `every finalist was pruned before Select` | Finalists were pruned for a non-score reason. |
| `every finalist carries a degraded or missing score` | Finalists reached Select without a valid score. |
| `every finalist failed deterministic plan eligibility` | Real rejection. `haltDetail.eligibilityRejections` lists every reason. |
| `no safe graph winner` | None of the above fits: read the graph. |

`haltDetail.infrastructureDegraded` is independent of the reason: both can be
true at once. Read the reason for what stopped Select and that flag for what
degraded the pool feeding it.

Score calls are read-only and idempotent, so a transport-level death is retried:
twice per call, capped run-wide at 5% of the agent ceiling, and refused entirely
once the remaining budget falls to the reserved floor (20% of the ceiling). A
malformed score is never retried: the schema is enforced at the tool layer, so
an invalid score is a judgment to keep, not a connection to redial. Every
attempt and every refused retry lands in `graph.scoreRetries`, and
`scoreReliability` rides out in the result on every run, halted or not: a flake
that costs two finalists still degrades a run that goes on to ship.

Claude's registered agent profiles enforce tool separation: local readers have
no shell, write, or web tools; public-web readers have no local-file or shell
tools; patch authors have no mutation tools; and appliers/verifiers have only
Bash plus structured output. Patch authors return unified diffs, one clamped
applier applies them, and a separately budget-reserved clamped verifier compares
the exact path set and diff digest immediately after every Build or Fix Apply,
before any reader or Gate call. Patch validation rejects symlinks, gitlinks,
binary patches, renames, copies, and file-type transitions before Apply. Gate
runs only allowlisted local validation
commands under macOS `sandbox-exec`, with no network, host reads limited to
runtime/system roots, the worktree, its `.git` common directory derived again
inside the exact Gate clamp, and the run's private temp root. The model-reported
common directory is never interpolated into sandbox permissions. Writes are limited to known generated artifacts
and that private temp root. The allowlist includes bounded project-local checks
for Node, Python, Go, Rust, Make, Swift Package Manager, Xcode simulator builds
with derived data under the private temp root, and offline Gradle validation.
Nested module `build` roots are derived only from selected files under that
module's `src` tree and are rejected if a symlink or realpath can escape the
worktree. A second diff attestation runs after Gate and hashes
the binary Git diff plus every reported file's mode, size, and bytes, including
untracked additions.

Gate removes credential-like and interpreter-injection environment variables,
then redirects home, temporary, and cache paths before an acceptance command
starts. If a check depends on removed credentials, report it as unverified;
never rerun it outside the sandbox merely to obtain a pass.

A successfully applied blocker patch is not treated as semantically cleared.
The original blocker remains in `fixedBlockersPendingVerification`. The Gate
attempt records its exact command set and reported output, but it cannot prove
those commands ran because the Workflow API exposes no trusted required-tool
execution receipt. The workflow therefore sets `claimedPassed` from the agent
report, forces `passed:false`, sets `gateVerified:false`, and keeps the verdict
and handoff status at `hold`. Only a trusted outer runner with immutable
execution receipts can promote that evidence.

These controls have a precise trust boundary. `bashCommandClamp` constrains a
Bash command when an agent invokes it; Claude Workflow does not provide a
required-tool-call receipt, so a structured verifier response remains a model
attestation rather than cryptographic proof that Bash ran. Likewise,
`authority`, `allowedRepo`, `allowedFiles`, and `allowedCommands` are audit
metadata, not filesystem permissions. Local reader tools are separated from web
tools but are not path-sandboxed by the Workflow API. Report these facts in any
security-sensitive handoff and do not describe the result as host-certified.

Production inspection is read-only. This skill never deploys, publishes,
releases, pushes, merges, changes credentials, deletes or reverts protected
work, or claims live verification. It does not choose the user's budget or
decide that missing scope can be skipped. Its ship verdict is evidence for the
user, not authority to perform an external action.

## Handoff and completion

Read the workflow's returned `runKey`, the validated unique `ship-<UUID>` leaf
from its isolated worktree. On a completed run, use the returned handoff
markdown. On a post-Scout halt, write a factual halt handoff from the structured
result and graph trace without spending another agent call; include any Build
or Fix lanes that completed before the halt. If Scout returns an invalid path
before `runKey` validation, report the halt without writing a run-keyed
handoff. Otherwise, save it to
`.suede-graph-flo-xr/${runKey}/handoff.md` at the target repo root, then verify it exists:

```bash
test -f ".suede-graph-flo-xr/${runKey}/handoff.md"
```

Report that path, the selected plan if any, gate result, changed files, commands
run, and explicit caveats. A completed local graph does not prove a deployment.

## License file

Part of `workflows/suede-graph-flo-xr.js` is distributed under BSD-3-Clause
terms carried in `LICENSE.graph-of-thoughts-BSD.txt`. Keep that file with every
source or binary redistribution of the workflow.

## Routing

- High-volume, well-specified, independent worker tasks → a separate private
  worker-fleet pass.
- Review or grade an existing diff → `suede-code`.
- CI, required checks, or branch-protection wiring → `suede-ci-gate`.
- Copy-only search and publication readiness → `suede-ship-copy`.
- From `suede-code`, `suede-ci-gate`, or `suede-ship-copy`: route a
  multi-file implementation-plan search with one
  selected mutating winner back to `suede-graph-flo-xr`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
