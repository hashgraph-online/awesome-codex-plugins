# Krypton

Current version: `0.3.2`

[![skills.sh](https://skills.sh/b/jturntdev/krypton)](https://skills.sh/jturntdev/krypton)

Stop AI agents from shipping plausible wrong work.

Krypton is the goal-based planning and proof gate for running Claude Code,
Codex, and other AI coding agents against production-grade codebases.

The failure mode Krypton is built for is not bad syntax. It is the right-looking
feature that compiles while living on the wrong layer, inventing a second source
of truth, skipping cutover, or claiming success without proof from the real path.

Krypton forces the plan before the code:

- truth owner
- contract boundary
- displaced path
- cutover decision
- acceptance evidence
- review gates

Built for `/goals`, equivalent goal-based agent workflows, Claude Code
skills/plugins, Codex skills, and operators who need agent speed without letting
the codebase rot.

## What's Included

- **New beta: VPS Codex setup** (`krypton-vps-codex-app`): a guided workflow for
  using a Linux VPS as the remote machine for Codex App work, including VPS
  readiness questions, SSH aliases, GitHub repo access, local config choices,
  Codex CLI auth, port forwarding, and proof checks.
- **Krypton planning** (`krypton-planning`): turns a request into a goal package
  with the truth owner, boundary, cutover decision, task plan, review gates, and
  acceptance evidence.
- **Krypton execution** (`krypton-execution`): keeps an approved plan on track
  while the main agent implements, verifies, and records proof.
- **GitHub Action beta**: checks pull requests for the goal-package evidence
  Krypton expects before non-trivial code changes ship.

Jump to: [Install](#install) | [Skills And Beta Workflows](#skills-and-beta-workflows) |
[VPS Setup Workflow Beta](#vps-setup-workflow-beta) |
[GitHub Action Beta](#github-action-beta)

## Why Operators Need It

Modern agents can create weeks of architectural debt in one enthusiastic
session. Krypton turns "build this" into an operational contract before the
agent touches code:

- what product or engineering outcome the work serves
- what current behavior is replaced, redirected, deleted, or demoted
- who owns the truth
- what contract crosses the boundary
- what evidence proves the result from the target person's perspective
- what kill criteria prevent duplicate paths from living forever

That contract is what lets an operator keep using agents on production systems
without letting the codebase become a pile of current-looking alternatives.

## Designed For `/goals`

Krypton is best used with `/goals` or any equivalent goal-based agent workflow.
It is not meant to be a one-shot "please implement this" prompt.

The planning session creates the durable handoff:

```text
docs/goals/<goal-slug>/PLAN.md
docs/goals/<goal-slug>/GOAL.md
docs/goals/<goal-slug>/EVIDENCE.md
```

`PLAN.md` is the source plan. `GOAL.md` is the compact `/goal` prompt.
`EVIDENCE.md` is where execution records the actual proof from the real command,
artifact, payload, browser state, trace, or operator-visible result. Start the
execution session with the GOAL prompt, then load `krypton-execution` so the
main agent preserves the plan's ownership, cutover, review, and evidence gates.

If your harness does not have `/goals`, paste the contents of `GOAL.md` into a
fresh Codex or Claude session. The shape still works.

## Install

### Recommended: skills.sh

Use the open skills CLI when you want Krypton installed into supported agent
skill directories:

Codex only:

```bash
npx --yes skills add jturntdev/krypton --skill '*' --agent codex --copy -y
```

Claude Code only:

```bash
npx --yes skills add jturntdev/krypton --skill '*' --agent claude-code --copy -y
```

That installs every Krypton skill for the named agent only. If you want Codex,
Claude Code, OpenCode, or another agent together, run the command without
`--agent ...` and use the interactive selector:

```bash
npx --yes skills add jturntdev/krypton
```

See the package page:

```text
https://skills.sh/jturntdev/krypton
```

### Codex Repo Marketplace

This repo ships a Codex marketplace file at `.agents/plugins/marketplace.json`.
For Codex clients that support repo marketplaces:

```bash
codex plugin marketplace add \
  "https://github.com/jturntdev/krypton.git" \
  --ref "main" \
  --sparse ".agents/plugins" \
  --sparse ".codex-plugin" \
  --sparse "assets" \
  --sparse "skills"

codex plugin install krypton --source krypton
```

### Claude Code Plugin

Use the plugin route when you want Claude Code to manage Krypton as a plugin:

```text
/plugin marketplace add jturntdev/krypton
/plugin install krypton@krypton-dev
/reload-plugins
```

Claude Code namespaces plugin skills, so invoke them as:

```text
/krypton:krypton-planning
/krypton:krypton-execution
```

This repo includes the Claude plugin files Claude Code expects:

```text
.claude-plugin/plugin.json
.claude-plugin/marketplace.json
skills/krypton-planning/SKILL.md
skills/krypton-execution/SKILL.md
```

### Claude Code Manual Skills

Use manual install when you want the skills available as personal Claude Code
skills without the plugin marketplace:

```bash
git clone https://github.com/jturntdev/krypton.git
mkdir -p ~/.claude/skills
cp -R krypton/skills/krypton-planning ~/.claude/skills/
cp -R krypton/skills/krypton-execution ~/.claude/skills/
```

Manual personal skills invoke without a plugin namespace:

```text
/krypton-planning
/krypton-execution
```

### Codex

For Codex skills:

```bash
git clone https://github.com/jturntdev/krypton.git
mkdir -p ~/.codex/skills
cp -R krypton/skills/* ~/.codex/skills/
```

## Skills And Beta Workflows

Stable skills:

- `krypton-planning`: turn a request into an outcome contract, architecture
  slice, task plan, evidence gate, and `/goal` handoff prompt.
- `krypton-execution`: execute an approved plan without drifting from ownership,
  cutover, or proof requirements.

Beta workflow:

- `krypton-vps-codex-app` beta: guide a user through setting up a Linux VPS as
  a Codex App SSH host, including VPS provisioning questions, SSH aliases,
  GitHub repo access, local config choices, Codex CLI auth, port forwarding,
  and proof checks.

The beta workflow points at where Krypton is going: not just plans and review
gates, but repeatable operator workflows that help a user move from local
agent work to durable remote development without hiding the security,
credential, and proof decisions.

## How It Works

1. Load `krypton-planning` with a feature request, bug, refactor, migration, or
   architecture goal.
2. The agent produces a goal package:

```text
docs/goals/<goal-slug>/PLAN.md
docs/goals/<goal-slug>/GOAL.md
docs/goals/<goal-slug>/EVIDENCE.md
```

3. `PLAN.md` is the full implementation plan. `GOAL.md` is the short `/goal`
   prompt or handoff prompt for the next session.
4. Paste or run the `GOAL.md` prompt in Codex or Claude.
5. Pair it with `krypton-execution` when you want the main agent to use the same
   ownership, cutover, review, and evidence discipline.
6. Finish only when the acceptance evidence is captured from the real route,
   artifact, payload, trace, browser state, or operator-visible output and
   recorded in `EVIDENCE.md`.

The workflow is intentionally two-stage:

```text
rough request
  -> krypton-planning
  -> PLAN.md + GOAL.md + EVIDENCE.md
  -> /goal handoff
  -> krypton-execution
  -> main-agent implementation + review gates + acceptance evidence
```

## GitHub Action Beta

Krypton also ships a reusable PR gate, but treat it as beta until you have
tested it in a throwaway repo that matches your workflow. The primary install
path is still the `skills.sh` command above.

The gate fails non-trivial code changes that do not include a changed Krypton
goal package with:

- `PLAN.md`
- `GOAL.md`
- `EVIDENCE.md`
- truth owner text
- deletion or cutover text
- evidence gate and acceptance evidence text

Beta workflow example:

```yaml
name: Krypton Goal Gate

on:
  pull_request:

permissions:
  contents: read

jobs:
  krypton:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          fetch-depth: 0
      - uses: jturntdev/krypton@v0.3.2
```

Run the same gate locally:

```bash
python3 scripts/check-krypton-goal.py --base-ref origin/main
```

Goal package templates live in:

```text
templates/goal-package/
```

Before relying on the Action in a real repo, test three cases in a throwaway
repository:

- code change with no goal package should fail
- docs-only change should pass
- code change with `PLAN.md`, `GOAL.md`, and `EVIDENCE.md` should pass

## VPS Setup Workflow Beta

Krypton also includes a clearly marked beta Codex App remote-development setup
workflow:
`krypton-vps-codex-app`.

Use it when you want a VPS to be the machine that does the work while Codex App
on your Mac or Windows machine connects over SSH. The VPS owns the repo,
toolchain, builds, tests, tmux/cmux sessions, dev servers, and Codex CLI auth.

This is beta because VPS providers, Codex App remote connections, GitHub access
choices, and project setup commands vary by operator. The goal is for Krypton to
become the clean setup lane: Codex asks the right questions, explains the safest
default, waits for user-owned steps, runs only approved setup or audit commands,
and finishes with proof from the real remote project.

The skill is intentionally consent-based. Codex should ask before each
operator-owned decision:

- whether the user already has a VPS or still needs to provision one
- whether Codex may edit `~/.ssh/config` or should only show the snippet
- whether GitHub should be the source of truth for the VPS checkout
- which GitHub access path to use: GitHub CLI login, account SSH key, read-only
  deploy key, public HTTPS clone, or no GitHub setup yet
- whether local config should be recreated from examples, copied selectively, or
  skipped
- whether Codex should only audit or may bootstrap tools over SSH

GitHub is the recommended code path. Local-only config and secrets are a
separate step. The skill tells Codex not to bulk-copy `.ssh`, `.codex`, browser
profiles, home directories, caches, `node_modules`, build outputs, private keys,
or random dotfiles.

Read the beta setup guide:

```text
docs/vps-codex-app-beta.md
```

The skill includes a read-only audit script:

```bash
skills/krypton-vps-codex-app/scripts/audit-vps-codex-app.sh \
  --host krypton-vps \
  --repo-url git@github.com:ORG/REPO.git \
  --repo-path ~/src/REPO
```

Passing the audit proves the SSH host prerequisites. It does not replace the
final Codex App remote-thread proof.

## Agent Roles

Krypton works best when the harness supports named agents:

- `explorer`: read-only source-of-truth and architecture mapping
- `plan-reviewer`: PRE and POST alignment checks
- `reviewer`: runtime correctness, security, and evidence check
- `maintainer`: codebase-shape, duplication, and cutover-debt check
- `verifier`: focused proof from the real path

See `docs/required-roles.md` for the role expectations. If your harness does
not support named agents, the main agent can still follow the same gates, but
independent exploration and review will be weaker.

## Prompt Files

Krypton keeps prompt templates individual instead of centralizing them into one
large prompt file. Each skill owns the prompts it actually uses:

- `skills/krypton-planning/plan-reviewer-prompt.md`
- `skills/krypton-execution/post-plan-reviewer-prompt.md`
- `skills/krypton-execution/reviewer-prompt.md`
- `skills/krypton-execution/maintainer-prompt.md`

## Example

Bad agent path:

```text
"Add sentiment to the dashboard."
```

The agent adds frontend-only sentiment logic and calls it done.

Krypton path:

```text
Truth owner: market intelligence producer
Contract boundary: typed sentiment payload
Cutover: dashboard reads producer output only
Evidence: API response plus browser state showing the real payload
```

See `examples/` and `tests/pressure-scenarios/` for more.

## Status

This is the first public cut. It is intentionally small: three skills,
individual prompt templates, agent role expectations, goal package templates, a
local gate script, beta GitHub Action and VPS setup workflows, examples,
pressure scenarios, and validation scripts.

## Versioning

Krypton uses SemVer-style versions while the public package stabilizes.

- Version source of truth: `VERSION`
- Plugin metadata must match: `.codex-plugin/plugin.json`,
  `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`
- Release tags should use `vX.Y.Z`

Version policy:

- Patch: README, examples, prompt wording, metadata, validation improvements
- Minor: new skills, new gates, changed `/goal` workflow shape
- Major: breaking skill names, removed gates, incompatible plan or goal format

## Development

Run:

```bash
./scripts/validate.sh
```

The validator checks required files, skill metadata, JSON plugin metadata, and
public-safety issues such as placeholders or private project references.

## License

MIT
