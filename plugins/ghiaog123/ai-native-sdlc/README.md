# ai-sdlc

A six-stage software development lifecycle for coding agents, where every stage
commits one Markdown artifact and stops at a human gate.

Plan writes `intent.md` — the problem and the outcome, from an interview with
whoever asked. Design turns an accepted intent into `spec.md`. Build reviews and
then implements `plan.md`. Test runs the project's real checks and quotes their
output rather than claiming they passed. Deploy runs the review passes and posts
ranked findings for a human to approve. Maintain watches control bands and files
the next intent when one breaks.

Nothing here replaces judgment. Agents do the synthesis, the implementation, the
verification and the triage; a person decides what to build, what risk to accept
and what ships. Git records who asked, what the agent produced and who approved.

![A terminal session. A plan.md declares a typo fix low-risk on the fast path and lists README.md as the only file it changes. The artifact gate admits a write to README.md with exit 0, then blocks a write to REVIEW.md with exit 2, because a fast-path change cannot reach a path listed under Sensitive paths.](https://raw.githubusercontent.com/ghiaog123/ai-native-sdlc/main/docs/demo.gif)

A person called that change low-risk, so it skipped the intent and spec stages. Then the
agent reached for `REVIEW.md` — the file that defines what it may touch — and a hook
stopped it. A declaration buys fewer stages, never fewer boundaries.

![The six-stage loop: Plan writes intent.md, Design writes spec.md, Build writes plan.md, Test produces checks and evals, Deploy runs REVIEW.md, Maintain watches bands.yaml, and a control-band breach files the next intent.md to restart the loop. A human gate separates every stage.](https://raw.githubusercontent.com/ghiaog123/ai-native-sdlc/main/docs/loop.svg)

## Install

```
/plugin install ai-sdlc --marketplace ghiaog123/ai-native-sdlc
```

Then run `/ai-sdlc-init` in a repository to scaffold it.

## Usage

### Start a change

```
/sdlc-plan add rate limiting to the public API
```

Plan interviews you about the problem — what users cannot do today, who is affected,
what the constraints are — and writes `.sdlc/rate-limit/intent.md`. It stops there and
waits for you to accept it. It will not choose an architecture.

Then walk the stages. Each one reads the artifact the last one committed, writes its
own, and stops:

```
/sdlc-design     # accepted intent.md  ->  spec.md
/sdlc-build      # accepted spec.md    ->  reviewed plan.md, then code
/sdlc-test       # runs the project's real checks, quotes the output
/sdlc-deploy     # review passes, ranked findings, stops for your approval
/sdlc-maintain   # watches bands.yaml, files the next intent on a breach
```

### A low-risk change

A typo fix does not need an interview. Tell `/sdlc-plan` the change is low-risk and it
checks your `REVIEW.md` sensitive-path list, then hands the change straight to
`/sdlc-build` to enter at the plan. The stages are skipped; the gates are not.

If the change turns out to touch a sensitive path, the agent refuses the fast path, and
`artifact-gate.sh` refuses the write even if the agent tries anyway.

### Find out where everything stands

```
/ai-sdlc-status
```

One line per in-flight change: the furthest stage reached, whether its artifacts are
committed, and which person the next gate is waiting on.

### Set a repository up

```
/ai-sdlc-init
```

Creates `.sdlc/`, writes project memory from the repository's real build, test and lint
commands — `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex — and installs the
`REVIEW.md` and `bands.yaml` policy templates. Safe to re-run.

### Try the gate without installing anything

```bash
git clone https://github.com/ghiaog123/ai-native-sdlc
cd ai-native-sdlc
export GATE="$PWD/plugins/ai-sdlc/hooks/artifact-gate.sh"
source docs/demo-setup.sh
gate README.md    # exit 0, the plan covers it
gate REVIEW.md    # exit 2, the fast path cannot reach a sensitive path
```

That is the recording above, reproduced in a throwaway repository under `$TMPDIR`.

## What it installs

Eight skills: the six stages, plus `/ai-sdlc-init` to scaffold a repository and
`/ai-sdlc-status` to report which changes are waiting on which person.

Two read-only subagents: a pull-request reviewer that applies the project's
`REVIEW.md`, and a diagnostician that investigates a control-band breach without
touching production.

Four hooks, all of them inert unless the repository has a `.sdlc/` directory, so
installing this plugin changes nothing until a project opts in:

- `artifact-gate.sh` refuses a source write that no approved `plan.md` covers, and
  keeps a change declared low-risk away from governance-sensitive paths such as
  `CLAUDE.md`, `REVIEW.md` and CI workflow files.
- `prod-guard.sh` asks for explicit human authorization on deploy and teardown
  command shapes. It is a second, weaker line — IAM, branch protection and deploy
  approvals remain the real controls.
- `session-context.sh` and `prompt-nudge.sh` report where each in-flight change
  sits, derived from committed artifacts rather than stored state.

Templates for every artifact the loop produces, including `REVIEW.md` and
`bands.yaml`.

## What it intercepts, and why

This plugin registers hooks, so it sees tool calls. Here is every one of them.

| Hook | Fires on | What it does | Can it block? |
| --- | --- | --- | --- |
| `artifact-gate.sh` | `Write`, `Edit` | Reads the target path and the committed `plan.md` files under `.sdlc/`. Refuses a source write that no approved plan covers, and refuses any sensitive path while a fast-path change is active. | Yes |
| `prod-guard.sh` | `Bash` | Matches the command against known deploy and teardown shapes and asks for explicit human authorization before those run. | Yes |
| `session-context.sh` | Session start | Prints which changes are in flight and which gate each is waiting on. | No |
| `prompt-nudge.sh` | Prompt submit | Prints the same one-line status. | No |

All four read the repository and write nothing. They make no network calls. Every one
of them exits immediately unless the repository has a `.sdlc/` directory, so installing
this plugin changes nothing until a project opts in — and `.sdlc/OPTOUT` disables them
even then.

`prod-guard.sh` is a second, weaker line, not a sandbox. It matches command shapes and
can be rewritten around by someone who already has shell access and intends to. IAM,
RBAC, branch protection and deploy approvals remain the real controls. `SECURITY.md`
says the same thing, and says which bypasses are worth reporting.

### Agent permissions

Both subagents are read-only: `Read`, `Grep`, `Glob`, `Bash` — no `Write`, no `Edit`.
On Codex they additionally run under `sandbox_mode = "read-only"`.

They hold `Bash` because a reviewer that cannot run `git diff` and `git log` cannot
review a change. They never edit a file, approve a pull request, merge, or claim a
human gate has passed, and everything they read from a diff, a commit message or a
dependency name is treated as data rather than instructions.

## What it does not do

It never merges, never deploys, and never treats an agent's approval as a
person's. It will not bypass branch protection, and it cannot: the gates it adds
sit beside your existing controls rather than replacing them.

## Run the checks

```bash
bash hooks/test-artifact-gate.sh
bash hooks/test-sdlc-state.sh
```

## Both runtimes

The same source runs on Claude Code and on Codex. Agent definitions ship as `.md`
and `.toml` kept in step, and project memory is written to `CLAUDE.md` or
`AGENTS.md` from one template so the two cannot drift.

Requires bash, git and python3. Nothing else.

## Documentation and license

The method, the threat model behind each control, the metrics and how each one
gets gamed, and a three-phase rollout are documented in the project repository at
<https://github.com/ghiaog123/ai-native-sdlc>.

This implements the method described in Anthropic's AI-Native SDLC playbook. It
is an independent community implementation, not an Anthropic product, and is
neither affiliated with nor endorsed by Anthropic.

MIT licensed.
