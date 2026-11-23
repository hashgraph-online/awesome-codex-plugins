# /agent-kit-onboard progressive resolution and domain-skills scaffold

Per-check resolution guidance, exact Ask-label examples, and the domain-skills scaffold execution detail for `.cursor/commands/agent-kit-onboard.md` (kept out of the command to fit its size budget; Goal, Hard Stops, the scaffold's own Ask prompt/labels, and Completion's verification steps stay in the command itself).

## Progressive Resolution (per-check guidance)

Resolve the first pending essential check according to its evidence and recommendation:

1. **Purpose and context:** use README, docs, manifests, workflows, schemas, and existing guidance. Ask only if purpose or source-of-truth context remains ambiguous.
2. **Git operating model:** distinguish no Git, local-only Git, and hosted Git. Treat local-only as valid. Confirm Git initialization and remote setup separately.
3. **Provider:** use explicit configuration, authenticated metadata, known hostnames, and provider files in that order. A custom hostname alone does not identify a provider.
4. **Branch strategy:** preserve existing conventions. Ask before creating, renaming, publishing, or deleting a branch, including `staging`.
5. **Safety and hooks:** safe `.gitignore` merges may use `agent-kit doctor --fix-safe --json`. Ask before installing or replacing hooks.
6. **Quality, CI, and deploy:** infer existing commands and files. Ask before creating CI or deployment configuration. Authentication, permissions, external secrets, and branch protection remain guided manual actions.
7. **Manual blockers:** state the blocker, one recovery action, and the exact check that will be revalidated.

Ask questions labels must describe the concrete effect. Examples:

- `Keep repository without Git` / `Initialize local Git` / `Stop setup`
- `Keep local-only repository` / `Configure a remote` / `Defer remote setup`
- `Confirm GitLab self-hosted` / `Confirm another provider` / `Leave provider unresolved`
- `Keep current branch strategy` / `Create staging branch` / `Defer branch setup`
- `Install Agent Kit hooks` / `Keep existing hooks` / `Show manual integration`
- `Create CI configuration` / `Keep local validation only` / `Defer CI setup`

When Ask questions is unavailable, say so once and present the same options as a numbered list. Accept the number, label, or a custom answer. Do not invent a tool call.

## Domain-skills scaffold: execution detail (after the Ask resolves)

   - **Scaffold domain skills:** show the proposal list, then write any accepted project-owned skills under `.cursor/skills/domain/<skill-id>/SKILL.md` only when the path does not already exist. Update the **Relevant skills** section of `.cursor/project-context.md` (create the heading if missing) with installed and newly accepted skill ids plus evidence; also ensure those ids appear under `.cursor/agent-kit.json` `skills[]` when that manifest is the project's install index. Record `onboarding.domainSkills` in `.cursor/context/config.json` with `status: "applied"`, the list of accepted items, and `appliedAt`.
   - **Defer:** ask for a short reason, then record `onboarding.domainSkills` with `status: "deferred"`, `reason`, and `recoveryCommand: "/agent-kit-onboard"`.
   - **Skip:** record `onboarding.domainSkills` with `status: "skipped"`.
   - Never overwrite an existing project-owned skill or file without a separate HITL confirmation. This closes the gap reported in public issue https://github.com/agent-kit-startup/agent-kit/issues/36 and the dogfood note `dogfood/cursor_onboard_should_scaffold_domain_skills_2026_08_01.md`.
   - **Instruction-only surface:** this gate is chat/`/agent-kit-onboard` prose executed by the agent session. There is no separate CLI subcommand that scaffolds domain skills; intentionally document defer/skip when the operator declines. Project-owned skills under `.cursor/skills/domain/` are one-way (not contributeable via `guessRegistryPath` / registry paths `core` and `community` only).
