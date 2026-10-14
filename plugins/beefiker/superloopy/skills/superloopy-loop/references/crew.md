# Crew

Load this reference before dispatching any subagent. When to use subagents, and that Superloopy never spawns, stay in `SKILL.md` under "Optional Subagent-Driven Mode".

## Parent agent responsibilities

- Keep the Superloopy plan and criteria as the source of truth.
- If the requested repository path differs from `cwd`, verify and state the exact target path before editing or dispatching workers.
- Allocate one bounded handoff card per worker: goal, criterion or slice, allowed files, active evidence root, report artifact target, validation command, non-goals, and expected status values.
- Avoid parallel executors on overlapping files. Parallelize read-heavy review, QA, and summarization lanes first.
- In full crew mode, the implementation worker must own a real bounded implementation slice before the parent edits or completes that slice. If there is no safe independent implementation slice, stay solo or use a smaller read-only crew instead of pretending an implementer lane ran.
- Wait for worker summaries, then record only artifact-backed proof with `superloopy loop prove`, `superloopy loop evidence`, `superloopy loop review`, or `superloopy loop checkpoint`.
- Summarize worker output by status, claim, changed files, commands, artifacts, risks, and next action. Do not paste raw transcripts into the main thread unless they are the evidence.
- After each worker finishes, show the user a concise role completion line with the role, normalized verdict, artifact path, and next action before closing or respawning that lane.
- For full crew, record each dispatch with `superloopy loop handoff --agent <name> --assignment <text> [--verdict <v>] [--artifact <path>]` and run `superloopy loop fleet --json` before the final gate. The fleet output normalizes the workers' APPROVE/PASS/REJECT-style verdicts into one accept/reject/needs-context enum and lists outstanding workers. An accepted verdict requires a valid artifact under the active evidence root. A lifecycle verdict (`working`/`in_progress`/`running`) stays outstanding; an unresolved verdict (`inconclusive`/`timeout`/`ack_only`) normalizes to needs-context and is NEVER counted as accept. Rejected and needs-context lanes appear in `attention`. Known crew lanes may print one original completion line for terminal verdicts, choosing the user's language from the assignment or scoped brief when it matches the supported catalog (`en`, `ko`, `ja`, `zh`, `es`, `fr`, `de`, `it`, `pt`, `id`, `hi`, `tr`, `vi`, `ru`, `ar`, `th`), but the line is presentation only; artifacts, normalized verdicts, `attention`, and `outstanding` remain authoritative. Use `--language <tag>` or `SUPERLOOPY_CREW_LANGUAGE=<tag>` only when the prompt language cannot be inferred. Set `SUPERLOOPY_MAX_PARALLEL` for a soft over-dispatch warning. Handoffs are parent-side bookkeeping only — they never spawn or complete.
- Before the final summary, run untracked-aware status commands such as `git status --short --untracked-files=all` and `git ls-files --others --exclude-standard` so new evidence, scripts, and reports are not omitted from the diff review.

### Dispatch contract (self-contained)

Because role-by-name routing is unverified, each spawn message must stand alone — paste the role's requirements into it rather than relying on the agent name. Lead with an imperative `TASK:` and name the rest:

- `TASK:` the one bounded assignment (one criterion or one non-overlapping slice).
- `DELIVERABLE:` the report artifact path under the active evidence root, and the required receipt (`SUPERLOOPY_EVIDENCE` for workers; `SUPERLOOPY_AUDIT` for `assayer`; `pathfinder` writes none).
- `SCOPE:` allowed files, the active evidence root, the validation command, and explicit non-goals.
- `VERIFY:` the binary check that decides PASS/FAIL, run once after the slice's edits are complete rather than after every patch.
- Size the assignment to the lane's model profile: the `fast`-profile `pathfinder` gets one concrete lookup with named targets and the host's dedicated read/search tools; open-ended exploration and multi-step shell work go to `standard`/`deep` lanes.

State that it is an executable assignment, not a context handoff. Prefer a fresh, minimal context over a full-history fork so the child works the delegated task instead of continuing old parent state.

### Subagent lifecycle

- Treat a running child as alive, not as a timeout counter. For a long pass, have it emit `WORKING: <task> - <phase>`; reserve `BLOCKED: <reason>` for genuine stalls.
- Do not record a criterion pass, mark a dependent step done, or finish the loop while a live child still owns that step's evidence.
- A silent or ack-only child after follow-up is **inconclusive — never an approval or a pass**. Close the lane, record it as inconclusive, and respawn a smaller self-contained task with only the missing deliverable.

Agent allocation:

- `forge`: edits one criterion or independent slice, writes a report, and ends with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.
- `sentinel`: reviews diff, scope, and evidence; writes a report under the active evidence root; does not edit product files.
- `probe`: exercises happy-path, regression, and risk scenarios; writes artifact-backed QA evidence; does not edit product files.
- `arbiter`: integrates implementation, review, QA, audit, and criteria coverage; writes a final gate report such as `.superloopy/evidence/arbiter-final-gate-report.md`; the parent still runs Superloopy completion commands.
- `assayer`: read-only, skeptical evidence auditor; judges Superloopy's deterministic re-run against the scenario and ends with `SUPERLOOPY_AUDIT: <verdict-path>`. Installed by `superloopy agents install` alongside the workers.
- `pathfinder`: read-only codebase navigator; locates files and code and returns absolute paths with a direct answer. Writes no evidence and edits nothing — dispatch it first to scope a slice before assigning an executor. Parallelize it with review/QA lanes.
