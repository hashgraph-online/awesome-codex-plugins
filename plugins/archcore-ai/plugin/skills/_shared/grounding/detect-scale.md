# Scale Detection

## What it detects

SCALE is how large and structurally subdivided a codebase is, expressed as a tier — `small` / `medium` / `large` — that selects how deep the init seed goes (consumed by `SKILL.md` Step 0.5 to branch the bootstrap flow). It is a function of two pieces of evidence the repo actually contains: how many cohesive top-level units (domains) its source splits into, and how many substantial source modules exist — independent of language, framework, or domain (web, ML, embedded, games, data/IaC, mobile, in-house frameworks). The numeric thresholds below are fixed and universal; only the recognition that *feeds* them must generalize to any stack.

## How to find it (any codebase)

1. **Compute the two counts from evidence.** Derive `domain_count` via the universal `detect-domains.md` method (cohesive top-level source units) and `module_count` via `detect-modules.md` (substantial non-test source files > 100 LOC), using its dominant-extension + manifest-declared logic — this works in any language. Also compute `entry_point_count` (per `detect-entry-points.md`); it is informational and **not** part of classification.
2. **Never default to `small` on a miss.** If both counts resolve to ~0 yet Step 0(b) proved source exists, recompute: take the dominant *non-config* file extension actually present (whatever it is — `.f90`, `.sv`, `.tla`, `.proto`, an engine's script type), enumerate cohesive top-level source directories directly, and as a last resort gauge breadth from total tracked source-file count and top-level directory count.
3. **Guard against distortion.** Example / demo / generated / vendored workspaces must not inflate `domain_count` (false-large); an unfamiliar language or non-mainstream layout must not pin the repo to the minimal seed (false-small). Escalate above `small` only on positive evidence of real breadth — widen the *inputs*, never the thresholds.
4. **Classify** against the fixed table (evaluate top-to-bottom, first match wins; rows are written so every `(domain_count, module_count)` pair matches exactly one row):

| Mode       | Condition                                            |
| ---------- | ---------------------------------------------------- |
| **small**  | `domain_count ≤ 1` AND `module_count ≤ 15`           |
| **medium** | `domain_count ≤ 2` AND `module_count ≤ 40`           |
| **large**  | otherwise (`domain_count ≥ 3` OR `module_count > 40`) |

Worked: `(1,10)` → small · `(2,10)` → medium · `(1,30)` → medium · `(2,45)` → large · `(5,10)` → large.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

**Conventional roots (priority order — prefer the earlier when several exist; monorepo roots outrank `src/`):**

1. `apps/`, `packages/`, `services/` — monorepo / microservice workspaces (each subdir is a candidate domain).
2. `internal/`, `pkg/` — Go packages (each subdir a domain); `cmd/` subdirs are entry points, not domains.
3. `src/`, `app/` — most common single-root / Rails / Next.js App Router conventions.
4. `modules/`, `domains/`, `lib/`.
5. Repo root (fallback) — if nothing above exists, enumerate top-level source directories directly.

**Utility names that do NOT count as domains** (even when cohesive): `utils`/`helpers`, `common`/`shared`/`core`, `types`/`constants`/`config`, `test`/`tests`/`__tests__`/`fixtures`, `vendor`/`node_modules`/`dist`/`build`/`out`/`target`/`coverage`, `generated`/`__generated__`, `docs`/`examples`/`scripts`. `lib/` is ambiguous — sole top-level dir → single-domain repo; alongside other qualifying dirs → exclude as utility.

**Border cases:**

- **One real app + empty `packages/`**: effective `domain_count` = 1 — don't let an empty workspace bump the tier.
- **Giant single-domain library** (one `src/`, 60 modules): module-count triggers `large`; team may `--mode=medium` if large-mode noise is unhelpful.
- **Only stubs** (subdirs of < 50 LOC files): `domain_count` = 0, low `module_count` → small.
- **Flat repo, no conventional root**: enumerate top-level source files directly; `domain_count` = 0, classify by `module_count` alone.

## Override

User may force a mode with `--mode=small|medium|large` on the bootstrap invocation. When overridden, Step 0.5 announces both the detected mode and the forced mode, e.g.:

> Mode: medium (forced, detected=small). Override with `--mode=X` or drop the flag to auto-detect.
