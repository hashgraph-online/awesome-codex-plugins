# Resume Tailor

[Русская версия](README.ru.md)

Two independent skills for working with a candidate's actual career record:

| Skill | Use it for |
|---|---|
| `resume-tailor` | Tailoring to a job, a general resume variant, a section edit, a review, or a requested cover letter/application note. |
| `onboarding` | Creating or updating a saved master profile from supplied resumes, notes and career facts. |

Job fit, factual reliability and document quality are reviewed separately. There is no estimated ATS score, interview probability, keyword quota or requirement to invent numerical achievements. Output language, target market, channel and format are separate choices. The candidate can be you or someone whose records you are authorized to use.

The core workflow consists of instructions and references. It needs a compatible agent host, but no plugin backend, API key, paid scanner or export dependency. The host's account and data policies still apply.

This checkout prepares **1.1.0**. It does not establish that a `v1.1.0` tag, release assets or an official directory listing has been published. GitHub installation follows the remote repository's current contents; use the prepared local checkout to test these changes before publication.

## Choose one installation route

A **plugin installation** bundles both skills with host metadata and a marketplace identity. A **skill installation** installs the selected skill directories directly; it does not register a plugin marketplace. Either skill works alone and carries its own profile contract.

Choose one route per host and workspace. Installing the same skill through a marketplace and the Skills CLI/manual copying can create duplicate entries or leave an older copy active.

### Skills CLI: project installation

Run from the workspace where you want to use the skills. Node.js/npm is needed for this installer, not for the resume workflow.

```bash
# Inspect without installing.
npx skills add olegvg/resume-tailor-plugin --list

# Install both skills for these two hosts in the current project.
npx skills add olegvg/resume-tailor-plugin --skill resume-tailor onboarding --agent codex claude-code

# Or install onboarding alone.
npx skills add olegvg/resume-tailor-plugin --skill onboarding --agent codex claude-code
```

Project scope is the default. Add `--global` only when you intentionally want a user-wide installation. For another host, choose its supported `--agent` identifier. To inspect the prepared checkout before publication, substitute `./resume-tailor-plugin` for the GitHub source.

After the maintainer publishes the matching tag, you can pin that version:

```bash
# Conditional example: requires a published v1.1.0 tag.
npx skills add https://github.com/olegvg/resume-tailor-plugin/tree/v1.1.0 --skill resume-tailor onboarding --agent codex claude-code
```

Keep a pinned source when you want reproducible installs. To update a project installation to available upstream changes:

```bash
npx skills update resume-tailor onboarding --project
```

See the [Skills CLI documentation](https://github.com/vercel-labs/skills) for supported agents and scope behavior.

### Codex plugin

With a Codex CLI that exposes `codex plugin`:

```bash
codex plugin marketplace add olegvg/resume-tailor-plugin
codex plugin add resume-tailor@resume-tailor
```

For the prepared local checkout, use `codex plugin marketplace add ./resume-tailor-plugin` instead of the remote source. To pin a release after its tag is published, add `--ref v1.1.0` to the remote marketplace-add command.

Refresh the configured marketplace and installed plugin caches with:

```bash
codex plugin marketplace upgrade resume-tailor
```

Open a new session after installation or refresh if the current session has not discovered the skills. Marketplace availability can differ between Codex surfaces; consult `codex plugin --help` for your installed CLI. See the [official plugin packaging guide](https://developers.openai.com/plugins/build/plugins).

### Claude Code plugin

These examples explicitly select project scope for the marketplace declaration and installation:

```bash
claude plugin marketplace add olegvg/resume-tailor-plugin --scope project
claude plugin install resume-tailor@resume-tailor --scope project
```

Update the marketplace snapshot, then the project installation, and restart Claude Code:

```bash
claude plugin marketplace update resume-tailor
claude plugin update resume-tailor@resume-tailor --scope project
```

To test a local checkout without installing it:

```bash
git clone https://github.com/olegvg/resume-tailor-plugin.git
claude --plugin-dir ./resume-tailor-plugin
```

In Claude Code, plugin skills use `/resume-tailor:onboarding` and `/resume-tailor:resume-tailor`; directly installed skills use `/onboarding` and `/resume-tailor`. In other hosts, select the skill in the host's skill picker or ask the agent to use it. See the [Claude Code plugin documentation](https://code.claude.com/docs/en/plugins).

## Usage examples

Paths below are relative to the **selected candidate workspace**, not the installed plugin or its cache. Supply your actual files or paste the records. A saved master profile is a source of career facts, not a finished resume.

### Create a new or anonymous profile

```text
Use onboarding. Create a master profile from sources/resume.md and the career
notes below in this workspace. Use candidate-1 as a file label; the candidate's
name is unknown. Save to resume/candidate-1/master-profile.md. Preserve unknowns
and source provenance. Do not create a resume or export.
```

New profiles default to `resume/<candidate-label>/master-profile.md` in your selected workspace. A supplied label or a neutral collision-free label is sufficient. Names, contacts, nationality, date of birth, photos and numerical achievements are not mandatory prerequisites. The skill extracts existing facts before asking material follow-ups. Conflicting candidate identities must be resolved before merging their records.

### Update an existing profile

```text
Use onboarding. Update career-records/master.md from the supplied corrected
career notes. Keep its existing schema, location, unrelated notes and edits.
Record the correction's source and leave unresolved facts qualified.
```

An explicit profile path takes precedence; otherwise an unambiguous established profile can be reused. Existing custom schemas and paths are accepted. Durable disclosure restrictions stay separate from decisions that apply to one application or output.

### Tailor without a saved profile

```text
Use resume-tailor. Tailor the supplied candidate resume to jobs/platform-role.md.
Write the English Markdown resume to applications/platform/resume.md. Use the
supplied facts directly; do not create a master profile. Keep the review outside
the recruiter-facing text.
```

A profile is optional. You can also paste the candidate record and JD into chat. If a supplied URL cannot be read, the agent must report the missing information rather than claim to have analyzed it.

### Tailor from a profile, or request a smaller task

```text
Use resume-tailor with career-records/master.md and the supplied JD. Generate a
PDF at applications/role/resume.pdf. Omit languages only for this PDF; preserve
the master profile. Use approved public employer names and NDA descriptions.
```

You can request a general variant without a JD, an edit to one existing section, a review without a rewrite, or a cover letter without a resume. A chat-only request creates no files. Tailoring and export do not automatically create/update a profile, submit an application or change a platform account.

Existing visibility rules and candidate-defined variants are respected. The supported values are `always`, `variant-specific`, `on-request` and `reference-only`; the last is internal-only and stays out of output and exclusion reports. Explicit output instructions can narrow permitted claims or exclude sections without rewriting the canonical career record.

## Optional PDF and DOCX export

Markdown/chat drafting needs no export tooling. For genuine PDF output, an available HTML-to-PDF tool can be used; **WeasyPrint** is one optional route with Python, native-library and font requirements. For genuine DOCX, **python-docx** or host document tooling can create native paragraphs; visual verification also needs an available document renderer.

The skill checks the available environment before choosing an export route. It does not require a particular package manager or global installation. Missing tooling is reported as a limitation, and installation/configuration changes require separate authorization. A renamed HTML/PDF file is not a DOCX export.

Exports exclude review tables and drafting notes. Verify text extraction, source fidelity and every rendered page before treating a file as ready. Local document checks cannot guarantee how a particular employer's ATS or upload form behaves. See the [export reference](skills/resume-tailor/references/document-export.md).

## Privacy and maintenance

Candidate records and outputs belong in the selected private workspace. Keep them out of installed assets, caches, public issues and release archives. The plugin provides no backend or telemetry; model hosts and any tools you enable process data under their own policies. Read [PRIVACY.md](PRIVACY.md) before using sensitive records.

For vulnerability reporting and supported code, read [SECURITY.md](SECURITY.md).

The portable root `plugin.json` declares Agent Plugins schema 1.0.0 and discovers the two directories under `skills/`. `.codex-plugin/plugin.json` provides the compatibility overlay; `.claude-plugin/plugin.json` and the two marketplace indexes expose the same plugin identity. This repository is not a claim of listing in an official plugin directory.

Maintainers: see [AGENTS.md](AGENTS.md), [CHANGELOG.md](CHANGELOG.md) and the [release guide](docs/releasing.md). Root `CLAUDE.md` is a maintainer pointer and is not plugin runtime context; native Claude validation may warn about it when validating a source checkout.

MIT — [LICENSE](LICENSE). Author: [Oleg Gaidukov](https://www.linkedin.com/in/ahaidukof/).
