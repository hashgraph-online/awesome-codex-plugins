<div align="center">

# Velith

<p>
  <a href="https://github.com/epicsagas/Velith/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/epicsagas/Velith?style=for-the-badge&labelColor=0d1117&color=ffd700&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/Velith/network/members"><img alt="Forks" src="https://img.shields.io/github/forks/epicsagas/Velith?style=for-the-badge&labelColor=0d1117&color=2ecc71&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/Velith/issues"><img alt="Issues" src="https://img.shields.io/github/issues/epicsagas/Velith?style=for-the-badge&labelColor=0d1117&color=ff6b6b&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/Velith/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/epicsagas/Velith?style=for-the-badge&labelColor=0d1117&color=58a6ff&logo=git&logoColor=white" /></a>
</p>
<p>
  <a href=".claude-plugin/plugin.json"><img alt="Version" src="https://img.shields.io/badge/version-0.7.0-fc8d62?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-3fb950?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="https://claude.ai/code"><img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-plugin-bc8cff?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="https://github.com/openai/codex"><img alt="Codex CLI" src="https://img.shields.io/badge/Codex_CLI-plugin-10a37f?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="https://x.ai/cli"><img alt="Grok Build" src="https://img.shields.io/badge/Grok_Build-plugin-ffffff?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="https://buymeacoffee.com/epicsaga"><img alt="Buy Me a Coffee" src="https://img.shields.io/badge/buy_me_a_coffee-FFDD00?style=for-the-badge&labelColor=0d1117&logo=buymeacoffee&logoColor=black" /></a>
</p>
<p>
  <a href="docs/i18n/README.ko.md">한국어</a> ·
  <a href="docs/i18n/README.ja.md">日本語</a> ·
  <a href="docs/i18n/README.zh-Hans.md">中文</a> ·
  <a href="docs/i18n/README.es.md">Español</a> ·
  <a href="docs/i18n/README.fr.md">Français</a> ·
  <a href="docs/i18n/README.de.md">Deutsch</a> ·
  <a href="docs/i18n/README.pt-BR.md">Português</a>
</p>

**Books to the human-quality bar.** A six-phase pipeline that takes a book from a blank page to a publishable EPUB and PDF, and holds every chapter, every edit, and every image to one standard: a cold reader who buys books in this genre cannot tell it was machine-drafted.

`Phase 0: Onboarding → Phase 1: Ideation → Phase 2: Outlining → Phase 3: Drafting → Phase 4: Editing → Phase 5: Publishing`

</div>

<img src="docs/assets/features.png" width="100%" alt="Features of Velith" />

## Why Velith?

Frontier models write good sentences. Left alone, they still write books that readers put down: a voice that drifts by chapter eight, characters who explain their feelings, statistics that do not exist, paragraphs that all end on a punch line, illustrations that change style every chapter. None of that is a model problem. It is a pipeline problem.

Velith is the pipeline. It reads the whole manuscript before writing the next chapter, locks the voice on a sample before drafting volume, critiques and revises every chapter before saving it, fact-checks every claim, rewrites during editing instead of filing reports, cold-reads the finished book as its target readers, and refuses to publish until they would keep reading. Images get the same treatment: one art bible per book, prompts compiled from it for whichever image model you use, diagrams rendered from code, and every picture opened and judged before it ships.

## What changed in 0.5

| Before (0.4) | Now (0.5) |
|--------------|-----------|
| Agents received chapter summaries | Agents read the entire manuscript (frontier models carry 1M tokens; a novel is under 200K) |
| Four chapters drafted in parallel | Narrative genres draft in order; chapter N reads chapter N-1 |
| One pass per chapter | Draft → cold critique with quoted lines → revise, before the file is saved |
| Editing produced reports | Editing rewrites the manuscript in place, with snapshots, across 7 stages |
| "delve"-list slop detection | The 2026 AI-tell taxonomy: rhythm, structure, emotion, dialogue, plus en/ko/ja lexical tells, measured by `velith.mjs metrics` |
| No fact-checking | `fact-checker` builds a claim ledger and removes what it cannot verify |
| Gate = files exist | Gate = `beta-reader` readiness verdict: five axes ≥ 7, no put-down point in chapters 1-3 |
| Cover prompts only | Art bible, look lock, code-rendered figures, compiled prompts for any backend, vision QA, asset validation |

| | Feature | Why it matters |
|--|---------|----------------|
| 📏 | One quality bar | `skills/loom/quality-bar.md`: five-axis rubric, AI-tell taxonomy, cold-read protocol. Every agent reads it |
| 📋 | 6-phase pipeline with author checkpoints | Concept, outline, voice lock, look lock, restructures, readiness. Everything else runs unattended |
| 📖 | 7 genre craft references + custom | Fiction, non-fiction, technical, screenplay, poetry, game, academic: structure options, craft, genre-specific tells, language notes |
| 🤖 | 12 specialized agents | Architect, scene planner, writer, continuity, fact-checker, style doctor, beta reader, art director, figure engineer, illustrator, cover, marketing |
| ✏️ | 7-stage editing | Fact check → assessment → developmental → line → copy → proofread → readiness |
| 🎨 | Visual system | Art bible, look lock, Mermaid/D2/SVG figures, model-agnostic prompts, vision QA, print/EPUB checks |
| 📊 | Deterministic metrics | Sentence rhythm, paragraph shape, repetition across chapters, tell density (en/ko) |
| 📦 | EPUB, PDF, MOBI, TXT, Markdown | Pandoc + optional Calibre, epubcheck, KDP and Korean platform checklists |

## Comparison

| | Velith | Raw prompts | Notion AI | Jasper / Sudowrite | Scrivener |
|--|-----------|-------------|-----------|-------------------|-----------|
| Full-manuscript context | Every agent, every task | Manual | None | Limited | n/a |
| Voice lock + critique-revise loop | Built in | None | None | None | Manual |
| Fact-checking with claim ledger | Dedicated agent | None | None | None | Manual |
| Readiness gate by simulated readers | Blocks publishing | None | None | None | None |
| Visual consistency across a book | Art bible + compiled prompts + vision QA | Per-image prompts | None | None | None |
| Genre awareness | 7 craft references + custom | Prompt-dependent | None | Fiction-focused | None |
| Output format | EPUB, PDF, MOBI, TXT, Markdown | Copy-paste | Markdown / PDF | DOCX, limited | DOCX, PDF |
| Requires | Claude Code, Codex CLI, Grok Build, Agy, Cursor, Cline, or Aider | Any LLM | Notion subscription | Subscription | License |
| Full control | Prompt-level, Apache-2.0 | Full | Black box | Black box | Full |

## Installation

### Claude Code

```
/plugin marketplace add epicsagas/plugins
/plugin install velith@epicsagas
```

All 18 skills and 12 agents are available immediately. Updates with `/plugin update velith@epicsagas`.

**Prerequisites:** [Claude Code](https://claude.ai/code) CLI installed and authenticated. Velith is tuned for the Claude 5 family (1M context); agents inherit your session model and set their own effort level.

### Codex CLI (OpenAI)

```bash
codex plugin marketplace add epicsagas/plugins
```

Velith provides 18 skills and 12 custom subagents (`.codex-plugin/agents/*.toml`, generated from `agents/*.md`). Codex auto-discovers both. Updates with `codex plugin update velith@epicsagas`.

**Prerequisites:** [Codex CLI](https://github.com/openai/codex) installed and configured.

### Grok Build (xAI)

```bash
grok plugin install epicsagas/Velith --trust
```

Grok reads skills from `skills/` and agents from `agents/` at the plugin root. No extra configuration needed. Agents spawn as `velith:<name>` (for example `velith:chapter-writer`).

Alternatively, add this repository as a marketplace:

```bash
grok plugin marketplace add epicsagas/Velith
grok plugin install velith --trust
```

Updates with `grok plugin update velith`.

**Prerequisites:** [Grok Build](https://x.ai/cli) installed and authenticated.

### Agy (Antigravity)

```bash
agy plugin install https://github.com/epicsagas/Velith
```

### Cursor

Context rules in `.cursor/rules/`:

| Rule File | Loaded When |
|-----------|-------------|
| `velith-pipeline.mdc` | Always (phases, router, agents, quality bar, checkpoints) |
| `velith-genres.mdc` | Editing drafts, outlines, or PRD files |
| `velith-editing.mdc` | Working on edits, STYLE.md, or bible.md |

### Cline

Project-level instructions in `.clinerules` at the repository root.

### Aider

Writing conventions in `CONVENTIONS.md`, auto-loaded via `.aider.conf.yml`.

## Quick Start

```bash
> /book-init          # genre, reader, language, voice sample → PRD.md + STYLE.md
> /loom               # detects state and runs the next phase, stopping at author checkpoints
```

What happens:

1. **Onboarding** — reader, promise, scope, and a voice fingerprint from your own writing sample
2. **Ideation** — premise stress test, real comparable titles, ranked concepts; you choose
3. **Outlining** — structure chosen and justified, chapter specs, figure plan, bible; architect scores it; you approve
4. **Drafting** — voice lock on a sample chapter; then sequential full-context chapters, each critiqued and revised, bible ledger updated, continuity checked
5. **Editing** — fact check, assessment, developmental rewrites, line edit, copy edit, proofread, then a cold read by simulated target readers. PASS or REVISE
6. **Publishing** — front and back matter, EPUB/PDF/MOBI, epubcheck, cover from the art bible, marketing plan, platform checklists

Images at any point from Phase 2: `/book-visuals plan` (art bible), `/book-visuals lock` (look lock), then figures and illustrations as the chapters need them.

## Skills

| Skill | Phase | Description |
|-------|-------|-------------|
| `/loom` | Router | Detect state, run the next phase, enforce gates |
| `/book-init` | 0 | Reader, promise, scope, voice fingerprint, source index → `PRD.md`, `STYLE.md` |
| `/book-ideation` | 1 | Premise stress test, comps, ranked concepts, voice samples |
| `/book-outline` | 2 | Structure, chapter specs, figure plan, bible, scored validation, approval |
| `/book-draft` | 3 | Voice lock, sequential draft-critique-revise, ledger, continuity |
| `/book-edit` | 4 | 7 stages: fact check … readiness verdict |
| `/book-publish` | 5 | Readiness gate, matter, formats, epubcheck, cover, marketing, checklists |
| `/book-visuals` | 2-5 | Art bible, look lock, figures, illustrations, photos, prompt compile, vision QA, asset check |
| `/book-illustrate` | 3-5 | Alias for the illustration subset of `/book-visuals` |
| `/book-status` | — | Terminal dashboard, `--ui` browser dashboard, `--metrics` |
| `/book-fiction` … `/book-academic` | — | Genre craft references (7) |
| `/book-genre-creator` | — | Genre selection and custom genre specs |

## Agents

| Agent | Phase | Job |
|-------|-------|-----|
| `book-architect` | 2 | Outline and bible; structure chosen and justified; scored validation; restructure proposals |
| `scene-generator` | 3 | Scene plans per fiction chapter (purpose, turn, subtext, exit). Plans, not prose |
| `chapter-writer` | 3-4 | One chapter in full context; drafts, critiques with quoted lines, revises, updates the ledger |
| `continuity-editor` | 3-4 | Contradictions and repetitions across the whole manuscript against the bible |
| `fact-checker` | 4 | Claim ledger; verification against sources and web; removes what cannot be verified; runs code |
| `style-doctor` | 4 | Measures, then rewrites tells, rhythm uniformity, and drift in place |
| `beta-reader` | 4 | Cold read as three target readers and one professional; readiness verdict |
| `art-director` | 2-5 | Art bible, look lock, vision QA of every image, contact-sheet review |
| `figure-engineer` | 3-5 | Diagrams, charts, technical drawings, maps' base layers as code; labels verified against the text |
| `illustrator` | 3-5 | Illustrations from the art bible with compiled prompts, generation when a tool exists, vision QA |
| `cover-designer` | 5 | Cover concepts from the art bible, formats, marketing variants |
| `marketing-expert` | 5 | Positioning, personas, channels, calendar, launch checklist |

## The quality bar

`skills/loom/quality-bar.md` is read by every writing, editing, and reviewing agent. It defines:

- **Five axes, scored 1-10 with anchors**: voice and prose, structure and pacing, depth, specificity and grounding, reader experience. Voice lock needs axis 1 ≥ 7. Readiness needs every axis ≥ 7, mean ≥ 7.5, and no put-down point in the first three chapters.
- **The 2026 AI-tell taxonomy**: what readers actually notice now (uniform paragraph rhythm, punch-line closures, "not X but Y", reflective codas, precise self-knowledge, dialogue that answers, hedged authority, invented specificity) with fixes, plus lexical lists for English, Korean, and Japanese.
- **The cold-read protocol**: read once at speed, mark, diagnose with quoted lines, score honestly, prioritize, then revise.
- **Visual rules**: one look per book, purpose before decoration, code for anything with text or data, look lock, vision QA, release constraints.

## CLI

```bash
node velith.mjs scan <dir> [--ui]           # project state, dashboard data, readiness verdict
node velith.mjs metrics <dir|file>          # prose metrics + cross-chapter repetition (JSON)
node velith.mjs snapshot <dir> <label>      # copy drafts/ before a rewriting stage
node velith.mjs images compile <dir> [id]   # art bible + spec → Midjourney / gpt-image / SD-FLUX / Imagen / Ideogram prompts
node velith.mjs images check <dir>          # dimensions, aspect, size, alt text, references, manifest coverage
node velith.mjs images render <dir>         # Mermaid / D2 / Graphviz / SVG / matplotlib → SVG + PNG
```

## Visual Dashboard

<img src="docs/assets/dashboard.png" width="100%" alt="Dashboard" />

`/book-status --ui` opens a Svelte dashboard: pipeline tracker, 12 agent cards, chapter table, 6-stage editing kanban, readiness verdict with axis scores, output files, settings. Pre-built `dist/` is included.

```bash
cd dashboard && npm install && npm run dev   # http://localhost:5173
npm run build                                 # rebuild dist/
```

## External Dependencies

```bash
brew install pandoc                 # EPUB/PDF (required for Phase 5)
brew install texlive                # PDF with CJK support
brew install --cask calibre         # MOBI (optional)
brew install epubcheck              # EPUB validation (optional, recommended)
npm i -g @mermaid-js/mermaid-cli    # Mermaid figures → SVG (optional)
brew install d2 graphviz librsvg    # D2 / Graphviz figures, SVG → PNG (optional)
```

Image generation is not bundled. `illustrator` and `cover-designer` generate when an image tool is available in your session (MCP image servers, Replicate, local Stable Diffusion); otherwise they hand you compiled prompt packs per backend in `visuals/prompts/`.

<details>
<summary>Troubleshooting</summary>

- **pandoc not found** — `brew install pandoc`
- **CJK characters missing in PDF** — `brew install texlive` or `brew install basictex && sudo tlmgr install collection-langkorean`
- **Plugin commands not found** — restart Claude Code
- **Phase 4 never completes** — the gate is `edits/readiness-report.md` with `verdict: PASS`; run `/book-edit 6`
- **Images look different per chapter** — no look lock; run `/book-visuals plan` then `/book-visuals lock`
</details>

## Project Structure

```
{project-dir}/
├── PRD.md              # Requirements + reader promise
├── STYLE.md            # Voice fingerprint, voice sample, rules, voice lock
├── ideation.md         # Concepts, comps, chosen concept
├── outline.md          # Chapter specs, figure plan, validation, approval
├── bible.md            # Characters/concepts, term rules, timeline, per-chapter ledger
├── art-bible.md        # Visual identity, figure system, look lock
├── sources/            # Reference material + INDEX.md
├── drafts/             # ch{NN}-{slug}.md, ch{NN}-scenes.md (revised in place during editing)
├── visuals/            # plan, manifest, figures/, illustrations/, photos/, ref/, prompts/
├── edits/              # 00-fact-check … 06-readiness-report, readiness-report.md, editorial-report.md
├── publish/            # book.epub/pdf/…, metadata, front/back matter, cover/, marketing, checklists
└── .velith/            # status.json, art-bible.json, critiques/, snapshots/, metrics.json
```

## Integration

- **alcove** — search your document vault as source material during `/book-init` and drafting.
- **obsidian-forge** — `of book init / sync / export` to write from an Obsidian vault.
- **humanize-korean** — if installed, `style-doctor` may run it as a final Korean polish.
- **Image generation MCPs** — used by `illustrator` and `cover-designer` when present.

All optional. Velith works standalone.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Prompts are the product: a change to `quality-bar.md` or an agent file changes every book. Test with `examples/` and `node velith.mjs metrics`.

## License

[Apache-2.0](LICENSE)
