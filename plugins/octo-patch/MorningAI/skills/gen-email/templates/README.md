# gen-email Templates

Email rendering uses **inline-CSS HTML** generated from `lib/email_template.py`. The actual templates are embedded in that Python module to avoid filesystem lookup overhead and keep the skill zero-dependency.

This directory exists for future template overrides. Currently contains:

- `subject_examples.md` — sample subject-line templates per language

## Customizing the email body

Edit `lib/email_template.py` directly:

- `_HTML_TEMPLATE` (string.Template) — outer HTML shell with header/footer
- `_HTML_ITEM` — per-item card block
- `LANG_TEXT` — language-specific labels (header count, footer, unsubscribe text)
- `_accent_for_score` — left-border color by importance

The HTML uses table-based layout and inline CSS for compatibility with Gmail, Outlook, QQ Mail, Apple Mail, and major mobile clients.

## Why no separate `.html` template file?

Loading external template files would require:
1. Skill-root path resolution (mirroring `lib/env.py:find_skill_root`)
2. File I/O on every send
3. Validation / fallback logic

For a single, stable HTML structure this is over-engineering. If you need radically different layouts per recipient or per region, extend `lib/email_template.py` to dispatch by config rather than introducing a template file system.
