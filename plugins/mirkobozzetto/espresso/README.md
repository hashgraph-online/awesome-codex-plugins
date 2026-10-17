# Espresso

![Espresso](https://raw.githubusercontent.com/mirkobozzetto/espresso/main/espresso-hero.jpeg)

**Less filler. Less unnecessary context. Same model, right effort.**

Lightweight workflows for Claude Code, Codex, OMP and Pi. Keep explanations,
evidence and useful code comments, without repetitive reminders or automatic
changes to your global settings.

## Where the savings come from

| Mechanism | What it changes | What we can honestly claim |
|---|---|---|
| No ordinary-prompt reminders | Removes Espresso's repeated reminder payload | Eliminates that input overhead compared with Espresso 1.x; total session savings are unmeasured |
| Concise policy | Asks for direct answers and the smallest correct change | Aims to reduce unnecessary prose and code; output length and quality remain model-dependent |
| Optional RTK | Filters supported command output before it enters context | Can reduce tool-output volume; RTK reports bytes removed and estimated tokens, not total session or subscription savings |
| Same-model delegation | Delegated agents keep the session model | Avoids the quality loss and retries of cheaper workers; each agent still pays its own startup context |

Espresso does not enlarge the context window or erase existing history.
Its policy also occupies context. We have verified the integrations, not measured
an end-to-end token reduction. There is no universal savings percentage.

RTK is **off by default** in the OMP/Pi extension. The integration only considers
simple `git status` and `git log --oneline` commands with a small flag allowlist.
Diffs, tests, patch logs and scripts stay untouched. Missing RTK or a failed
rewrite leaves the original command intact. Existing RTK hooks are independent.
Checked with RTK 0.51.0.
See [RTK's measurement definition](https://github.com/rtk-ai/rtk/blob/develop/docs/guide/analytics/gain.md).

## Smaller code: Ponytail included

Espresso bundles the real [Ponytail](https://github.com/DietrichGebert/ponytail)
4.13.0 runtime and all six upstream skills, with its MIT license and pinned
source commit in `ponytail-upstream.json`. No separate installation or startup
download is needed. It starts in **full** mode unless an existing Ponytail
configuration or `PONYTAIL_DEFAULT_MODE` overrides that default.

In OMP and Pi, **`/ponytail` opens a selector**: full, lite, ultra, off or status.
`/ponytail off` disables it for the session; `/ponytail default off` changes the
default for future sessions. Use `/ponytail default full` to restore it.
Headless commands show status instead of opening a menu. Claude/Codex use the
bundled skills and lifecycle hooks; they do not get the OMP/Pi native selector.

Also included: `ponytail-review`, `ponytail-audit`, `ponytail-gain`,
`ponytail-debt` and `ponytail-help`. Use their slash commands in OMP/Pi,
plugin skill commands in Claude, and skill invocation in Codex.
Espresso and Ponytail have independent switches. Avoid enabling a second,
standalone Ponytail extension alongside the bundled one.

Its authors' [agentic benchmark](https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-06-18-agentic.md)
reports less code and fewer tokens on 12 feature tasks with Haiku 4.5, four runs
per task and condition. Gains are largest where custom code can be replaced by
native features, and small or absent where the implementation is already minimal.
These are Ponytail's results, not Espresso measurements.
The authors also warn that reasoning overhead can increase cost on GPT-5.5.

Use it to reduce unnecessary implementation, not to chase the fewest lines.
Shorter code is not automatically better code; validation, error handling,
security and accessibility must remain intact.

## Harness support

| Harness | Policy | Delegation |
|---|---|---|
| Claude Code | SessionStart hook and skill | Read-only `espresso:scout` and native subagents, all on the session model |
| Codex | Trusted SessionStart hook and skill | Native agents on the session model |
| OMP | Extension and skill | Native agents and an explicit text-only worker |
| Pi | Extension and skill | Explicit text-only worker; core Pi has no subagent tool |

In Claude Code, Espresso ships one agent, `espresso:scout`: read-only (no edit
tools), on the session model (`model: inherit`), at medium effort, in the
background. Claude picks it for research whose raw output would flood the
conversation (multi-file search, flow tracing with GitNexus, docs, long logs),
and you keep talking with the main thread while it works. Below the prompt,
each running agent shows its model, effort and tokens.

Espresso no longer routes delegated work to a cheaper model. With a strong
session model, adding agents brings no gain or a loss on sequential coding
work ([260-configuration study](https://arxiv.org/abs/2512.08296)), and cheaper
workers can cost more per solved task once retries are counted. Delegate only
substantial read-only research or work whose output would flood the main
context; keep edits and consequential review on the main thread. Explicit model
choices and specialist agents are preserved.

In OMP/Pi, the text-only worker runs on the session model and follows the
session thinking level (low on OMP). Use `/espresso effort low|medium|high` to
set it for this session; `/espresso effort` and `/espresso status` report it.
This setting applies only to `/espresso worker`, not native named agents.
Before delegating, announce the agent, resolved model, effort and reason.

## Install

Node.js is required for hooks and the adapter installer. Restart the harness
after installing or updating.

| Harness | Install | Update |
|---|---|---|
| Claude Code | `claude plugin marketplace add mirkobozzetto/espresso`<br>`claude plugin install espresso@espresso` | `claude plugin marketplace update espresso`<br>`claude plugin update espresso@espresso` |
| Codex | `codex plugin marketplace add mirkobozzetto/espresso`<br>`codex plugin add espresso@espresso` | `codex plugin marketplace upgrade espresso`<br>`codex plugin add espresso@espresso` |
| Pi | `pi install npm:espresso-agent-tools` | `pi update` |
| Prime Agent | `prime-agent package install /path/to/espresso` (a checkout) | `git pull` in the checkout |
| OMP | `node src/hooks/install.js omp --apply` (from a checkout) | `git pull` in the checkout, then refresh the skill copies |

In Claude Code, the same commands work as `/plugin …` inside a session.

**Codex** runs plugin hooks only once you trust them. Review them in Codex
before starting a new thread, and again after an update: a changed hook gets a
new hash.

**Pi and Prime Agent** load the extension, the six Ponytail skills and the
Espresso skill from the package. Pi also accepts a checkout path
(`pi install /path/to/espresso`). Keep a checkout in place when you install
from it.

**OMP** needs a permanent checkout:
```sh
git clone https://github.com/mirkobozzetto/espresso.git
cd espresso
node src/hooks/install.js omp --apply
```
The OMP extension imports the checkout, so `git pull` updates it. The skills
are copies: the installer refuses to overwrite a copy that differs, so replace
`~/.omp/agent/skills/espresso` and `~/.omp/agent/skills/ponytail*` with the
checkout's `skills/` folders after pulling.

For Codex skills without the marketplace, run `node src/hooks/install.js codex --apply`.
Omit `--apply` to preview adapter files. Conflicting files are refused;
settings, credentials and model overrides are untouched.

See [INSTALL.md](INSTALL.md) for upgrade and removal precautions. Existing
Caveman/Ponytail installations and old global rules are not deleted automatically.

## OMP / Pi commands

```text
/espresso status
/espresso on
/espresso off
/espresso worker Summarize this supplied text: ...
/espresso rtk-on
/espresso rtk-off
```

The worker launches the same CLI on the session model, with no tools or
recursive extensions. It works only on the supplied text. State is per session:
concise policy starts on, RTK starts off. `off` stops new policy injection and RTK
rewriting; it cannot erase messages already sent to the model.

### OMP automatic research mode

`/espresso auto` enables standing authorization for substantial independent
read-only research. `/espresso manual` returns to explicit delegation;
`/espresso off` also clears automatic mode. These commands change session state.
The default is manual. A personal OMP wrapper can opt in on every startup by
calling the extension factory with `{auto: true}` as its second argument.
The installer refuses to overwrite such a customized wrapper.

The lead decides whether delegation is worthwhile after initial inspection.
Instructions limit it to two workers on the session model, no nested delegation, no edits,
and no trivial tasks. These are model instructions, not an enforced scheduler
or read-only sandbox. Explicit choices and stricter skill instructions win;
skills that require fresh consent may still ask. No workers run while idle.

[Anthropic’s research system](https://www.anthropic.com/engineering/multi-agent-research-system)
supports the usefulness of parallel independent research, not a token-saving
guarantee for Espresso. Espresso’s automatic policy still needs
task-level evaluation; command and policy-transition checks are not proof of
reliable delegation decisions.

### Arsenal and Ship compatibility

Arsenal owns skill selection and transitions. The selected skill owns approval
gates, solo flags, specialized agents, model assignments, output schemas,
artifact states, verification and commits. These take precedence over Espresso
recommendations. Espresso must not create a competing team or extra reviewer,
or use an external worker CLI to bypass a controlled runtime.

Ship currently asks before each delegation: automatic Espresso mode does not
remove that requirement. Likewise, `--no-agents` and solo mode remain solo.
Existing workflows do not require Espresso and are not rewritten by it.
This is instruction-level coexistence, not a verified end-to-end compatibility
claim for every Arsenal skill or harness.

## Verification scope

Local checks for 2.2.0: `claude plugin validate`, every Claude hook run
directly (per-project Ponytail modes, mode commands, visible status line,
silence on Codex), the OMP/Pi extension against a simulated host (string, array
and section prompts, same-model worker), selective RTK rewriting with RTK
0.51.0, and a Codex 0.160.1 install in an isolated configuration listing the
three bundled hooks. For 2.3.0: the scout agent passes `claude plugin
validate`, skips the Ponytail injection, and the agent status rows render from
sample input. How often Claude picks the scout on its own, and comparative
token/quality benchmarks, were not measured.

MIT License.
