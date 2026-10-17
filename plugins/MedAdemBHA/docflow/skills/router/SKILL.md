---
name: router
description: 'Find the right doc before reading code. Use when asked "where is X documented", "is there a spec/ADR for X", "what''s the roadmap", "open bugs", "read the docs about X", or "share the docs".'
---

# router

Project-agnostic. No hardcoded tree — **discover, then route**. Works in any repo.

---

## 1 — Discover the docs (do this first, once per session)

Run a cheap scan to learn what this project has. Cache the result mentally for the session.

```bash
# docs roots + entry points
ls README* CONTRIBUTING* 2>/dev/null
fd -t d -d 2 -i 'docs?|spec|adr|decisions|wiki|reference' 2>/dev/null \
  || find . -maxdepth 3 -type d \( -iname 'docs' -o -iname 'spec*' -o -iname 'adr' -o -iname 'decisions' \) -not -path '*/node_modules/*'
# the markdown tree under the main docs dir (swap <DOCS> for what you found)
fd -e md . <DOCS> 2>/dev/null | head -80 || find <DOCS> -name '*.md' | head -80
```

If a hand-maintained index exists (`<DOCS>/README.md`, `SUMMARY.md`, `mkdocs.yml`, `docusaurus.config.*`), **read that** — it's the authoritative map. Don't rebuild what the maintainer already wrote.

---

## 2 — Route a question → one doc

Match the question's *shape* to a folder by its conventional name, then **Read that one doc**. Don't bulk-read the tree.

| Question shape | Look in (by conventional name) |
|----------------|-------------------------------|
| "What does feature X do?" (user-facing) | `product-spec/`, `docs/features/`, top-level `README` |
| "How is X implemented / data flow / API contract?" | `specs/`, `docs/architecture/`, `design/` |
| "Why did we choose X?" | `decisions/`, `adr/`, `docs/adr/` (ADR files) |
| "How do I do X / convention for X?" | `references/`, `docs/guides/`, `CONTRIBUTING.md` |
| "What's planned / status of X?" | `plans/`, `roadmap/`, `docs/roadmap/`, project board |
| "Known issues / open bugs?" | `reviews/bugs/`, `ISSUES.md`, GitHub issues |
| "What shipped recently?" | `CHANGELOG.md`, `changelog/`, releases |

If names don't match these, fall back to the discovered index from step 1.

### Rules
- Map question → doc → **Read** exactly that doc. Grep the tree only when no index resolves it.
- Docs reflect state *when written* (check dates / filenames) — verify against code before acting on stale detail.
- For how-to-*code* questions, prefer the project's own coding-rules / conventions doc over re-deriving from spec.
- Before fixing a bug, check the bug catalog / issues for an existing entry + severity.

---

## 3 — Share docs + this skill with collaborators (GitHub)

Three layers — do whichever the user asked for.

### A. Ship the skill in the repo (teammates auto-get it)
Project skills live at `.claude/skills/<name>/SKILL.md` and are **checked into git** — anyone who pulls + uses Claude Code gets them automatically, zero setup.

```bash
mkdir -p .claude/skills/router
cp ~/.claude/skills/router/SKILL.md .claude/skills/router/SKILL.md   # or author a project-tuned copy
git add .claude/skills/router && git commit -m "docs: add docs router skill"
```
- **Global** copy (`~/.claude/skills/`) = only you, every project.
- **Project** copy (`.claude/skills/` in repo) = whole team, this repo. Commit it to share.
- A project copy can hardcode the real tree (faster, no discovery) — keep this generic one global as the template.

### B. Make docs browsable on GitHub (no Claude Code needed)
- **Minimum:** a `<DOCS>/README.md` index with relative links to every doc — GitHub renders it; links are clickable in the web UI.
- **Link from root:** add a "## Documentation" section in the top-level `README.md` pointing at `<DOCS>/`.
- **Full site (optional):** GitHub Pages via MkDocs or Docusaurus, or a GitHub **Wiki** for free-form pages. Pages = versioned with code; Wiki = separate, easier for non-devs.

### C. Shareable onboarding link (Claude Code)
For a teammate who'll use Claude Code: create an `ONBOARDING.md` at repo root (point them at `<DOCS>/` + the skills), then use the **ShareOnboardingGuide** tool to upload it and get a link they open in Claude Code. Generic and project-agnostic.

---

## Reuse note
This skill is intentionally project-agnostic — it lives in `~/.claude/skills/` so it loads in every repo. To specialize it for one project, copy it into that repo's `.claude/skills/` and replace step 1's discovery with the project's actual doc tree (like a hand-written router).
