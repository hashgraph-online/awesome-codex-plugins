# Runtime and Verification

What this machine can actually do, how to prove a document is right, and how to say what was not proven.

## 1. Probe before claiming

`python3 assets/tools/hyper_docx.py doctor` prints one JSON object. It reads the interpreter, then searches for a Chromium-family binary and LibreOffice, then derives the capabilities:

| Capability | Needs | Meaning when missing |
|---|---|---|
| `build`, `inspect`, `verify`, `tracked_changes`, `comments` | Python 3.8+ only | never missing; these are standard library |
| `html_render` | Python 3.8+ | never missing |
| `pdf_render` | a Chromium-family binary | HTML proof only; no PDF, no page image |
| `docx_to_pdf` | LibreOffice (`soffice`) | no Word-engine conversion; the HTML render is the only layout proof |
| `png_preview` | LibreOffice or QuickLook (`qlmanage`) | no preview image |
| `docx_to_text` | `textutil` on macOS, otherwise the standard library reader | the built-in `text` command always works |

The probe finds the browser in the Playwright cache (`~/Library/Caches/ms-playwright`, `~/.cache/ms-playwright`) and in the usual application paths. Result on 2026-11-13 on this machine: Python 3.9.6, a Playwright `chrome-headless-shell`, `textutil`, `qlmanage`, and `sips`; no LibreOffice. So `pdf_render` yes, `docx_to_pdf` no.

Never install a package or an application to make a check possible. A missing capability is reported, not solved by the skill.

## 2. Proof surfaces, strongest first

| Surface | What it proves | What it does not |
|---|---|---|
| Word or Pages opened the file | the file opens without a repair prompt, fields evaluate | nothing on this machine; needs the user |
| LibreOffice conversion to PDF | the package parses in a second, independent office engine | not Word's layout engine |
| HTML render printed to PDF | content, page box, margins, table widths, indents, page breaks | not Word's line breaking or font shaping |
| Page image from the PDF | the reader sees what the spec described | a proof of appearance, not of Word fidelity |
| `verify` | structural validity: parts, types, relationships, styles, anchors, geometry | nothing about appearance |
| Text extraction | the words and their order | nothing about layout |

`render --pdf` writes an HTML page whose `@page` size equals the document's page size, with the margins as padding, then prints it with the headless browser. That is a faithful proof of the numbers the file stores. It is not a proof that Word breaks lines at the same places — Word's own line-breaking and font shaping differ.

## 3. `verify` check meanings

| Check | Fails when | Usual cause |
|---|---|---|
| `xml-wellformed` | a part will not parse | a hand-edited part with an unclosed tag |
| `document-part` | the main document part is missing | a relationship target typo |
| `content-types` | an override names a missing part, or a media part has no default extension | adding a part without calling `ensure_override` |
| `relationship-targets` | an internal target does not resolve | a target written relative to the package root instead of the owning part |
| `styles-resolve` | a paragraph names a style id that is not defined | building a paragraph with `pStyle` but not declaring the style |
| `images` | a relationship points at a missing part, a blip has no relationship, an extent is zero or wider than the page, or an extent implies absurd resolution | a path read after the file moved; an extent written in twips instead of EMU (1 mm = 36000) |
| `comment-anchors` | a comment has no range, or a range has no comment | a comment written without its start/end pair |
| `placeholders` | `TODO`, `TBD`, `FIXME`, `XXX`, or lorem text survives in the body | a draft spec delivered as final |
| `geometry` | page size or a margin differs from the spec by more than 2 twips | a spec edited after the build |
| `length` | the body has fewer characters than `min_chars` | a truncated build or an empty block list |

`skipped` is not `pass`. The geometry check reports `skipped` when no spec is supplied, and a report that counts a `skipped` check as green is wrong.

## 4. Independent read

A second reader catches what a self-check cannot: a missing part, a broken relationship, a style the reader ignores. On this machine:

```bash
textutil -convert txt -stdout out.docx | head -40      # macOS, always present
python3 -c "import docx; d=docx.Document('out.docx'); print(len(d.paragraphs), len(d.tables))"   # when python-docx is installed
```

Neither is installed by the skill. When neither is available, the built-in `text` command is the reader, and the report says so — a self-read is weaker evidence than an independent one and must be labelled that way.

## 5. When a reader says the file is broken

Run `verify` first. The failing check names the part, and that is the whole diagnosis in almost every case:

| Reader symptom | Check to read first |
|---|---|
| "Word found unreadable content" | `content-types`, then `relationship-targets` |
| Images show as a red X | `images` |
| A picture renders as a sliver | `images` — an extent written in twips shrinks the drawing 17-fold |
| Comments vanished | `comment-anchors` |
| Text looks like a different font | not a verify failure; read `w:rFonts` in the run properties |
| Table borders missing in a previewer | not a package defect; the previewer drops style-only borders — set `tblBorders` explicitly |
| Page breaks in the wrong place | `geometry`, then the paragraph that carries `pageBreakBefore` |

A previewer that draws a table without borders while Word draws it with borders is a previewer limitation, not a package defect: verify the XML carries `tblBorders` before changing anything.

## 6. Reporting a gap

Say what was proven and how, then say what was not, in one line each:

- "verify 통과, HTML 렌더 PDF로 여백·표 폭 확인. Word 실물 렌더는 이 기기에 LibreOffice가 없어 확인하지 못했습니다."
- "폰트 모양은 대체 폰트로 렌더되어 확인하지 못했고, 크기·굵기·줄간격만 확인했습니다."

A gap stated plainly is worth more than a claim that cannot be reproduced.

## Sources

> Checked 2026-11-13

- python-docx installation and reader behavior — https://python-docx.readthedocs.io/
- Microsoft Learn, Open XML package and content-type rules — https://learn.microsoft.com/en-us/office/open-xml/word/
- Chromium headless printing and its `--print-to-pdf` behavior — https://developer.chrome.com/docs/chromium/headless
- ECMA-376, package relationships and part resolution — https://ecma-international.org/publications-and-standards/standards/ecma-376/
