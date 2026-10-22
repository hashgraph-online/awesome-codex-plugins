---
name: firecrawl-parse
description: |
  Efficiently extract and convert the contents of any local file—such as PDF, DOCX, DOC, ODT, RTF, XLSX, XLS, or HTML—into clean, well-formatted markdown saved to disk. Use this skill whenever the user requests to parse, read, or extract information from a file on their computer, including phrases like “parse this PDF”, “convert this document”, “read this file”, “extract text from”, or when a local file path (not a URL) is provided. This skill offers advanced options like generating AI-powered summaries and answering questions based on the file's content. Prefer this tool over `scrape` when handling local files to deliver precise, structured outputs for downstream tasks.
---

# firecrawl parse

Turn a local document into clean markdown on disk. Supports **PDF, DOCX, DOC, ODT, RTF, XLSX, XLS, HTML/HTM/XHTML**.

## When to use

- You have a file on disk (not a URL) and want its text as markdown
- User drops a PDF/DOCX and asks what it says, or to summarize it
- Use `scrape` instead when the source is a URL

## Quick start

Always save to `.firecrawl/` with `-o` — parsed docs can be hundreds of KB and blow up context if streamed to stdout. Add `.firecrawl/` to `.gitignore`.

```bash
mkdir -p .firecrawl

# File → markdown
firecrawl parse ./paper.pdf -o .firecrawl/paper.md

# AI summary
firecrawl parse ./paper.pdf -S -o .firecrawl/paper-summary.md

# Ask a question about the doc
firecrawl parse ./paper.pdf -Q "What are the main conclusions?" \
  -o .firecrawl/paper-qa.md
```

Then `head`, `grep`, `rg` etc., or incrementally read the file - don't load the whole thing at once.

## Options

| Option                 | Description                             |
| ---------------------- | --------------------------------------- |
| `-S, --summary`        | AI-generated summary                    |
| `-Q, --query <prompt>` | Ask a question about the parsed content |
| `-o, --output <path>`  | Output file path — **always use this**  |
| `-f, --format <fmt>`   | `markdown` (default), `html`, `summary` |
| `--timeout <ms>`       | Timeout for the parse job               |
| `--timing`             | Show request duration                   |

## Tips

- Quote paths with spaces: `firecrawl parse "./My Doc.pdf" -o .firecrawl/mydoc.md`.
- Max upload size: **50 MB** per file.
- Credits: ~1 per PDF page; HTML is 1 flat.
- Check `.firecrawl/` before re-parsing the same file.
- To check your credit balance (recommended for batch processing and similar workflows), use the `firecrawl credit-usage` command.

## See also

- [firecrawl-scrape](../firecrawl-scrape/SKILL.md) — same idea for URLs
