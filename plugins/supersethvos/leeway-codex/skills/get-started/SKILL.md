---
name: get-started
description: Connect Codex to a Leeway drive and make the first save. Use right after the Leeway plugin is installed, when the person asks to connect or set up Leeway, or when a Leeway tool answers UNAUTHENTICATED.
---

# Get started with Leeway

Leeway is a drive the person shares with their team and their agents. Its tools are on the `leeway` MCP server at `https://leeway.to/mcp`.

## Connect

1. If the Leeway tools aren't available or answer `UNAUTHENTICATED`, the server needs signing in. In the Codex CLI that is `codex mcp login leeway`; in the Codex app, open the Leeway plugin and choose Connect. A browser opens at leeway.to.
2. In that browser the person signs in with their passkey, or makes a free drive (50 GB) on the spot. They then choose the drive or one folder in it, and what Codex may do there: read, write, workspaces, publish, history.
3. Back in Codex, call `get_discovery`. It says which drive this is, the name Codex's changes carry in history, the folder this connection sees as `/`, and the scopes it was given. Tell the person what you can do there, in one line.

## First save

A new drive is empty. Offer to put something in it, for example a short summary of this session at `/Notes/summary.md`:

1. `make_folder` with path `/Notes` (fine if it's already there).
2. `write_file` with path `/Notes/summary.md`, the text as content, and `if_none_match` set to `*` so nothing already there is replaced.
3. Answer with the path and the `rev` from the result. The file is now in the person's Leeway folder on every computer they've connected.

## Good to know

- Paths start at `/`, the top of what this connection may see. A folder connection sees only that folder.
- A tool that needs a scope this connection wasn't given answers `FORBIDDEN` with `details.scope`. Say which scope is missing; the person can connect again and allow it.
- Removing Codex at https://leeway.to/activate?people ends its access at once.
- For the drive's working rules, see the other Leeway skills: save-to-drive, find-in-drive, history-and-undo, workspace-publish and handoff-note.
