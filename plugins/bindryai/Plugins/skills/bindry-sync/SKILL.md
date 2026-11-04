---
name: bindry-sync
description: Compile a bound Bindry Binder into Codex skills for this project, so its Skills load on demand instead of sitting in every prompt. Use when the user asks to sync, install, or update Bindry Binder skills for this project.
---

Compile a Bindry Binder into Codex skills so its Skills load on demand instead of sitting in every prompt.
Invoke explicitly with `$bindry-sync`, or let it trigger automatically when the user asks to sync/update Bindry
skills.

1. Determine the source from what the user actually said, in order:
   - A Binder id (GUID) or a full export URL they gave you — sync live from the Bindry API.
   - A file path they gave you — compile from that local export file.
   - Neither given: check for `./bindry.config.json` in the current project (written by a previous sync) and
     reuse the Binder id it remembers.
   - None of those apply — ask the user for a Binder id (from Bindry → Binder → Export → target "codex") or a
     saved export file path, then stop.
2. For a live sync, also need `--api-base <url>` (the Bindry API's base URL — ask the user if not obvious from
   context) and, for a private Binder, `--token <api-key>` (generated from the workspace's team page in Bindry,
   not Account settings). A published Library Binder (referenced by slug or GUID) needs no token at all — it
   resolves through the public Library's anonymous export route. Only your own private Binders require one.
3. Default is `--mode pinned` (a static snapshot). If the user wants this Binder to always stay current instead
   — `--mode live` — first confirm the Bindry MCP server is connected (check the configured MCP servers for one
   named `bindry`). If it isn't connected, tell the user to use the `bindry-connect` skill first and stop;
   compiling live skills with no live connection would produce skills that always fail when used. `--mode live`
   also only works from a live Binder id/URL, not a local export file — its Skills need real GUID ids, which a
   hand-written or example export file won't have.
4. If the user wants a specific published version of a Library Binder rather than its latest — e.g. rules for
   the framework release they are actually on — pass `--version <v>`. It is remembered in
   `bindry.config.json`, so later syncs stay on that version until `--version latest` removes the pin. A
   version pin only applies to a Library Binder (your own workspace Binder always compiles from its current
   composition), and an unknown version fails with a message naming the versions that do exist rather than
   quietly serving the latest.
5. Locate this plugin's own installed root first (e.g. list installed Codex plugins and find the path for
   `bindry@<marketplace>`), then run:
   `node <resolved-plugin-root>/scripts/compile-binder.mjs [<binder-id-or-file>] --out .agents/skills [--api-base <url>] [--token <api-key>] [--mode pinned|live] [--version <v>]`
   If you can't locate `scripts/compile-binder.mjs` under this plugin's installed root, stop and say so plainly
   rather than guessing a path.
6. Report exactly what the script printed: how many skills were written and where. If it failed with an
   authentication error, tell the user plainly what it said — don't guess or retry silently. If it wrote a
   `bindry.config.json`, mention that future syncs in this project can omit the Binder id (and remember the mode
   too).
7. Remind the user to re-run this whenever a **pinned** Binder changes in Bindry — each pinned skill is tagged
   with a Skill version in an HTML comment, so the `bindry-check` skill can diff against it. A **live** skill
   never goes stale — it calls the Bindry MCP server for current content every time it's used — so there's
   nothing to re-sync for it, only re-run if the Binder's Skill *list* itself changed (added/removed Skills).
8. If any Skill carries a file attachment (e.g. an exact logo to place), the script downloads it into that
   skill's `assets/` folder alongside `SKILL.md` — in both pinned and live mode, since the live MCP tools don't
   serve binary files. If the script printed a warning that it skipped an asset, mention that plainly too —
   that skill still compiled, just without the file, and needs an `--api-base`/network fix before it will
   download.
