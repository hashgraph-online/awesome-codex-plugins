# README Mode Contract

> The contract, workflow, and gates for a project or package `README.md` written from the codebase.

**Purpose**: Own the `readme` mode end to end. **Read when**: `rules/mode-routing.md` selected `readme`, before that mode's first phase.

## 1. Purpose

- Generate a project `README.md` grounded in the real codebase, not boilerplate.
- Refactor stale or generic READMEs so install, usage, structure, and examples match current code.
- Adapt section choice and depth to project shape (CLI, library, web app, monorepo, plugin, framework, docs site, service).
- Preserve evidence: every install command, script, badge, and example traces back to a file in the repo.

## 2. Instruction Contract

| Field | Contract |
|---|---|
| Intent | Produce or improve a `README.md` that reflects the real shape, install, usage, and constraints of the target project. |
| Scope | Own the target `README.md` (root or package) and a short summary; do not edit source code, configuration, license, or unrelated docs unless the user asks. |
| Authority | User instructions and project-local docs (`AGENTS.md`, `CLAUDE.md`, root README, package manifests) outrank generic README conventions and external templates. |
| Evidence | Ground every install command, script invocation, file path, badge, and feature claim in a real file under the project. Do not invent commands or APIs. |
| Tools | Use read/edit/write and shell search (`find`, `grep`, `ls`) only inside the project. Do not run install, build, deploy, or release commands as part of authoring. |
| Loop | None. One pass per request, specified in §4; re-invoke only when the user asks for another README or a follow-up section update. |
| Output | A single written or updated `README.md`, plus a short summary noting which files were inspected and which sections changed. |
| Verification | Run project-discovery, shape, language, and evidence checks from `rules/readme/validation.md` before completion. |
| Stop condition | Finish when checks pass and any uncertain claims are flagged with `<!-- TODO -->`; escalate when project shape is ambiguous, license is unclear, or commands cannot be verified from the repo. |

## 3. Sub-modes

| Situation | Mode |
|------|------|
| Project has no `README.md` | create |
| `README.md` exists but is stale, generic, or contradicts current code | refactor |
| Specific sections need updating after a feature, rename, or move | update |
| A sub-package or workspace inside a monorepo needs its own README | create |
| README needs Korean-by-default language alignment, or must preserve an explicitly requested/existing documentation language | refactor |

## 4. Loop Policy

No loop. One request produces one discovery pass, one section plan, one draft, one validation pass, and one report. When a check fails, fix the named section and re-run that check, at most twice; after that, report the remaining gap instead of iterating further. Self-review alone never counts as verification.

## 5. Workflow

| Phase | Task | Output |
|------|------|------|
| 0 | Confirm the deliverable is a `README.md`; pick `create`/`refactor`/`update` | Mode decision |
| 1 | Scan project structure and detect shape (`rules/readme/project-discovery.md`) | Project profile |
| 2 | Read existing README, `AGENTS.md`, `CLAUDE.md`, license, manifests, and entry points | Evidence base |
| 3 | Pick sections, order, depth, and Korean-by-default language handling (`rules/readme/section-design.md`) | Section plan |
| 4 | Draft or refactor `README.md` using grounded examples and Korean-default templates from `references/readme/readme-templates.md` / `.ko.md` | Updated README |
| 5 | Run validation checks (`rules/readme/validation.md`) and write the completion summary | Final README + summary |

### Phase 4 authoring rules

- Read first, write second. Never invent install commands, scripts, environment variables, or APIs.
- Write README prose in Korean by default. Use another language only when the user requests it or an existing target README must preserve its current documentation language.
- Prefer one accurate example over three speculative ones.
- Keep the README scannable: title, description, install, and quickstart belong above the fold.
- Move long deep-dive content out of the README and link to it; the README should orient, not exhaust.
- Do not add badges that cannot be verified (CI status, coverage, npm version) unless the project already publishes them.

## 6. Required

| Category | Required |
|------|------|
| Evidence | Every install/usage line maps to a manifest, script, source file, or existing doc in the repo |
| Shape match | Section selection matches the detected project type |
| Language match | README prose is Korean by default, or matches the user-requested/existing target language when preservation is required |
| Discoverability | Title, one-line description, install, and quickstart are above the fold |
| Scope | Update mode touches only the sections the user named or the diff implies, and adds a change-history entry only when the README already tracks one |
| Verification | Validation checklist completed before claiming done |

## 7. Forbidden

| Category | Avoid |
|------|------|
| Fabrication | Install commands, scripts, environment variables, or APIs not present in the repo |
| Drift | Stale screenshots, broken links, deprecated commands left in place |
| Overload | Embedding full API references, long tutorials, or design docs inside the README |
| Tone | Marketing fluff, vague superlatives, hype the code does not support |
| Side effects | Editing source code, configs, or licenses while authoring the README |
| Extra files | Creating `CHANGELOG.md`, `CONTRIBUTING.md`, or other docs unless the user asks |

## 8. Validation

| Check | Rule |
|------|------|
| Evidence | Each command and path in the README exists in the repo |
| Shape | The selected template matches the actual project type |
| Language | README is Korean by default, with non-Korean output only for explicit user request or existing target-language preservation |
| Above the fold | Title, description, install, and quickstart appear within the first screen |
| No fabrication | No invented APIs, scripts, env vars, or external badges |
| Lean body | Long content is linked, not inlined |
| Translation pair | If the skill itself or other markdown was edited, English/Korean files stay aligned |

Must-pass thresholds:
- [ ] Project shape detected and recorded in the completion summary
- [ ] At least one verified install command and one verified usage example
- [ ] Existing README sections that remain accurate are preserved (refactor/update mode)
- [ ] Unknowns are marked with `<!-- TODO -->`, not fabricated
- [ ] No dead links or removed scripts left in the new draft

## Sources

> No external sources were used. Content checked 2026-11-07.

| Claim | Source |
|---|---|
| The README contract, sub-modes, workflow, and gates in this file | this package's own procedure text, carried over unchanged in substance when the README workflow became a mode of this skill on 2026-11-07 |
| The discovery order, section policy, and per-type skeletons it delegates to | `rules/readme/project-discovery.md`, `rules/readme/section-design.md`, `references/readme/readme-templates.md` (this package) |
