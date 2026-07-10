# Capability Card Schema

Capability cards are routing hints. They are not the source of truth and must preserve provenance.

Required fields:

- `id`: stable identifier, lower-case kebab-case where possible.
- `name`: human-readable capability name.
- `kind`: `skill`, `plugin`, or `connector`.
- `categories`: list of routing categories.
- `use_when`: short text describing positive triggers.
- `avoid_when`: short list of negative triggers.
- `inputs`: likely input sources or file types.
- `outputs`: likely output artifacts.
- `requires`: required access or execution capability.
- `examples`: short positive example prompts.
- `provenance`: source metadata.
- `updated_at`: source file modified time if known.

Recommended categories:

- `process`: planning, debugging, TDD, verification, review, orchestration
- `source`: local, web, github, gmail, drive, notion, slack, figma, linear
- `artifact`: code, web_app, document, spreadsheet, presentation, pdf, image, dashboard
- `domain`: frontend, ios, data, finance, sales, design, devops, research
- `risk`: read_only, writes_files, external_connector, requires_auth, network, destructive_possible

Example:

```json
{
  "id": "pdf",
  "name": "PDF",
  "kind": "skill",
  "categories": ["artifact", "local", "pdf", "read_only"],
  "use_when": "Use for reading, creating, rendering, or reviewing PDF files.",
  "avoid_when": ["Do not use when final output is a slide deck and PDF is only an input."],
  "inputs": ["pdf"],
  "outputs": ["text", "pdf", "rendered_pages"],
  "requires": ["filesystem"],
  "examples": ["Summarize this PDF.", "Render this PDF and check layout."],
  "provenance": {
    "source_type": "skill",
    "path": "/absolute/path/to/SKILL.md"
  },
  "updated_at": "2026-06-04T10:00:00+08:00"
}
```
