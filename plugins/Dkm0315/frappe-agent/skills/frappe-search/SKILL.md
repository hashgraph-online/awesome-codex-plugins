---
name: frappe-search
description: Frappe-specific search and discovery guidance for finding benches, apps, remotes, sites, ports, hooks, DocTypes, builder DocTypes, and frontend surfaces quickly. Use when the task starts with locating or classifying Frappe context.
---

Search like a Frappe operator, not a generic grep user.

Look for:
- bench roots
- `apps.txt`
- `common_site_config.json`
- `hooks.py`
- DocType folders
- `www` pages
- client or server scripts
- report, workspace, dashboard, and print-format definitions
- app remotes and branch markers

Prefer:
- `rg --files`
- `rg`
- focused file inspection
- config and manifest discovery before code edits

When searching, summarize:
- what was found
- what type of Frappe surface it is
- whether it is official, custom-derived, or custom
- what the safest next step is

