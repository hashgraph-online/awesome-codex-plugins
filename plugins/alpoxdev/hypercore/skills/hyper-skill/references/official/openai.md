# OpenAI Official References for Skill-Maker

## Contents

- Refresh Policy
- Codex Agent Skills
- Codex Skill Discovery and Distribution
- Evaluating Skills
- API Skills
- AGENTS.md Guide
- Prompt Engineering
- Evaluation Best Practices
- Safety in Building Agents
- Sources

## Refresh Policy

- last_verified_at: 2026-11-03
- refresh_when:
  - Codex skills guidance changes materially
  - Codex skill discovery locations, the listing budget, or `agents/openai.yaml` change
  - AGENTS.md/custom instruction guidance changes materially
  - skill evaluation guidance changes in ways that affect validation rules
  - agent safety or tool-calling guidance changes in ways that affect skill safety gates
- supports_rules:
  - `rules/trigger-design.md`
  - `rules/skill-anatomy.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/context-and-harness-alignment.md`
  - `rules/validation-and-iteration.md`

## Codex Agent Skills

- source_url: https://learn.chatgpt.com/docs/build-skills
- last_verified_at: 2026-11-03
- applies_to: skill package shape, `name`/`description`, invocation, resources, scripts, progressive disclosure, the listing budget
- summary: A skill packages instructions, resources, and optional scripts, and its `SKILL.md` must
  include `name` and `description`. Explicit invocation is `@` in ChatGPT and `/skills` or `$` in Codex
  CLI and the IDE extension; implicit invocation happens when the task matches the `description`. In
  Codex the initial skill list uses **at most 2% of the model's context window, or 8,000 characters when
  the context window is unknown**, and `skills.max_context_tokens` sets a different budget **up to
  10,000 tokens**. If many skills are installed, Codex **shortens skill descriptions first**, and for
  large skill sets it **may omit some skills from the initial list and show a warning**. The budget
  applies only to the initial list; the full `SKILL.md` is still read once the skill is selected. Codex
  detects skill changes automatically and suggests a restart if an update does not appear. The page
  prefers instructions over scripts unless deterministic behavior or external tooling is needed.
- implication_for_hyper_skill: the failure mode is not only a truncated description but a skill that
  never appears, so the key trigger must lead the description and the description must stay short. The
  repository measurement lives under Sources in `rules/trigger-design.md`.

## Codex Skill Discovery and Distribution

- source_url: https://learn.chatgpt.com/docs/build-skills
- last_verified_at: 2026-11-03
- applies_to: where Codex finds skills, how to disable one, UI metadata, invocation policy, distribution
- summary: Codex scans `.agents/skills` in every directory from the current working directory up to the
  repository root, plus `$HOME/.agents/skills` (user), `/etc/codex/skills` (admin), and system skills
  bundled with Codex. **If two skills share the same `name`, Codex does not merge them; both can appear
  in skill selectors.** Codex follows symlinked skill folders to their target. `[[skills.config]]`
  entries in `~/.codex/config.toml` disable a skill without deleting it; when more than one entry matches
  a skill, the last matching entry wins. `[skills.bundled] enabled = false` in a trusted project's
  `.codex/config.toml` turns off bundled system skills for that project. `agents/openai.yaml` configures
  UI metadata (`interface`), invocation policy (`policy.allow_implicit_invocation`, default `true`; when
  `false`, implicit selection stops while explicit `$skill` invocation still works), and tool
  dependencies (`dependencies.tools`). For distribution beyond one setup, the page recommends packaging
  skills as a **plugin**. `$skill-installer` adds curated skills and `$skill-creator` walks a new skill
  through creation.
- implication_for_hyper_skill: a "reusable Codex skill folder" is only half the story. State the
  discovery locations, note that `.agents/skills` is shared with other runtimes, and treat plugins as the
  documented distribution path. `allow_implicit_invocation: false` is the Codex way to make a skill
  manual-only, and it is a runtime-only switch (SK-P-3).

## Evaluating Skills

- source_url: https://developers.openai.com/blog/eval-skills
- last_verified_at: 2026-11-03
- applies_to: trigger tests, process checks, output style checks, deterministic graders, the prompt-set size
- summary: Skill quality is evaluated with small prompt sets and observable checks across four axes -
  **outcome, process, style, and efficiency** ("did it get there without thrashing"). "A small set of
  10-20 prompts is enough to surface regressions and confirm improvements early", covering explicit,
  implicit, contextual, and negative-control invocations. `codex exec` is the automation path: it
  streams progress to stderr and writes only the final result to stdout. The post's example skill paths
  use the older `.codex/skills` locations; the build-skills page's `.agents/skills` locations win.
- implication_for_hyper_skill: the four axes and the invocation-mode split are the load-bearing parts;
  keep the case count as a starting recommendation rather than a validated optimum.

## API Skills

- source_url: https://developers.openai.com/api/docs/guides/tools-skills
- last_verified_at: 2026-11-03
- applies_to: skills uploaded through the OpenAI API, versioning, bundle limits, security posture
- summary: Uploaded skills use versioned bundles (`skill_reference.version` such as `"2"` or
  `"latest"`) and are compatible with the open Agent Skills standard. A bundle holds exactly one
  `SKILL.md`, at most 500 files, and has a 50 MB zip / 25 MB uncompressed-file limit. Skill instructions
  are user-prompt input, not system-prompt input. The page warns that skills "introduce security risks
  such as prompt injection-driven data exfiltration" and says to treat them as privileged code and
  instructions, and not to expose an open skills repository to end users.
- implication_for_hyper_skill: a skill is code plus instructions with real authority over planning and
  tool use, so the artifact audit and version pinning apply on this surface too.

## AGENTS.md Guide

- source_url: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- last_verified_at: 2026-06-02
- recheck_status: not re-read in the 2026-09-20 or 2026-11-03 passes - the date above is the last actual read
- applies_to: project instruction discovery, scope, precedence, local guidance layering
- summary: Repository instructions define scoped guidance for agents and should be considered when operating inside a project.
- implication_for_hyper_skill: Local `instructions/` and project rules outrank generic provider examples.

## Prompt Engineering

- source_url: https://developers.openai.com/api/docs/guides/prompt-engineering
- last_verified_at: 2026-06-02
- recheck_status: not re-read in the 2026-09-20 or 2026-11-03 passes - the date above is the last actual read
- applies_to: clear instructions, examples, structured context, explicit output formats
- summary: Clear instructions, examples, and explicit formatting improve followability.
- implication_for_hyper_skill: Core skill instructions should be explicit, example-backed, and contract-shaped.

## Evaluation Best Practices

- source_url: https://developers.openai.com/api/docs/guides/evaluation-best-practices
- last_verified_at: 2026-06-02
- recheck_status: not re-read in the 2026-09-20 or 2026-11-03 passes - the date above is the last actual read
- applies_to: AI system variability, eval-backed iteration
- summary: Model behavior varies, so production-facing behavior needs evaluations rather than intuition.
- implication_for_hyper_skill: Important skill changes should include at least a small eval or smoke set.

## Safety in Building Agents

- source_url: https://developers.openai.com/api/docs/guides/agent-builder-safety
- last_verified_at: 2026-06-02
- recheck_status: not re-read in the 2026-09-20 or 2026-11-03 passes - the date above is the last actual read
- applies_to: prompt injection, tool calling, MCP/tool safety, side-effect gates
- summary: Agent systems need safeguards around untrusted input, tools, permissions, and side effects.
- implication_for_hyper_skill: Skills that mention network, credentials, destructive actions, or production side effects must gate those actions explicitly.

## Sources

> Checked 2026-11-03 for the rows marked "yes". `developers.openai.com/codex/skills` now serves the build-skills page with a canonical link to `learn.chatgpt.com/docs/build-skills`, so the canonical URL is cited.

| Claim | Source | Read in the 2026-11-03 pass |
|---|---|---|
| Skill package shape, required `name`/`description`, `@` / `/skills` / `$` invocation, the 2% / 8,000-character listing budget, `skills.max_context_tokens` up to 10,000 tokens, shorten-then-omit, and the initial-list-only scope of the budget | <https://learn.chatgpt.com/docs/build-skills> | yes |
| The discovery locations, same-`name` non-merge, symlinked skill folders, `[[skills.config]]` with last-match precedence, `[skills.bundled]`, `agents/openai.yaml` including `allow_implicit_invocation`, plugins as the distribution path, `$skill-installer`, `$skill-creator` | <https://learn.chatgpt.com/docs/build-skills> | yes |
| The four evaluation axes, the 10-20 prompt starting set, the four invocation modes, and `codex exec` for repeatable runs | <https://developers.openai.com/blog/eval-skills> | yes |
| Versioned API bundles, standard compatibility, bundle limits, user-prompt priority, and the prompt-injection/exfiltration warning | <https://developers.openai.com/api/docs/guides/tools-skills> | yes |
| AGENTS.md discovery and precedence | <https://learn.chatgpt.com/docs/agent-configuration/agents-md> | no |
| Clear instructions, examples, and explicit output formats | <https://developers.openai.com/api/docs/guides/prompt-engineering> | no |
| Model variability and eval-backed iteration | <https://developers.openai.com/api/docs/guides/evaluation-best-practices> | no |
| Prompt injection, tool-calling, and side-effect safeguards | <https://developers.openai.com/api/docs/guides/agent-builder-safety> | no |

### Evidence grade

`VENDOR` - these are OpenAI's statements about OpenAI's own products. A vendor statement about its
own loading mechanics (discovery locations, size caps, invocation policy) is a fact about that product;
the same vendor's statement about what makes a skill good is a heuristic. Four rows above are carried
forward unread from the 2026-06-02 pass and are marked as such rather than given a refreshed date.
