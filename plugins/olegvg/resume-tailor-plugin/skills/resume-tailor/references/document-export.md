# Export a clean, inspectable resume

Read this only for file generation or file QA. Use the requested path and format; editing a summary in chat does not require an export workflow. Deliver a real DOCX when asked for DOCX. Renaming a PDF or HTML file is not conversion.

## Prepare the final content

Separate the resume from internal review before generation. For a legacy Markdown draft, use the content **before the first** `<!-- ATS-ANALYSIS-START -->`; do not export the marker or following analysis. Remove unresolved template slots, drafting notes, source/conflict tables and excluded-role explanations. Required material uncertainty must be resolved, omitted or accurately qualified, not hidden by cleanup.

Use public names and permitted details. Apply output-scoped changes such as omitted languages without editing the master. Remove whole unused sections rather than leaving empty headings. Use ordinary paragraphs, headings and bullets with contacts in the document body.

Select A4 or Letter from recipient instructions and target context, independently of language. Start around 10.5–11pt body text with readable contacts/technology lines; shorten redundant content before shrinking type. Combine short related lists, such as languages, into one paragraph when that improves pagination. Page targets guide editing, not factual omissions or a universal ATS cutoff. Keep headings with their first paragraph; allow a long role to break across pages rather than forcing its entire container onto one page.

## HTML to PDF

Copy the selected HTML template to the requested output location and replace its slots with escaped text. Duplicate only the needed role/bullet/category prototypes. Remove unused optional sections. Photo is absent by default; add a supplied photo when requested or required by verified recipient instructions, while respecting explicit user exclusions. Keep sequential body text; the supplied templates are starting points, not an automatic Markdown renderer.

Core drafting needs no export dependency. For PDF, use an available HTML-to-PDF tool. WeasyPrint is an optional route requiring its Python package and the native libraries/fonts needed on the current operating system. For DOCX, `python-docx` is optional; visual QA also needs an available document renderer. Check the environment before selecting a route. Installation, dependency/configuration changes and remote uploads are separate actions, not implied by an export request.

Copy templates from this installed skill's `references/` directory; generated sources, PDFs and QA files belong in the user's chosen workspace or an appropriate temporary directory. Use the user's existing runtime and package manager when available. No repository layout, `uv`, Homebrew, desktop runtime, hardcoded cache or global installation is required.

If the selected interpreter already has WeasyPrint, invoke it with the actual input/output paths; for example:

```bash
python -m weasyprint "/chosen/workspace/resume-target.html" "/chosen/workspace/resume-target.pdf"
```

`python` here means the selected environment's interpreter. Module invocation avoids a stale console-script interpreter path. If an established `uv` environment is present, its existing offline/no-sync invocation can be used; do not require it or alter dependencies. On macOS, a missing native-library error may require a command-local library lookup setting pointing at an existing, verified directory; do not universally prescribe a Homebrew path or change global settings. Follow current tool documentation when diagnosis needs it.

When the required runtime is unavailable, preserve the clean source and report the specific limitation or use another supported export tool. Do not claim a PDF was generated until the command succeeded and the resulting file was inspected. [Current WeasyPrint documentation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

## Native DOCX

Use available document tooling and its document skill when present. When a desktop runtime discovery tool such as `load_workspace_dependencies` is available, it can locate bundled libraries; otherwise use the available local runtime. These integrations are optional. Avoid hardcoded paths to a particular user's runtime cache.

A `python-docx` implementation should create a fresh `Document`, set paper/margins and paragraph styles, and add the selected content directly as native body paragraphs. Use `add_heading`, `add_paragraph` and `List Bullet` for structure. Historical role/title/date lines are ordinary readable paragraphs. Do not use layout tables, floating text boxes, or Word headers for essential information.

A minimal content adapter can consume ordered `(kind, text)` blocks populated with the actual approved text:

```python
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.oxml.ns import qn


def export_docx(blocks, output, paper="A4"):
    doc = Document()
    section = doc.sections[0]
    width, height = {"A4": (210, 297), "Letter": (215.9, 279.4)}[paper]
    section.page_width, section.page_height = Mm(width), Mm(height)
    section.top_margin = section.bottom_margin = Mm(18)
    section.left_margin = section.right_margin = Mm(18)
    sizes = {"Normal": 11, "List Bullet": 11, "Title": 22,
             "Heading 1": 12, "Heading 2": 11}
    for name, size in sizes.items():
        style = doc.styles[name]
        style.font.name, style.font.size = "Arial", Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.widow_control = True
    for name in ("Normal", "List Bullet"):
        doc.styles[name].paragraph_format.space_after = Pt(4)
        doc.styles[name].paragraph_format.line_spacing = 1.12
    for name in ("Title", "Heading 1", "Heading 2"):
        style = doc.styles[name]
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(8)
        style.paragraph_format.space_after = Pt(4)
    # Some default templates carry a decorative Title paragraph border.
    title_properties = doc.styles["Title"]._element.find(qn("w:pPr"))
    if title_properties is not None:
        for border in list(title_properties.findall(qn("w:pBdr"))):
            title_properties.remove(border)
    for kind, text in blocks:
        if kind == "name":
            doc.add_heading(text, 0)
        elif kind == "heading":
            doc.add_heading(text, 1)
        elif kind == "role":
            doc.add_heading(text, 2)
        elif kind == "bullet":
            doc.add_paragraph(text, style="List Bullet")
        else:
            paragraph = doc.add_paragraph(text)
            if kind == "contact":
                for run in paragraph.runs:
                    run.font.size = Pt(10)
            if kind == "meta":
                paragraph.paragraph_format.keep_with_next = True
    doc.save(output)
```

This is a structure adapter, not a Markdown parser or fact-selection engine. Keep review outside `blocks`; populate them only with permitted final content. Use `meta` for short company/date/engagement lines and `contact` for contacts. Check the actual default template for inherited borders, theme colors and font fallbacks/Cyrillic. The border cleanup uses low-level OOXML and should be reverified after a library/template change. If modifying an existing DOCX, preserve unrelated styles/content rather than rebuilding it blindly. [python-docx text](https://python-docx.readthedocs.io/en/latest/user/text.html), [sections](https://python-docx.readthedocs.io/en/latest/user/sections.html).

## Verify the actual artifacts

| Check | What to inspect |
|---|---|
| Creation | Requested file exists, opens in its real format, and contains no unfilled slots or review. |
| Text and order | Names, contacts, Cyrillic/accents, role/company/date associations, bullets and section order survive extraction. Reopen DOCX paragraphs; use available PDF text extraction. |
| Visual pages | Render and inspect every page for clipping, overlap, font substitutions, crowded type, large avoid-break gaps, and orphan headings. |
| Content fidelity | Dates, metrics, contribution, optional sections and scoped overrides agree with the selected source. |
| Portal behavior | Inspect actual autofill only when accessible and application/profile work is authorized. Local extraction cannot establish this. |

Render DOCX through the available document renderer; a separate HTML-derived PDF does not verify DOCX pagination. For PDF, available tools include `pdftotext`, `pdftoppm`, and PyMuPDF. Use only available runtimes; do not label absent tools or an unperformed render “passed”.

Report **passed / issue / not checked / not applicable** for the relevant checks, with actual observations. Correct issues and repeat affected checks. Link requested deliverables with absolute paths. Clean Markdown/HTML can remain as a source when requested; QA fixtures and internal analysis are not extra deliverables.
