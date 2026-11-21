# Prior art survey

> Twenty-one existing PDF skills and plugins were read before this one was written. The point of the survey is to name what they do well, and the specific gap this package closes.

## 1. Method

Each candidate was read from its published source on 2026-11-13: the `SKILL.md` (or plugin manifest), the reference files, and the bundled scripts where they exist. Stars, last push date, and license are from the GitHub API at the same date. Where a repository has no license file, the entry says `none` and its code is treated as idea-only.

## 2. The table

| Repository | Stars | Last push | License | Approach | What it contributes | What it lacks |
|---|---|---|---|---|---|---|
| `anthropics` PDF skill collection | 193971 | 2026-11-06 | none | pypdf + pdfplumber + JS field scripting | The most complete form-filling flow of any candidate: discover fields, read them, fill, verify | Python runtime; no Korean typesetting; no structure-tree or language-tag check |
| `openai/skills` (.curated/pdf) | 28722 | 2026-10-28 | none | Tool routing in one file | Terse trigger and routing discipline: say which tool for which job | No implementation; no verification step |
| `anthropics/knowledge-work-plugins` (pdf-viewer) | 35630 | 2026-11-13 | Apache-2.0 | Viewer plugin | Shows a viewer as a separate capability from authoring | Read-only role; no generation |
| `github/awesome-copilot` (pdftk-server) | 41117 | 2026-11-13 | MIT | pdftk wrapper | Names the exact pdftk operations for merge/split/rotate | Requires a pdftk install; thin wrapper, no quality checks |
| `nexu-io/open-design` (pdf) | 107474 | 2026-11-13 | Apache-2.0 | Design-oriented export | Treats the PDF as a design deliverable with visual review | No extraction side; no accessibility |
| `tw93/Kami` | 12534 | 2026-11-10 | MIT | Document template system | Proof a template-driven not-browser path is viable for reports | Latin-first; no Korean line-break rules |
| `0xcjl/md-pdf-report` | 1 | 2026-07-29 | MIT | md → PDF with CJK fonts | Korean precedent: registers a CJK face and sets `word-break` | Markdown only; no extraction, no accessibility |
| `Straits-AI/pdf-skill` | 0 | 2026-07-17 | MIT | Extraction focus | Clear statement of extraction limits | No generation |
| `claude-office-skills/skills` | 574 | 2026-01-31 | MIT | Three narrow skills (extract/form/merge) | Splitting by operation keeps each contract small | No shared runtime; overlapping setup in each |
| `ComPDFKit/compdf-skills` | 110 | 2026-08-12 | none | Commercial SDK wrapper | Names the SDK-level operations (OCR, convert, sign) | Tied to a paid SDK; not runnable here |
| `Nebutra/MinerU-Skill` | 133 | 2026-09-24 | MIT | MinerU document parser | Strong layout-aware extraction for complex PDFs | Heavy model dependency; no generation |
| `ndpvt-web/latex-document-skill` | 828 | 2026-11-13 | none | LaTeX source generation | Highest-fidelity typography path when TeX is installed | Needs a TeX toolchain; not available here |
| `SidneyLYZhang/pdf-generation` | 1 | 2026-11-09 | MIT | Generation only | Minimal generation contract | No verification; no extraction |
| `yejinlei/pdf-ocr-skill` | 13 | 2026-04-20 | MIT | OCR pipeline | Shows OCR as a layer over the page, not a rewrite | OCR only |
| `vlebert/markdown-to-pdf-agent-skill` | 4 | 2026-07-17 | MIT | md → PDF | Simple, one-purpose contract | No quality checks |
| `hamzaabduljabbar/claude-pdf-markup-skill` | 16 | 2026-08-02 | NOASSERTION | Annotation and markup | Annotation coordinates as the core primitive | Annotation only; license unclear |
| `aliceisjustplaying/claude-skill-pdf-to-markdown` | 55 | 2025-11-29 | none | PDF → markdown | Concrete ordering rules for output markdown | No Korean or table-specific handling |
| `carboneio/carbone-agent-plugin` | 6 | 2026-11-12 | Apache-2.0 | Template engine plugin | Template + data separation as the generation model | Requires the Carbone service; Latin-oriented |
| `two4mamba/claude-skill-pdf-smart-ocr` | 2 | 2026-05-12 | MIT | OCR + routing | Routing to OCR only when the page needs it | No verification of the result |
| `molefrog/skills` | 170 | 2026-02-12 | MIT | Multi-skill collection | Skill boundaries stated by output shape | PDF not a focus |
| `formify-e-sign/formify-skills` | 5 | 2026-11-12 | MIT | E-signature flow | Signature fields as first-class | Service-backed; no local generation |

## 3. The gap this package closes

No surveyed candidate combines all five of these:

1. **Korean typesetting rules** as an explicit contract: prohibited line-start characters, particle attachment, `keep-all` behaviour, and the 1.6+ line-height range. The CJK precedents name a font but not the break rules.
2. **Font-embedding verification from the produced bytes** rather than from the input configuration. Most candidates set a font and stop; none reads back whether `FontFile2`/`FontFile3` landed.
3. **Structure tree and `/Lang` as a checked property**, with the specific loss named for each missing item. Accessibility is a section in most skills; it is a scanned invariant here.
4. **Two generation paths with an explicit routing rule**, so a data-driven contract never depends on a browser and a CSS-heavy design never pretends a spec composer can reproduce it.
5. **A zero-dependency runtime** on macOS frameworks. Every other candidate needs Python, a paid SDK, TeX, a model, or an external service — none runs on a stock machine with no installs.

## 4. Ideas taken, and what was written fresh

| Idea | Source | How it was used |
|---|---|---|
| Fill fields by discovering them first, then verifying the fill | `anthropics/skills` | `form` prints `fields[]` with no `--fill`; `--fill` reports `applied`/`missing` |
| Table recovery by intersecting drawn rules | `jsvine/pdfplumber` (library, not a skill) | Reimplemented on CoreGraphics page text and line queries; boundaries reported as inferred |
| Route to OCR only after a page check | `two4mamba/claude-skill-pdf-smart-ocr` | `check` emits `PAGE_NEEDS_OCR` with a page list before `ocr` runs |
| Treat the page image as the review surface | `nexu-io/open-design` | `render` is a mandatory gate, not an optional preview |
| Split by operation | `claude-office-skills/skills` | One engine with subcommands instead of separate skills, so the runtime is shared |

No source file was copied. Where a repository carries no license (`anthropics/skills`, `openai/skills`, `ComPDFKit/compdf-skills`, `aliceisjustplaying/claude-skill-pdf-to-markdown`, `ndpvt-web/latex-document-skill`), only the described behaviour was read and the implementation here is independent.

## 5. What was deliberately not built

| Not built | Why |
|---|---|
| Python extraction stack | A stock machine here has no Python PDF libraries; requiring one narrows who can run this |
| PDF/A or PDF/UA certification | Certifying conformance needs a validator and a human review; claiming it without either is false |
| Embedded JavaScript execution | A PDF action is untrusted input; the scan reports it and never runs it |
| AES-256 encryption | PDFKit exposes RC4 128-bit only; the command says so rather than implying more |
| Structure-tree repair of third-party PDFs | A rebuilt tree over a wrong content stream claims structure the content does not have |

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Repository metrics, push dates, licenses | GitHub REST API `GET /repos/{owner}/{repo}`, queried 2026-11-13 |
| `anthropics` PDF skill structure | <https://github.com/anthropics/skills> |
| Table recovery approach | <https://github.com/jsvine/pdfplumber> |
| Tagged PDF and structure-tree requirements | <https://pdfa.org/resource/pdfa-2/> |
| Korean line-breaking standard | <https://www.w3.org/TR/klreq/> |

### Evidence grade

`MEASURED` for every star count, push date, and license in §2, taken from the GitHub API on 2026-11-13. `LOCAL` for the gap analysis and the reuse table, both derived from reading each `SKILL.md` on that date. The metrics move; re-query before quoting them as current.