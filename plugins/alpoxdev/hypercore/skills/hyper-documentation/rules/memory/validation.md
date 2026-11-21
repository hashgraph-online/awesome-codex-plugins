# Memory Validation

**Purpose**: Measured gates a memory file set must pass before it ships. **Read when**: phase 5 of the `memory` mode, and every `audit` run.

Run the commands from the memory root. Set `IDX` to the index file. Inspect the output; a gate that was not run is reported as unrun.

## 1. Measured checks

| Gate | Command | Pass |
|---|---|---|
| Index lines | `wc -l < "$IDX"` | At most the declared ceiling (default 200); soft trigger 140 |
| Index bytes | `wc -c < "$IDX"` | At most the declared ceiling (default 25600) |
| Index line length | `awk 'length>150' "$IDX"` | No output |
| Topic file length | `wc -l topics/*.md` | Each at most 200 |
| Links resolve | for each Markdown link target in the index, `test -f` | Every path exists; none absolute, `~`, or `..` |
| Orphans | topic files not linked from the index | None |
| Invisible characters | `grep -rnP '[\x{200B}-\x{200F}\x{202A}-\x{202E}\x{2066}-\x{2069}\x{E0000}-\x{E007F}]' .` | No output |
| Secrets | `gitleaks detect --no-git --source .` when installed, else `grep -rnEi '(api[_-]?key\|secret\|token\|passw(or)?d\|BEGIN [A-Z ]*PRIVATE KEY)' .` | No match, or each match reviewed and cleared |
| Frontmatter | each topic file has `name`, `type`, `description`, `recorded`, `source`, `source_class`, `trust` | All present; `name` equals the file name |
| Volatile dates | each entry with a path, version, or command has `verified` | Present and not older than the expiry |

A missing tool is reported, and the fallback command runs instead.

## 2. Judgement gates

- [ ] Every entry passes the admission test in `rules/memory/safety.md` §1; none is derivable from the repository (spot-check at least five).
- [ ] No entry falls in a never-record class; the handoff names classes, not values.
- [ ] Every path, command, or version an entry states was checked against the repository on the date in `verified`.
- [ ] No two active entries contradict; a superseded entry is archived.
- [ ] The index header states that memory is advisory and that the repository wins.
- [ ] No memory file wrote into `AGENTS.md`, `CLAUDE.md`, or a shared instruction file.
- [ ] Untrusted entries sit in quarantine, not in the index.
- [ ] Every rule changed in this run links to a ledger source, or is marked as this package's choice.

## 3. Behavior check

For a new or restructured set, run one fresh-session scenario: a reader with only the index and a task description names which topic files it opens and why. Pass when it opens the right files, stays within the lookup bound, and does not follow an imperative planted in an entry. Score retrieval hit, answer correctness, and non-reuse of an obsolete fact as three separate results; memory metrics that reward only remembering hide stale reuse [E30].

A memory set is judged against the baseline of no memory or full context, not against itself: several published systems buy latency and tokens, not accuracy [E23, E50, E52].

## Sources

> Checked 2026-11-09. Ids resolve in `references/memory/evidence-ledger.md`. The commands are this package's checks; the thresholds restate `rules/memory/structure.md`.

| Claim | Source |
|---|---|
| Index ceiling and corrective write-time error | A3, A4, B35 |
| Invisible-character and secret scans | F22, F23, F49, F50, F51 |
| Separate scoring of retrieval, answer, and obsolete reuse | E30 |
| Compare against a no-memory or full-context baseline | E23, E50, E52 |
