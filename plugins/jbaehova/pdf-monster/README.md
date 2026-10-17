<h1 align="center">PDF Monster</h1>

<p align="center">
  <strong>AI-agent PDF analysis skill and Codex plugin</strong>
</p>

<p align="center">
  <em>PDFs in, model-readable evidence out.</em>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="PyMuPDF" src="https://img.shields.io/badge/PDF-PyMuPDF-DC2626?style=flat-square">
  <img alt="OCR" src="https://img.shields.io/badge/OCR-Tesseract-0F766E?style=flat-square">
  <img alt="Codex Plugin" src="https://img.shields.io/badge/Codex-Plugin-111827?style=flat-square">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-C5A800?style=flat-square">
</p>

<p align="center">
  <a href="#what-it-does">Features</a> &bull;
  <a href="#install">Install</a> &bull;
  <a href="#cli-usage">CLI Usage</a> &bull;
  <a href="#output">Output</a> &bull;
  <a href="#use-as-an-agent-skill">Agent Skill</a> &bull;
  <a href="#license">License</a>
</p>

> **PDF Monster** turns PDFs into model-readable evidence: extracted text, optional OCR text, rendered page images, and embedded image files. It is built for agents that need to inspect PDFs without dumping generated folders into the user's project.

## What It Does

- Extracts per-page text from PDFs
- Renders pages to PNG when layout or visual inspection matters
- Runs optional OCR through Tesseract
- Extracts embedded images for figures and screenshots
- Emits a structured JSON manifest for agents to read
- Avoids creating `output/`, `pages/`, or similar folders unless explicitly requested

## Install

### Install As A Codex Plugin

Add this repository to Codex:

```bash
codex plugin marketplace add jbaehova/pdf-monster
```

Then install or enable **PDF Monster** from Codex's Plugins UI.

For local development, add this checkout directly:

```bash
codex plugin marketplace add /absolute/path/to/pdf-monster
```

This repository is the installable Codex plugin package. Its plugin files follow the same root-level layout used by simple Codex plugins:

```text
.codex-plugin/plugin.json
.claude-plugin/marketplace.json
plugin -> .
assets/pdf-monster.svg
skills/pdf-monster/SKILL.md
skills/pdf-monster/scripts/analyze_pdf.py
```

`plugin` is a compatibility symlink to the repository root. It keeps the installable package at the root while giving Codex a non-empty marketplace source path.

After these files are pushed to GitHub, users can add the plugin with `codex plugin marketplace add jbaehova/pdf-monster`.

### Install As A Standalone Skill

Clone this repository, then copy or reference the skill package at `skills/pdf-monster`:

```bash
git clone https://github.com/jbaehova/pdf-monster.git pdf-monster
```

Python 3 is required. On first use, the skill tells the agent to check for PyMuPDF and install the recommended Python dependency when it is missing and pip/network installs are allowed:

```bash
python3 -m pip install -r /absolute/path/to/pdf-monster/skills/pdf-monster/requirements.txt
```

If you run the CLI yourself, install it once from the repo root:

```bash
python3 -m pip install -r skills/pdf-monster/requirements.txt
```

Optional system tools are not installed automatically:

- Poppler: `pdfinfo`, `pdftotext`, `pdftoppm`, `pdfimages`
- Tesseract: `tesseract` plus language data such as `eng` or `kor`

## Use As An Agent Skill

Install the skill folder, not just `SKILL.md`, because the skill uses `scripts/analyze_pdf.py`.

Common locations:

```text
Claude Code:   ~/.claude/skills/pdf-monster
Codex:         ~/.codex/skills/pdf-monster
Pi:            ~/.pi/agent/skills/pdf-monster or ~/.agents/skills/pdf-monster
OpenClaw:      ~/.openclaw/skills/pdf-monster or <workspace>/skills/pdf-monster
Hermes:        ~/.hermes/skills/pdf-monster
```

For agents without native skill discovery, point custom instructions at the absolute path to the nested `SKILL.md` and tell the agent to run:

```bash
python3 /absolute/path/to/pdf-monster/skills/pdf-monster/scripts/analyze_pdf.py <file.pdf> --json
```

## CLI Usage

Basic analysis:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --json
```

Visual or scanned PDFs:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --render-pages all --ocr auto --json
```

Slide decks or PDFs with repeated logos/icons:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --render-pages all --min-image-area 10000 --dedupe-images --json
```

Korean and English OCR:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --render-pages all --ocr auto --ocr-lang kor+eng --json
```

Text-only mode:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --render-pages none --no-extract-images --ocr never --json
```

Selected pages:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --pages 1,3-5 --render-pages all --json
```

Persist artifacts when you actually want files kept:

```bash
python3 skills/pdf-monster/scripts/analyze_pdf.py file.pdf --save-to ./pdf-monster-artifacts --json
```

## Output

The script prints JSON with fields such as:

- `page_count`
- `selected_pages`
- `backend`
- `artifact_root`
- `cleanup_command`
- `pages_needing_visual_review`
- `pages[].text`
- `pages[].ocr_text`
- `pages[].render_path`
- `pages[].embedded_images`
- `pages[].needs_visual_review`
- `pages[].visual_review_reasons`
- `pages[].warnings`

If temporary artifacts are created, the JSON includes a `cleanup_command`. Run it only after the image paths are no longer needed.

## Notes

PyMuPDF is the preferred backend. If it is unavailable, PDF Monster falls back to Poppler CLI tools where possible. OCR is optional; when Tesseract is missing, the script reports a warning and continues with text extraction and page rendering.

## License

MIT. See [LICENSE](LICENSE).
