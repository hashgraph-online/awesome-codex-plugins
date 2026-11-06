---
name: suede-code
description: "Use when explicitly asked \"review this PR\" or to grade a diff, branch, or commit range. Suede AI returns evidence-backed P0-P3 findings, fix paths and an A-F ship grade; supports findings-only, grade-only and fix modes, seven review lanes, security checks, deploy safety and commit dirt. NOT FOR: automatic CI enforcement (use suede-ci-gate), agent evaluations (use suede-ai-eval), implementation-plan search (use suede-graph-flo-xr), or parallel fix coordination (use suede-agent-teams)."
metadata:
  display-name: "Suede AI Code Skills"
---

# Suede AI Code Skills

One skill for judging code: what is wrong, and whether it ships. Every finding
has a file, evidence, and a fix path. Every grade has the evidence that earned
it. No finding without evidence; no volume without signal.

**Runs only when asked.** Never fire this as a side effect of a diff, a save,
or a commit.

## Compatibility

An agent with repository read access and Git; Bash is needed for local tests and the bundled commit-dirt scan. Fix mode additionally needs authorized file edits. Review can proceed with explicitly unverified runtime checks when execution is unavailable.

## Gate policy: advisory, not blocking

Every check, grade, and ship verdict here is a recommendation to the user, not
a control on the agent.

- Run every check and report results honestly. `ship`, `ship-with-caveats`,
  `hold`, letter grades, and BLOCKED items are advice attached to the work.
- Never block, delay, skip, or rewrite the action the user asked for because a
  gate said hold. A failed gate changes what you report, never what you do.
- Single exception: an extreme-risk finding (data loss, credential exposure,
  legal or rights violation, payment mistake, irreversible public damage).
  Pause, state the risk and the options, and let the user pick. Their choice
  is final.

## Pick the mode

| Request sounds like | Mode | Emits |
|---|---|---|
| "review and grade", "is this safe to ship", "check this PR" | **full** (default) | Findings, grade, deploy safety, commit dirt, ship gate |
| "findings only", "no grade", "line by line", "find the bugs" | **`--findings-only`** | Findings, deploy safety, commit dirt, ship gate. No letters. |
| "grade only", "give it a letter", "A-F verdict", "should this merge" | **`--grade-only`** | Lane grades, caps, required upgrades, ship gate. No findings list. |

Grade-only still runs Step 1 (Instant-F) and still reads the code. It skips
the itemized findings output, not the investigation.

Other modes that combine with any of the above:

- **Plan review:** nothing built yet; check scope, sequencing, acceptance
  criteria, test mapping, and missing decisions.
- **Fix verification:** after fixes, rescan only the changed files and confirm
  each original finding is gone.
- **Release review:** add build, secrets, env, public copy, screenshots,
  metadata, and live or API readback.
- **`--fix`:** apply fixes (see Fix Mode).
- **`--threat-verify`:** confirm declared threat-model mitigations exist.
  Procedure in `references/threat-verify.md`; read it only in this mode.

**Depth** (state it at the top of every output):

- `--quick` (about 2 min): pattern scan for obvious bugs, secrets, missing null
  checks, injection, broken error handling. No cross-file analysis.
- `--standard` (default, about 10 min): per-file correctness on changed paths,
  language traps, state handling, test coverage of changed behavior, call graph
  within changed files, maintainability baseline.
- `--deep` (about 25 min): full import graph, call-chain tracing, whole-repo and
  history pass, critic lanes. Use for auth, payments, migrations, public APIs.

Model: Sonnet by default. Recommend Opus for auth, payments, and public API
surfaces.

## Pre-flight

Name three things before analysis:

- **Target:** repo, branch, PR, commit range, diff, route, API, or release build.
- **Intent:** what the change claims to do. Find the spec in this order: issue
  references in commits and PR body (`#123`, `Closes #45`), a path the caller
  passed, a matching file under `docs/` or `specs/`. If none exists, write
  "no spec available" and judge intent from the PR description alone. Never
  invent requirements.
- **Risk lanes:** frontend, backend, data, auth, payments, contracts, iOS,
  release, public copy, analytics, secrets, deployment, docs.

Pin the comparison point and prove it is reviewable: `git rev-parse <base>`
resolves, diff with three dots (`git diff <base>...HEAD`) so the comparison
runs against the merge-base, and the diff is non-empty. A bad ref or empty
diff fails here in one line.

## Context graph

Build it before judging the diff:

1. Changed files and generated files.
2. Imports, callers, routes, handlers, jobs, hooks, models, schemas, and
   config or env dependencies the change touches.
3. Tests, fixtures, migrations, release scripts, docs, and screenshots that
   should move with the behavior.
4. Runtime surfaces: local route, live URL, API endpoint, simulator flow,
   dashboard, store metadata, deploy target.
5. Domain contracts: ownership, rights and provenance, payments and wallets,
   agent commerce, and published-statement accuracy.

Flag beyond-the-diff risk when related files, defaults, docs, env, or deploy
requirements no longer agree.

## Run the repo's own gates first

Do not hand-review what a tool already decides. Detect what the repo ships
(`package.json` scripts, config files, lockfiles) and run only that. Never add
a tool the repo does not use. Never report a result you did not run.

| Stack | Type check | Lint | Test | Other |
|---|---|---|---|---|
| Web / Node | `npx tsc --noEmit` | `npm run lint` (changed files) | `npm test` | `npm audit` when deps changed |
| MCP server (Node) | `node --check <server>.mjs` | configured linter | repo MCP tests | One stdio session: `initialize`, `notifications/initialized`, then list/call/read/get |
| iOS / Swift | the build is the check | SwiftLint if configured | XCTest target | `xcodebuild -scheme X -destination 'platform=iOS Simulator,name=<device>' build` |
| API / backend | compile step if any | configured linter | contract or schema tests | OpenAPI validation against the live route |

Severity mapping: a type error on a changed line is P2 (P1 on a critical
path); a failing test on changed behavior is P1; a test that silently stopped
running is P2; a reachable, exploitable dependency CVE is P0 or P1; a verified
live secret is P0; a broken production build in a release review is P0.

Cite command, exit status, and the file:line it implicates. A gate that cannot
run goes in Verification as "not run" with the reason.

**House rules bind.** Read `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`.editorconfig`, and formatter, linter, or review config. Do not flag what a
rule permits; do flag what it forbids. The nearest-ancestor rule wins for files
under its path. When the user dismisses a finding as deliberate, record it in
one line (pattern, why allowed, path scope) and do not raise it again.

## Step 1: Instant-F triggers (always first, every mode)

Any match is an automatic **F** and a P0 finding. Report file and line. Other
lanes cannot raise the grade.

- **Secrets:** hardcoded API key, token, or password in committed source; a
  committed private key or certificate; a signing secret outside a secret
  manager.
- **Injection:** SQL built by string concatenation with user input; shell
  command from user input via exec, spawn, or eval; unescaped user input
  rendered where XSS is reachable.
- **Auth bypass:** middleware with a skip path (early return, swallowed
  exception, always-true condition); a permission check a request param can
  bypass; JWT accepting `alg: none` or a hardcoded secret.
- **Payments and wallets:** a handler that swallows errors; a webhook with no
  signature verification; amount or recipient taken from untrusted input
  without server-side validation.
- **Data destruction:** a DROP or destructive ALTER with no rollback and no
  tested restore; bulk delete or update with no WHERE or a user-controlled
  WHERE; production cache wipes with no restore path.
- **Plaintext sensitive data:** passwords stored or logged in plaintext; PII
  sent to unencrypted logs or analytics; card, SSN, or health data in an
  unencrypted field.

## Step 2: Language and platform traps

Load only the sections that match the diff:

- `references/traps-web.md`: TypeScript, React, accessibility, Next.js, SEO
  impact, database (Drizzle, Prisma), performance and Core Web Vitals.
- `references/traps-swift-ios.md`: Swift, SwiftUI, and client-server contract
  drift for iOS.
- `references/maintainability-baseline.md`: twelve structural checks for
  `--standard` and `--deep`, diff-scoped and always labeled as judgment.

## Step 3: Security baseline

Runs automatically when the diff touches `auth/`, `api/`, `middleware/`,
`routes/`, `pages/api/`, or imports crypto, session, or payment modules. Cite
the category in each finding using the **OWASP Top 10:2025** numbering: A01
Broken Access Control (now includes SSRF), A02 Security Misconfiguration, A03
Software Supply Chain Failures, A04 Cryptographic Failures, A05 Injection, A06
Insecure Design, A07 Authentication Failures, A08 Software or Data Integrity
Failures, A09 Security Logging and Alerting Failures, A10 Mishandling of
Exceptional Conditions. API and mobile changes also map to the OWASP API
Security Top 10 (2023) and MASVS. What counts as a finding per category is in
`references/security-baselines.md`.

**Observability delta** (any new handler, endpoint, job, cron, or consumer):
flag `catch` blocks that only `console.error` or swallow silently; new paths
with no log on entry or failure; React subtrees with no error boundary; new DB,
external API, or model calls with no timing or trace span; analytics events
the old code fired and the new code dropped; background jobs that finish
without logging count, duration, or failure reason.

## Step 4: Deep pass (`--deep` only)

- **Reverse dependencies:** find every caller of a changed function, type,
  route, or constant across the repo. Name the call sites you checked.
- **Shared assumptions:** for a changed schema, env var, default, or
  invariant, find other places that assume the old value.
- **History:** `git log -L` or `git blame` the touched lines. A change that
  reintroduces a previously fixed shape is a regression; cite the prior commit.
- **Sibling pattern:** compare to the nearest analog (other handlers, other
  migrations). A lone handler skipping the shared auth wrapper is P1 even if
  it works.
- **Critic lanes** for auth, payments, migrations, or public APIs: a change
  mapper, runtime critic, security critic, product critic, and test critic,
  each reporting separately. Collect consensus. If a high-severity concern
  survives a fix cycle, keep `hold` and name the smallest next check.

A whole-repo claim with no named symbols is not evidence.

## Step 5: Intent and scope

- **Claim vs diff:** map each acceptance criterion to a code path or test.
  Claimed behavior with no matching change is a P1 truth gap.
- **Scope creep:** flag unrelated refactors, bundled dependency bumps, and
  formatting sweeps that bury the change. Recommend a split.
- **Effort signal:** state files and net lines changed and rate the review
  effort: trivial, moderate, heavy, or too large to review safely.
- **Walkthrough** (four or more files): a table of file, what changed, risk
  lane. Add a mermaid `sequenceDiagram` or `flowchart` only when data crosses
  three or more boundaries or an async, auth, or payment path changes.

## Step 6: Grade (full and `--grade-only`)

For full and grade-only modes, read [the complete grading contract](references/grading-contract.md) before assigning a grade. It defines all seven lanes, letter meanings, gate mapping, surface caps and debt weighting. An Instant-F or deploy-safety result still applies in every mode; never assign a letter from impression.

## Step 7: Deploy safety (every mode, every run)

Rate each `pass | conditional | block`:

- **Breaking changes:** a public API, schema, config key, or interface changes
  with no versioned migration or fallback → block.
- **Rollback safety:** `git revert` cannot undo it (migrations, sent email,
  charges, deletes, storage writes, queue publishes) → block.
- **Blast radius:** state it as `~0%` (flagged), `~partial` (one flow), or
  `~100%` (shared middleware, auth, hot query).
- **Environment readiness:** a required env var, secret, or flag is not in
  production yet → block.
- **Dependency changes:** new dependency with a known CVE, or unpinned in
  production → block.
- **Data mutations:** irreversible writes with no tested restore → block.
- **Security delta:** improved, neutral, or new attack surface without
  mitigation → block.
- **Automation coverage:** no CI covering the changed surface, or required
  checks not enforced on the default branch, in a production-connected repo →
  block.

## Step 8: Commit dirt (every mode, every run)

Run the bundled scanner from the target repo instead of eyeballing:
`bash <skill-dir>/scripts/commit-dirt-scan.sh main...HEAD`, or pipe a diff
with `-`. It is read-only and always exits 0. Confirm each hit against the
diff before reporting. If it cannot run, check every added line by hand.

Seven categories: secrets and credentials; debug artifacts; conflict markers;
staged build output (`node_modules/`, `.next/`, `dist/`, `.DS_Store`, logs);
WIP breadcrumbs (`DO NOT MERGE`, `TEMP:`, lorem ipsum); oversized or binary
blobs over 500 KB; exposed internals (internal hosts, staging URLs, personal
emails). Rate each `clean | suspicious | dirty`. Overall **DIRTY** is a P0
finding and moves the gate to `hold`. **SUSPICIOUS** is named for the reviewer
to confirm.

## Findings: format and precision

Lead with findings by severity. Group a repeated pattern once ("appears in 4
files: ..."). If a structural defect exists, report it first and alone, and
hold the line-level findings it governs as deferred.

P0 and P1 use the full block:

```
[P0] path/to/file.ts:142
Issue: JWT secret falls back to empty string; any token is valid when SECRET is unset.
Fix: process.env.JWT_SECRET ?? (() => { throw new Error('JWT_SECRET required') })()
Verify: set JWT_SECRET="" and curl /api/me: expect 401, currently 200.
OWASP: A04:2025 Cryptographic Failures
Confidence: high
```

P2 and P3 get one line each:

```
[P2] components/Feed.tsx:88, index used as key on .map(); use item.id.
```

**Severity:** P0 data loss, security exposure, payment loss, broken release,
or unsafe public behavior. P1 likely production regression, auth bug, broken
primary path, false published statement, missing deploy requirement. P2
real edge-case failure, incomplete state, test gap on changed behavior. P3
low-risk cleanup. A concern that cannot be tied to a file, route, command, or
behavior goes under Open Questions.

**Confidence is observable:** `high` = reproduced, traced across the call
graph, or tied to a named failing input; `medium` = read, not executed;
`low` = looks wrong, nothing proves it. Label every P0 and P1. A low-confidence
security suspicion keeps its severity with the label attached; low-confidence
style notes collapse into one "nitpicks" line.

**Before emitting, cut** anything with no file:line and fix, anything a gate
already reports, and anything that would not change the ship decision or earn
a human reviewer's comment.

## Fix mode (`--fix` or an explicit request)

1. Auto-apply local P2 and P3 fixes (single file, no contract change), one
   commit per finding ID.
2. Present P0 and P1 as fix briefs first: failing behavior and evidence, files
   to open, expected change, acceptance criteria, verification command, WIP to
   preserve. Never auto-apply to auth, payment, or migration code without
   explicit confirmation.
3. Re-run the relevant mode on changed files and mark each finding resolved or
   escalated.
4. Stop after 3 cycles on the same finding and escalate it as a design issue.

## Suede-specific checks

Auth and session behavior across app, API, native shells, and server ·
rights, provenance, licensing, royalty, and agent-commerce claims match
implemented behavior · payment, wallet, x402, checkout, and credit flows fail
closed · public pages invent no metrics, pricing, partners, testimonials, or
release promises · deploy and account assumptions match local guidance before
production claims · store screenshots, metadata, and privacy answers match the
app · migrations, env, flags, cron, queues, webhooks, and secrets are
documented · contracts do not drift across web, backend, mobile, and docs.

## Red flags: stop

- "CI is green, so it's fine." CI that never exercised the change is not
  evidence.
- "The diff is small." Small diffs touch auth too. Step 1, 7, and 8 run every
  time.
- "I wrote this, I know it works." Switch to review mode and hunt what your
  implementation would miss.
- "The PR description explains it." Review the diff, not the story about it.
- "It was hard work, round up to B." Effort never moves a grade; evidence does.
- "Flag everything to be safe." Volume is noise. Run the precision cut.

## Output

Open with **Simple explanation**: one plain paragraph a ten-year-old can follow
covering whether it passed and the single biggest reason. Then, by mode:

```text
Depth:
Findings            (full, --findings-only)
Code Grade          (full, --grade-only: 7 lanes + overall, cap applied, why, required upgrades)
Deploy Safety       (all modes: 8 dimensions + SAFE TO DEPLOY | DEPLOY WITH CONDITIONS | DO NOT DEPLOY)
Commit Dirt         (all modes: 7 categories + CLEAN | SUSPICIOUS | DIRTY)
Open Questions
Verification        (checked / not checked, with commands and exit codes)
SHIP GATE: hold | ship-with-caveats | ship: [one sentence naming the blocker or caveat]
```

For no findings, say so and name residual risk or unrun checks. To revise a
grade, name what changed. Silence means accepted.

Worked examples, read only when calibrating: `references/worked-example.md`
(a full pass on a real file) and `references/worked-example-grade-only.md`
(lane arithmetic in grade-only mode).

## Boundaries

- Preserve user and other-agent WIP. Never stage, revert, or rewrite unrelated
  files. Apply fixes only under Fix Mode.
- Never invent tests, screenshots, live checks, deploy status, or gate results.
- Never auto-apply fixes to auth, payment, or migration code without
  confirmation.
- A style choice no rule, formatter, or real cost governs is not a finding.

## Routing

- Make CI enforce the verdict on every merge → **suede-ci-gate**
- The diff ships LLM, RAG, or agent behavior with no eval coverage →
  **suede-ai-eval**
- Several implementation plans need comparing before one multi-file change is
  built → **suede-graph-flo-xr**
- Fixes span several coordinated lanes → **suede-agent-teams**
- The same value is stated on two surfaces that can drift →
  **suede-parity-contract**

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
