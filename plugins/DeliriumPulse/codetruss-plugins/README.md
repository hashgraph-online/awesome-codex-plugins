# CodeTruss agent plugins

CodeTruss is the deterministic first-pass verification gate for AI-written code.
This repository is the open wrapper that puts that gate inside Claude Code and
Codex: a skill that teaches the agent to operate the separately installed
CodeTruss CLI, bind each task to an approved file boundary, run the repository's
own verification commands, and read the signed receipt the CLI writes for every
change. The analysis is deterministic and runs on the developer's machine, the
receipt records exactly what ran and what did not, and anyone can re-verify a
receipt offline. Nothing here calls a model, uploads source, or scores a repo by
vibes.

The wrappers contain no analyzer, no bundled hook, no MCP server, and no upload
path. They invoke the separately installed CLI, keep deterministic analysis
local, and require explicit consent before installation, provider-backed `--llm`
review, authentication, or receipt `sync`.

## Install for Claude Code

Inside a Claude Code session:

```text
/plugin marketplace add DeliriumPulse/codetruss-plugins
/plugin install codetruss@codetruss
```

Or from a shell:

```bash
claude plugin marketplace add DeliriumPulse/codetruss-plugins
claude plugin install codetruss@codetruss
```

Then ask Claude to `Set up CodeTruss for this repository`. The skill proposes an
allow/deny boundary and verification commands, waits for your confirmation, and
runs the CLI's own guided `codetruss setup` with `--hooks claude` so the tested
CLI installer owns hook installation. From then on the gate runs on the agent's
lifecycle events and writes a receipt per session.

The owned marketplace is live now. CodeTruss is not currently listed in
Anthropic's reviewed community catalog or its separately curated official
marketplace.

## Prerequisites

- Git
- Node.js 20.9 or newer
- CodeTruss CLI v0.2.35 or newer from <https://codetruss.com/cli>

Skill instructions in this repository are verified against the shipped CLI
v0.2.35. The skill can explain the official installer when the CLI is missing,
but it must not install software without the developer's confirmation.

## What a receipt looks like

Verbatim excerpt from `codetruss report latest` after a review where the agent
also touched a denied path and committed a live key:

```markdown
# CodeTruss receipt — FAILED

- **Session:** `20260807T051345990Z-4f2f16`
- **Task:** Add a SESSION_TTL constant to src/auth.ts
- **Starting commit:** `14482ad37ea1f3ea5c9547071b58c3cdffb7c0b0`
- **Policy SHA-256:** `d13f4367129bb7683c486d4d4e8e876bc1e9a7f541cd0e539945743b16d95a03`

## Verdict: FAILED

- 1 high/critical security or dependency finding(s) affect changed files
- 1 file(s) changed in denied paths: infra/deploy.sh
- 1 file(s) changed outside approved scope: .codetruss.yml
- sensitive surfaces changed: .codetruss.yml (policy)

## Changed files (3)

| Path | Change | Scope | Sensitive | Lines |
|---|---|---|---|---:|
| `.codetruss.yml` | added | unexpected | policy | +5/−0 |
| `infra/deploy.sh` | added | denied | — | +3/−0 |
| `src/auth.ts` | modified | allowed | — | +1/−0 |

## Introduced or worsened analyzer findings (1)

| Severity | Analyzer | Location | Finding |
|---|---|---|---|
| HIGH | secrets | `infra/deploy.sh:2` | Possible Stripe live secret key committed in deploy.sh |

## Analysis profile

Profile: `local-registry-v2`.

The 13 deterministic registry analyzers ran locally on this machine, plus a local
security pass: the shared SAST engine — the same rules and the same
source-to-sink taint tracking as the hosted audit — over the JavaScript,
TypeScript and TSX in this repository.

### What the local security pass checked

- **SQL injection (CWE-89).** Untrusted input tracked from request sources
  through string building into query execution.
- **Mass assignment (CWE-915).** A raw request body spread into a database
  write, and write helpers whose payload type accepts arbitrary keys.
- **Un-awaited database writes, swallowed errors, coercion-prone `==`
  comparisons, and N+1 queries in loops** — the defect classes coding agents
  most often introduce.

### What did not run

- **The rest of the security rule pack.** Command injection, code injection,
  path traversal, SSRF, open redirect, XSS and insecure deserialization were
  **not** checked here. Those rules run in a hosted scan; absence of a finding
  in those classes means they were not analyzed, not that the code is clean.
- **Non-JavaScript languages.** The local pass covers JavaScript, TypeScript and
  TSX only. Python, Go, Java, C#, PHP, Ruby and Rust in this repository received
  secret scanning and the other registry passes, but no security rule or taint
  analysis.
- **Hosted symbol graph.** No cross-file call or data-flow graph was built, so
  architecture and dead-code conclusions cover only what the local passes can
  see in isolation.
- **Optional LLM review.** No model read this diff. It is opt-in via `--llm` and
  is force-disabled under agent hooks, so a hook receipt is always deterministic
  evidence only.
- **Hosted Health scores.** Not calculated, reported as **N/A**. The scores are
  defined over the graph and the complete SAST pass; a number derived from this
  pass set would overstate what ran.

Local security findings are reported for review and do not fail the verdict on
their own.
```

`codetruss verify latest` re-checks the signature over those bytes and prints
`verified 20260807T051345990Z-4f2f16 (FAILED)`.

## What runs where

Local and deterministic, with no account and no network required:

- the 13 registry analyzers listed in the receipt's analysis profile;
- since CLI v0.2.35, a security pass running the shared SAST engine and its
  source-to-sink taint tracking over the repository's JavaScript, TypeScript and
  TSX: SQL injection, mass assignment, un-awaited database writes, swallowed
  errors, coercion-prone `==`, and N+1 queries in loops;
- scope classification of every changed file against the approved allow/deny
  boundary, including untracked and sensitive-surface detection;
- secret detection on changed files;
- the repository's own verification commands, executed against a fresh
  materialization of the final Git tree;
- receipt signing and offline `codetruss verify`.

Hosted, and only when the developer explicitly asks for it:

- the rest of the security rule pack — command injection, code injection, path
  traversal, SSRF, open redirect, XSS, insecure deserialization — and every
  non-JavaScript language;
- the cross-file symbol graph, which together with the full rule pack backs the
  full-codebase audit and the Health scores;
- receipt `sync` to a CodeTruss account.

A local receipt names its own remaining gaps in its "What did not run" section,
and local security findings are `REVIEW_REQUIRED` at most — they never fail a
verdict on their own. Optional provider-backed `--llm` review is force-disabled
under agent hooks, so a hook receipt is always deterministic evidence only.

Measured behaviour on public repositories is published at
<https://codetruss.com/benchmark>. CLI downloads, checksums, and the SBOM are at
<https://codetruss.com/cli>.

## Codex

```bash
codex plugin marketplace add DeliriumPulse/codetruss-plugins
codex plugin add codetruss@codetruss
```

The owned marketplace is live now. CodeTruss is not currently listed in
OpenAI's public Plugin Directory.

## Agent Skills clients

Install the same canonical skill for both Claude Code and Codex with the public
Agent Skills installer:

```bash
npx --yes skills add DeliriumPulse/codetruss-plugins \
  --skill codetruss --agent claude-code codex -y
```

For an immutable install, pin the most recent published release:

```bash
npx --yes skills add \
  https://github.com/DeliriumPulse/codetruss-plugins/tree/v0.1.5 \
  --skill codetruss --agent claude-code codex -y
```

The skill is indexed at
<https://skills.sh/DeliriumPulse/codetruss-plugins/codetruss>. Review the skill
before use; it can invoke the separately installed CLI with the agent's local
permissions.

## What the skill does

- proposes a narrow repository allow/deny policy and verification commands;
- runs guided `codetruss setup` only after the developer confirms the boundary,
  hook target, and exact verification-command trust;
- installs and diagnoses the existing Claude Code or Codex lifecycle hook;
- reviews working-tree or staged changes and interprets the resulting receipt;
- treats exit codes 1 and 2 as product verdicts with valid evidence, not generic
  shell failures;
- refuses to weaken policy merely to manufacture a green verdict.

The canonical Agent Skills definition is in `skills/codetruss/`. Platform
packages contain byte-identical copies so each marketplace archive is
self-contained.

## Development

```bash
npm test
claude plugin validate . --strict
claude plugin validate ./plugins/codetruss-claude --strict
python3 /path/to/plugin-creator/scripts/validate_plugin.py ./plugins/codetruss
npm run release:verify
```

`npm test` uses only Node.js built-ins and verifies manifests, marketplace
entries, skill parity, and privacy guardrails.
`npm run release:verify` builds the OpenAI and Claude plugin archives twice
from the committed Git tree and proves their bytes are reproducible.

## Security and support

Read [SECURITY.md](SECURITY.md) before reporting a vulnerability. General
wrapper issues belong in this repository; CLI issues belong in the
[CodeTruss CLI tracker](https://github.com/DeliriumPulse/codetruss-cli/issues).
Never attach third-party source, credentials, or unredacted receipts to a public
issue.

## Licensing boundary

The manifests and skill instructions in this repository are MIT licensed. The
separately installed CodeTruss CLI is free to use under the CodeTruss CLI
Proprietary License and CodeTruss Terms of Service. This repository does not
make the CLI open source and does not redistribute its executable bundle.
