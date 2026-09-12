---
name: book-publish
description: "Phase 5: Publishing. Gate on readiness, assemble front and back matter, build EPUB/PDF/MOBI/TXT/Markdown with Pandoc, validate with epubcheck, produce metadata, title candidates, cover concepts, and marketing plan. Includes KDP and Korean platform checklists."
argument-hint: "[project-dir] [--force] [--formats=epub,pdf]"
---

# Phase 5: Publishing

Goal: files a distributor accepts on the first upload, and the supporting assets a launch needs.

## Gate in

`edits/readiness-report.md` must say `verdict: PASS`. Without it, stop and explain; `--force` overrides and records the override in `publish/PUBLISH-NOTES.md`. Also refuse if any chapter is not `status: final` unless forced.

## 1. Metadata and front/back matter

Write `publish/metadata.yaml`:

```yaml
title: ...
subtitle: ...
author: ...
lang: ko          # BCP-47
date: 2026-09-04
publisher: ...
rights: © 2026 Author. All rights reserved.
description: |      # 150-300 words, the back-cover copy
keywords: [..., ...]
cover-image: cover/cover.jpg   # only if the file exists
toc-title: 차례
```

Generate front matter files in `publish/frontmatter/`: title page, copyright page (include an AI-assistance disclosure line if the author wants one; Amazon KDP requires disclosure of AI-generated text at upload regardless), dedication (if any), epigraph (if any). Back matter: about the author, acknowledgments, further reading (nonfiction), glossary (technical), index of sources (academic).

Chapter files are the `drafts/` files with frontmatter stripped. Do not build from `edits/`.

## 2. Build

Requires `pandoc`. Check with `pandoc --version`; if missing, tell the author how to install and stop after writing metadata.

```bash
# EPUB
pandoc publish/frontmatter/*.md drafts/ch*.md publish/backmatter/*.md \
  -o publish/book.epub --toc --toc-depth=2 \
  --metadata-file=publish/metadata.yaml --css=publish/style.css \
  --epub-chapter-level=1

# PDF (requires xelatex; CJK needs a font)
pandoc ... -o publish/book.pdf --pdf-engine=xelatex \
  -V geometry:paperwidth=6in,paperheight=9in,margin=0.75in \
  -V mainfont="Noto Serif CJK KR" -V CJKmainfont="Noto Serif CJK KR" \
  --toc

# MOBI (optional; Kindle accepts EPUB)
ebook-convert publish/book.epub publish/book.mobi

# TXT, MD
pandoc ... --to plain --wrap=none -o publish/book.txt
pandoc ... --to markdown --standalone -o publish/book.md
```

Pre-processing:
- **Frontmatter strip**: pandoc treats the YAML block as metadata; concatenating many files makes later blocks collide. Strip every chapter's frontmatter into a temp copy before building.
- **Poetry**: add two trailing spaces to every non-empty line inside poem bodies so pandoc preserves line breaks.
- **Screenplay**: build PDF with a monospace font (Courier Prime) and no TOC; also export Fountain if requested.
- **Cover guard**: if `cover-image` points to a missing file, remove the key for the build and note it.
- **Images**: drafts reference `../visuals/figures/...` and `../visuals/illustrations/...`; run pandoc from the project root with `--resource-path=.:visuals:visuals/figures:visuals/illustrations:visuals/photos:publish`. Legacy `publish/illustrations/` still resolves if added to the path.

Validate: `epubcheck publish/book.epub` if installed. Zero errors required; warnings listed in `PUBLISH-NOTES.md`. Open the PDF page count and confirm chapter starts on new pages.

## 3. Title candidates

`publish/title-candidates.md`: 20+ candidates in five families (descriptive, emotional, question, image/metaphor, provocative), each with a subtitle option and a one-line reason. For Korean books, check whether the title is already in use on 교보/알라딘 when web search is available. Recommend three.

## 4. Visual assets and agents

- If `visuals/manifest.json` exists: `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs images render [project-dir]` (figures from source), then `images check`. Any failure blocks the build until fixed or the author defers the image. Prefer SVG figures for EPUB and PNG for PDF; pandoc picks by extension, so keep both and reference the SVG in drafts (the PDF build swaps to PNG via `--resource-path` order or a pre-processing pass).
- `cover-designer` (requires `art-bible.md`) → `publish/cover/concepts.md`, `spec.json`. If an image generation tool is available, execute the recommended concept and save `publish/cover/cover.jpg`; then rebuild EPUB with the cover.
- `art-director` → contact-sheet consistency review across interior images and the cover, recorded in `visuals/plan.md`. Publishing with an unresolved fix list requires an author override.
- `marketing-expert` → `publish/marketing-plan.md`; cover variants from `spec.json` feed the launch assets.

## 5. Platform checklists

Write `publish/CHECKLIST.md`:

**Amazon KDP** — EPUB (reflowable) or print PDF; cover 1600×2560 min for ebook; AI-content disclosure question answered honestly (text/images/translations); ISBN optional for ebook, required for expanded print distribution; categories (up to 3), keywords (7); description with allowed HTML; pricing and royalty tier (70% requires $2.99-$9.99 and delivery cost under limits); pre-order window.

**Korean platforms** — 교보문고 POD/전자책, 예스24, 알라딘, 리디, 밀리의 서재(구독): ISBN via 국립중앙도서관 서지정보유통지원시스템 (publisher registration required; individuals use 1인 출판사 등록 or an aggregator like 부크크/유페이퍼); 전자책 ePub 3 with embedded fonts checked; 표지 규격 per platform; 도서정가제 applies; 부가세 면세 for books.

**Apple Books / Google Play / Kobo** — EPUB 3, cover ratio, ISBN handling, territory pricing.

**Print** — trim size, bleed, spine width from page count and paper, PDF/X-1a for some printers, embedded fonts.

## Output

`publish/`: `book.epub`, `book.pdf` (+ `.mobi`, `.txt`, `.md` as requested), `metadata.yaml`, `style.css`, `frontmatter/`, `backmatter/`, `title-candidates.md`, `cover/`, `marketing-plan.md`, `CHECKLIST.md`, `PUBLISH-NOTES.md` (build log, warnings, overrides).

## Gate

EPUB and PDF built; epubcheck clean if available; metadata complete; title candidates, cover concepts, marketing plan, checklist present.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
