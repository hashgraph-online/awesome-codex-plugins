# Espresso

![Espresso](https://raw.githubusercontent.com/mirkobozzetto/espresso/main/espresso-hero.jpeg)

**Less filler. Less unnecessary context. Right-sized delegation.**

Lightweight workflows for Claude Code, Codex, OMP and Pi. Keep explanations,
evidence and useful code comments, without repetitive reminders or automatic
changes to your global settings.

## Where the savings come from

| Mechanism | What it changes | What we can honestly claim |
|---|---|---|
| No ordinary-prompt reminders | Removes Espresso's repeated reminder payload | Eliminates that input overhead compared with Espresso 1.x; total session savings are unmeasured |
| Concise policy | Asks for direct answers and the smallest correct change | Aims to reduce unnecessary prose and code; output length and quality remain model-dependent |
| Optional RTK | Filters supported command output before it enters context | Can reduce tool-output volume; RTK reports bytes removed and estimated tokens, not total session or subscription savings |
| Model ladder | Sends suitable bounded work to a lower model tier | Changes which model does the work, not the number of tokens; delegation adds overhead and is not a quota-saving guarantee |

Espresso does not enlarge the context window or erase existing history.
Its policy also occupies context. We have verified the integrations, not measured
an end-to-end token reduction. There is no universal savings percentage.

RTK is **off by default** in the OMP/Pi extension. The integration only considers
simple `git status` and `git log --oneline` commands with a small flag allowlist.
Diffs, tests, patch logs and scripts stay untouched. Missing RTK or a failed
rewrite leaves the original command intact. Existing RTK hooks are independent.
See [RTK's measurement definition](https://github.com/rtk-ai/rtk/blob/develop/docs/guide/analytics/gain.md).

## Smaller code: optional Ponytail

[Ponytail](https://github.com/DietrichGebert/ponytail) is a separate, optional
companion for avoiding over-engineering: reuse existing code, prefer the standard
library and native platform features, and avoid speculative abstractions.
Espresso neither bundles nor installs it automatically.

Its authors' [agentic benchmark](https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-06-18-agentic.md)
reports less code and fewer tokens on 12 feature tasks with Haiku 4.5, four runs
per task and condition. Gains are largest where custom code can be replaced by
native features, and small or absent where the implementation is already minimal.
These are Ponytail's results, not Espresso measurements or evidence for Astra/Sol.
The authors also warn that reasoning overhead can increase cost on GPT-5.5.

Use it to reduce unnecessary implementation, not to chase the fewest lines.
Shorter code is not automatically better code; validation, error handling,
security and accessibility must remain intact.

## Harness support

| Harness | Policy | Delegation |
|---|---|---|
| Claude Code | SessionStart hook and skill | Automatic ladder for unpinned generic Claude workers |
| Codex | Trusted SessionStart hook and skill | Explicit named GPT agents |
| OMP | Extension and skill | Named GPT agents and an explicit text-only worker |
| Pi | Extension and skill | Explicit text-only worker; core Pi has no subagent tool |

GPT tiers: **Astra → Sol → Terra → Luna**, with Luna as the floor.
Named agents are `espresso-sol`, `espresso-terra` and `espresso-luna`.
OMP workers use the subscription provider `openai-codex`; Codex agents inherit
their provider. The OMP/Pi text worker checks model availability on the same
provider before launching. Explicit model choices and specialist agents are
preserved. Keep consequential review on the parent model; do not delegate trivial
work or spawn workers without authorization.

## Install

Node.js is required for hooks and the adapter installer.

**Claude Code** (run each command separately):
```text
/plugin marketplace add mirkobozzetto/espresso
/plugin install espresso@espresso
```

**Codex**:
```sh
codex plugin marketplace add mirkobozzetto/espresso
codex plugin add espresso@espresso
```
Review and trust the hooks in Codex before starting a new thread.

**Pi**: `pi install git:github.com/mirkobozzetto/espresso`

**OMP**, or named GPT agents for Codex, from a permanent checkout:
```sh
git clone https://github.com/mirkobozzetto/espresso.git
cd espresso
node src/hooks/install.js omp --apply
```

For Codex's named GPT agents, run `node src/hooks/install.js codex --apply`.
Pi can alternatively use `node src/hooks/install.js pi --apply` for the extension
and skill. Omit `--apply` to preview adapter files. Conflicting files are refused;
settings, credentials and model overrides are untouched. Restart the harness.
Keep this checkout in place when using a local extension reference.

See [INSTALL.md](INSTALL.md) for upgrade and removal precautions. Existing
Caveman/Ponytail installations and old global rules are not deleted automatically.

## OMP / Pi commands

```text
/espresso status
/espresso on
/espresso off
/espresso ladder
/espresso worker Summarize this supplied text: ...
/espresso rtk-on
/espresso rtk-off
```

The worker launches the same CLI on a lower available tier, with no tools or
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
Instructions limit it to two lower-tier workers, no nested delegation, no edits,
and no trivial tasks. These are model instructions, not an enforced scheduler
or read-only sandbox. Explicit choices and stricter skill instructions win;
skills that require fresh consent may still ask. No workers run while idle.

[Anthropic’s research system](https://www.anthropic.com/engineering/multi-agent-research-system)
supports the usefulness of parallel independent research, not a token-saving
guarantee for Espresso or Astra. Espresso’s automatic policy still needs
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

Local checks covered reminder removal, absence of startup writes, explicit-model
preservation, installer idempotence and conflict refusal, toggles and selective
RTK rewriting. Real OMP and Pi text workers returned replies using the selected
Luna CLI configuration. Claude's manifest and direct hooks were checked; Codex's
plugin installation was checked in an isolated configuration. Full Claude/Codex
delegation sessions and comparative token/quality benchmarks were not run.

MIT License.
