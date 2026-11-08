# Anthropic Official References for Skill-Maker

## Contents

- Refresh Policy
- Claude Code Skills
- Agent Skills Overview
- Skill Authoring Best Practices
- Skills for Enterprise
- Agent Skills Engineering Post
- Claude Skills Product Post
- Sources

## Refresh Policy

- last_verified_at: 2026-11-03
- refresh_when:
  - Claude Code or Agent Skills guidance changes materially
  - the frontmatter field table, the listing budget, or the spec-vs-extension split changes
  - skill anatomy, progressive disclosure, script, or validation guidance changes
  - core hyper-skill rules cite Anthropic behavior more directly
- supports_rules:
  - `rules/skill-anatomy.md`
  - `rules/trigger-design.md`
  - `rules/progressive-disclosure.md`
  - `rules/resource-placement.md`
  - `rules/validation-and-iteration.md`

## Claude Code Skills

- source_url: https://code.claude.com/docs/en/skills
- last_verified_at: 2026-11-03
- applies_to: `SKILL.md`, the full frontmatter surface, supporting files, invocation control, dynamic context injection, string substitution, the listing budget, discovery locations, the in-context lifecycle, eval tooling
- summary: Claude Code skills follow the Agent Skills open standard and extend it. **Claude Code reads
  the frontmatter only when the opening `---` is the file's first line**; otherwise it treats the whole
  file, `---` markers included, as skill content. If the YAML between the markers does not parse, the
  skill still loads with no fields set. The page documents twenty frontmatter fields, all optional, of
  which six belong to the standard - `name`, `description`, `license`, `compatibility`, `metadata`,
  `allowed-tools`. Claude Code ignores a field it does not recognize without an error, but on the
  claude.ai upload and Skills API path a field the spec does not allow is a **hard error** ("Unexpected
  key(s) in SKILL.md frontmatter"), and Claude Code-only body features such as dynamic context injection
  do not function there. Skills load from enterprise, personal, project, nested, `--add-dir`, plugin, and
  claude.ai-account locations. **An invoked skill's rendered content enters the conversation as one
  message and stays across later turns; Claude Code does not re-read the file.** `claude plugin
  validate .claude/skills` reports skill files whose frontmatter does not parse.
- implication_for_hyper_skill: separate the six standard fields from the fourteen extensions in the rule
  text, because a skill that relies on them is portable only to Claude Code (SK-P-3). A skill can look
  fine locally and still fail to upload. The first-line rule is already enforced by both repository
  gates, so it needs stating, not new tooling.

### Frontmatter fields as documented

Standard fields (portable): `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.

Claude Code extensions: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`,
`user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`,
`paths`, `shell`.

| Field | Behaviour worth carrying into a rule |
|---|---|
| `description` | Combined with `when_to_use`, the text is truncated at **1,536 characters** in the skill listing. Put the key use case first |
| `when_to_use` | Extra trigger context, appended to `description` and counted against the same 1,536-character cap |
| `disable-model-invocation` | `true` stops Claude from loading the skill automatically, so only explicit invocation works. The Claude Code counterpart of Codex's `allow_implicit_invocation: false` |
| `user-invocable` | `false` hides the skill from the `/` menu so only Claude invokes it |
| `allowed-tools` | Tools Claude may use **without asking permission during the turn that invokes the skill**; the grant clears on the next message even though the skill content stays in context. A permissive grant, not a restrictive boundary |
| `disallowed-tools` | Tools removed from the pool while the skill is active; the restriction clears on the next message |
| `context` | Set to `fork` to run the skill in a forked subagent context, with `agent` choosing the subagent type and `background` controlling whether the turn waits |
| `paths` | Glob patterns that limit automatic activation to matching files |
| `shell` | Shell used for inline shell blocks; `bash` by default |
| `hooks` | Hooks registered when the skill is invoked and kept for the session |

### Body features

- **Dynamic context injection**: `` !`command` `` runs a command and replaces the line with its output
  before Claude sees the skill content. Claude Code-only; it does not function on the claude.ai or API path.
- **String substitutions**: `$ARGUMENTS`, `$ARGUMENTS[N]`/`$N`, named `$name` from the `arguments`
  list, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`,
  and, in plugin skills, `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`.
- `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` are substituted in two places: the skill's markdown
  content and Bash rules in `allowed-tools`. Using the same variable in both lets a skill run a bundled
  script without a permission prompt - the documented pattern for shipping a script.

### The listing budget

- Claude Code loads a listing of skill names and descriptions into context. **The listing always
  contains every skill name, but when it overflows, Claude Code shortens descriptions to fit, starting
  with the skills you invoke least.** The budget scales at **1% of the model's context window**, and
  each entry's combined `description` + `when_to_use` text is capped at 1,536 characters regardless of
  budget. `skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`, and `skillListingMaxDescChars`
  change the budget. `/doctor` estimates the listing's cost and its biggest contributors, and
  `/skill-doctor` shows what each skill costs and how often it is used. The `skillOverrides` setting
  controls visibility from settings (`on`, `name-only`, `user-invocable-only`, `off`) without editing a
  skill's frontmatter; plugin skills are not affected by it.
- implication_for_hyper_skill: this is a second, tighter budget than Codex's 2%/8,000 characters, and it
  drops by usage frequency rather than by position. A skill that is rarely invoked is the first to lose
  its description, so the key trigger must lead.

### Eval tooling

- The `skill-creator` skill stores prompts, input files, and expected behavior in `evals/evals.json`
  inside the skill directory and spawns a subagent per case so each run starts clean.
- `claude plugin eval` runs each prompt in an isolated session with and without the plugin, scores it
  with graders, and exits non-zero below a threshold so CI can gate on it; a `tool_used: Skill` grader
  measures triggering.
- **The two formats are not interchangeable.**
- Each eval run starts from a fresh session, because leftover context from authoring the skill masks
  gaps in the written instructions.

## Agent Skills Overview

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- last_verified_at: 2026-11-03
- applies_to: the three loading levels and their costs, field constraints, surface differences
- summary: Metadata loads at startup at about 100 tokens per skill; the `SKILL.md` body loads when
  triggered and should stay under 5k tokens; bundled resources cost nothing until read, and a script's
  code never enters context - only its output does. `name` is at most 64 characters of lowercase
  letters, numbers, and hyphens, with no XML tags and no reserved words "anthropic" or "claude";
  `description` is at most 1,024 characters with no XML tags. Custom skills do not sync across surfaces
  (claude.ai, API, Claude Code). Through the API, skills run in the code execution container without
  network access; in Claude Code they have the same network access as any other program on the machine.
- implication_for_hyper_skill: the 1,024-character spec limit and the 1,536-character Claude Code
  listing cut are different limits; a skill's network posture depends on the surface it runs on.

## Skill Authoring Best Practices

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- last_verified_at: 2026-11-03
- applies_to: frontmatter constraints Claude adds, naming, description voice, progressive disclosure patterns, reference-file structure, model coverage, degrees of freedom
- summary: Claude adds constraints on top of the standard: `name` cannot contain XML tags and cannot
  contain the reserved words **"anthropic"** or **"claude"**, and `description` cannot contain XML tags.
  Descriptions must be written in **third person** - the field is injected into the system prompt, and an
  inconsistent point of view causes discovery problems. Gerund-form names (verb + `-ing`) are the
  recommended convention, with noun phrases and action-oriented names acceptable and vague names such as
  `helper` or `utils` to avoid. Keep `SKILL.md` under 500 lines. Keep references **one level deep**,
  because Claude may partially read files referenced from other referenced files and preview them with
  `head -100` instead of reading them whole. **For reference files longer than 100 lines, include a
  table of contents at the top** so the full scope is visible even on a partial read. Test the skill on
  every model you plan to use, because "what works perfectly for Opus might need more detail for Haiku".
  Match specificity to fragility across three levels: high freedom (text instructions) when many
  approaches are valid, medium freedom (parameterised scripts) when a preferred pattern exists, and low
  freedom (an exact script, no parameters) when operations are fragile and consistency is critical.
- implication_for_hyper_skill: the third-person rule, the reserved-word and XML-tag constraints, the
  gerund convention, and the >100-line table-of-contents rule are all checkable and belong in the rule
  text; the 500-line figure agrees with the specification.

## Skills for Enterprise

- source_url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise
- last_verified_at: 2026-11-03
- applies_to: vetting a skill, the risk-tier table, evaluation dimensions including coexistence, version pinning, recall limits, scanning coverage
- summary: The risk-tier table lists seven indicators with a concern level: **code execution**,
  **instruction manipulation**, **MCP server references**, **network access patterns**, and
  **hardcoded credentials** are High; **filesystem access scope** and **tool calls** are Medium.
  Evaluation before deployment includes **coexistence: "Does adding this Skill degrade other Skills?"**
  with the failure "New Skill's description is too broad, stealing triggers from existing Skills", using
  3-5 representative queries per skill covering should-trigger, should-not-trigger, and ambiguous cases.
  In production, pin skills to specific versions, treat every update as a new deployment requiring full
  security review, keep the previous version as a rollback, compute checksums of reviewed skills and
  verify them at deployment, and keep authors from reviewing their own skills. Limit simultaneously
  loaded skills to keep recall reliable; the API accepts at most 20 skills per request. Automated
  scanning does not cover skills uploaded through the Skills API or the Console.
- implication_for_hyper_skill: the artifact audit must carry all seven risk rows, coexistence must be an
  evaluation dimension rather than an afterthought, and installed-skill count is a budget.

## Agent Skills Engineering Post

- source_url: https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills
- last_verified_at: 2026-11-03
- applies_to: skill anatomy, progressive disclosure, scripts, eval-first iteration, trust boundary
- summary: Published 2025-10-16; the old `/engineering/` URL redirects here. "Progressive disclosure is
  the core design principle that makes Agent Skills flexible and scalable": metadata, then the body,
  then linked files. Code is deterministic, so a bundled script makes a workflow consistent and
  repeatable without loading the script into context. Install skills only from trusted sources, and
  audit an untrusted skill before use - its bundled files, code dependencies, and any instruction to
  reach untrusted network sources. Start with evaluation and build skills incrementally against the gaps.
- implication_for_hyper_skill: Progressive disclosure, scripts with clear purpose, and source/resource trust checks are first-class rules.

## Claude Skills Product Post

- source_url: https://claude.com/blog/skills
- last_verified_at: 2026-06-02
- recheck_status: not re-read in the 2026-09-20 or 2026-11-03 passes - the date above is the last actual read
- applies_to: portability, composability, scripts/resources as reusable capabilities
- summary: Skills are folders with instructions, scripts, and resources that make specialized workflows portable and composable.
- implication_for_hyper_skill: Skills should be maintained as reusable packages rather than one-off prompts.

## Sources

> Checked 2026-11-03 for the rows marked "yes".

| Claim | Source | Read in the 2026-11-03 pass |
|---|---|---|
| The twenty-field frontmatter table, the six standard fields, the hard error for non-spec fields on the upload/API path, unknown fields ignored locally, the first-line rule, YAML-parse fallback, discovery locations, the in-context lifecycle, `context: fork`, dynamic context injection, string substitutions, the 1% / 1,536-character listing budget with least-invoked-first dropping, `/doctor`, `/skill-doctor`, `skillOverrides`, `claude plugin validate`, `evals/evals.json`, `claude plugin eval`, the non-interchangeable formats, and fresh sessions per eval run | <https://code.claude.com/docs/en/skills> | yes |
| The XML-tag and reserved-word constraints on `name`, the XML-tag constraint on `description`, third-person descriptions, the gerund convention, the 500-line body, one-level-deep references and the partial-read reason, the >100-line table-of-contents rule, model-coverage testing, and the three degrees of freedom | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> | yes |
| The three loading levels with their token costs, the field limits, no cross-surface sync, and the surface-dependent network posture | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview> | yes |
| The seven risk-tier rows with their concern levels, coexistence, the 3-5 query suite, version pinning, re-review, rollback, checksums, separation of duties, the 20-skills-per-request limit, and the scanning gap | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> | yes |
| Progressive disclosure as the core principle, the trusted-source and audit rules, and eval-first iteration (published 2025-10-16) | <https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills> | yes |
| Portability, composability, and skills as reusable packages | <https://claude.com/blog/skills> | no |

### Evidence grade

`VENDOR` - Anthropic's statements about its own products. One row above is carried forward unread from
the 2026-06-02 pass and is marked as such rather than given a refreshed date. The enterprise page's
severity labels are that page's assignment, not a controlled study's finding, so an audit against them
is a checklist that catches known artifact-level problems rather than a proof of safety. The
20-skills-per-request limit is stated on the enterprise page, not the overview page.
