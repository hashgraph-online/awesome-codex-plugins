---
name: centricmem-agent
description: "Organises and retrieves Markdown memory on the hosted CentricMem librarian (search, notes, decisions, transcripts). Use when starting a session, resuming after context compress / checkpoint / new chat, filing Non-Micro work, searching project memory, connecting an agent key, or refreshing this Skill. On session start, compare the loaded copy (see REFERENCE Skill refresh) against cm_health / ambient skill_latest and refresh if stale."
license: PolyForm-Noncommercial-1.0.0
compatibility: "Requires host MCP at https://mem.centricmem.com/mcp. CLI >=0.21.50: every card is summary + key points (a keep stub is not a card); a folder is cm_keep card:false then cm_import items. Archive zip is optional. share: shelf ids; cm_move selected cards (whole paths, not lessons.md or #); cm_delete {file,shelf} a card (heading= for ##); cm_rename {file,shelf,title} a card. Omit cm_library id to list. Codex OAuth needs librarian >=0.21.51. OAuth key picker / ChatGPT Approve hop: librarian >=0.21.56. Applicant HTTPS callbacks: librarian >=0.21.55. skipExisting / copy-aside FTS skip need librarian >=0.21.50."
metadata:
  version: "1.0.5"
  compatible_cli: ">=0.21.50"
  changelog_url: https://github.com/zeyu-j/centricmem-skill/blob/main/CHANGELOG.md
---

# CentricMem Agent Skill v1.0.2

**Names:** product/CLI = `centricmem`; GitHub install package = `centricmem-skill`; this Agent Skill folder = `centricmem-agent` (keep that folder name — it is not a second product).
Handover (when / loop). Schemas win. Branches: [REFERENCE.md](REFERENCE.md).
**Library** → **Shelf** → **Card** (summary + key points). No Inbox / `unclassified`. One key = grants. Never paste keys in chat (REFERENCE **Bearer: where plaintext is OK vs not** — claim may write a private local MCP file; docs/plans use `${VAR}` or URL-only).
**Style** of a card (voice, length, evidence density) is yours + this agent's — not a CentricMem house voice. Structure only: REFERENCE **Card contract**.

## Do not (full list: REFERENCE)

- Don't wait for "log this" / close / wrap up to file a finished chunk — sweep before you yield (§4)
- Don't write `unclassified` — pick or create a named shelf
- Don't put secrets / keys in cards, and never ask the human to paste a key or transcript in chat
- Never echo a credential value. Confirm a key with a fingerprint, not the value (`9352... len=64 fp=5E4ED29C`); never dump `mcp.json` / `config.toml` / `*.env` whole, and never redact by length threshold (short keys slip through). If a key reaches the transcript, say so in that turn and rotate it. Details: REFERENCE **Never echo a credential (agent side)**.
- Don't stop after a title-only card — every card needs summary + key points
- Don't treat this git checkout as the memory disk

## When to Use

Start or resume; search; file Non-Micro; connect / refresh Skill. Recipes: REFERENCE.

## 0. Reach

1. MCP only `https://mem.centricmem.com/mcp`: `cm_health` `cm_ambient` `cm_doctor` `cm_search` `cm_show` `cm_note` `cm_log_decision` `cm_done` `cm_keep` `cm_library` `cm_copy` `cm_move` `cm_delete` `cm_rename` `cm_import` `cm_index`. No curl / CLI-write / bootstrap.
2. Missing tools or short grants → **connect this turn**. REFERENCE **Reach**. Remote/cloud is **not** “paste key only”: OAuth if this agent receives the browser login; paste Bearer only when it cannot. Listed OAuth hosts only: an unlisted callback shape leaves the host stuck on “connecting”, so prefer `/connect?device=` and send that callback shape to zeyu@poppyg.com (REFERENCE “Approved, but the agent stays connecting”).
3. `cm_show` = card on the **hosted** shelf (not a local junction file). `grants=["*"]` = default. Extra `mode=read` = view-only (search/show only). `ACADEMIC.md` beside this → follow it. Upsert corpus paths: REFERENCE **Import shapes** (`bundle.imported` + `rel_path`, never bare `items=`).
4. **Writes — `items=` and `bundle` are different contracts.** `cm_note` / `cm_log_decision` / `cm_done` file cards; `cm_import` with `items=` (or `package.items`, or a zip) adds **new cards under `imported/kept/`** and nothing else. `cm_import` with **`bundle: {version: 1, …}`** is the full ImportBundle and **also writes library files**: `context` → the shelf's **`active_context.md`** (current focus, overwritten), `rules` → **`AGENTS.md` Global Rules**, plus `decisions` / `lessons` / `sessions` / `imported` / `research`. A key that can open the shelf can write those — it is **not** host-only. An unknown or mistyped top-level slot is **`400 BAD_IMPORT_BUNDLE`** (it names the slot and the allowed list), never a silent drop. Slot table: REFERENCE **Writes**.

## 1. Classify

| Skip (Micro) | Sweep (Non-Micro) |
|---|---|
| Typo, one-liner, no durable fact | Implement, ops, research, architecture, decision |
| | ≥2 real turns **or** one turn that shipped / decided |

## 2. Start

Prefer `cm_ambient` with **`shelf=`** (or `library=`) first — it already carries grants / mode / skill_latest / Recent / Session. That shapes **Recent decisions / Session tail / Curate**, not only later write routing. Ambient with only an unmatched `cwd` and no `shelf=` often shows empty Recent/Session — that is not “the shelf is empty.” Call `cm_health` only when tools are missing, connect is needed, or ambient is unhealthy / unreachable. Unreachable: say once — no bootstrap. Named shelf for writes.

**Resume = new session.** Compress, checkpoint restore, or new chat on same task → ambient first (health only if needed).

Once after ambient (or health): refresh if `skill_latest` newer. **Load path ≠ refresh path** — read the version of the copy **this host loads**, not a sibling skills dir (plugin-tree hosts: `<host-plugins-dir>/centricmem-skill/package.json`; npx `-g` / `~/.agents` does not update that tree). Install morphologies + hosts outside them: REFERENCE Skill refresh — adapt, do not invent a fourth shared hub. After a disk refresh: **re-read this SKILL.md and Do not** before the next write — installing newer ≠ acting on it. Name the key once (`mode=read` → view-only). Don't log → skip sweep. Empty shelf once: REFERENCE Existing memory.

## 3. During

**chunk** = accepted unit (verified fragment, locked decision, evidenced lesson, delivery). Any in this reply → same-turn sweep. Not the whole task.
**yield** = any reply end (incl. progress).

Search/show/ambient while working. Hold half-finished. **Chunk done → sweep before you yield.**
Cards need summary + key points. Keep stubs ≠ cards. File/folder: REFERENCE Writes. Voice/density: theirs + yours (REFERENCE **Card contract**), not a CentricMem template.

## 4. Sweep — single source

No wrap-up wait. Agent close does not run this. Don't log / Skill done → skip.

**Gate:** Non-Micro chunk this reply, zero `cm_*` this session, no Don't log → **sweep before you yield**.

| File now | File at wrap-up |
|---|---|
| Locked decision; method-changing lesson; finished chunk | Version-tied stats; unverified conclusions |

Same `lessons.md` title → 409; rewrite = `cm_delete` then write (REFERENCE). Early wrong write costs more.

MCP down: hold **CentricMem deferred sweep**; connect (REFERENCE); file after health.

`shelf=` / `library=` (REFERENCE **Shelf routing**):

1. Transcript plaintext exists → Shell-read → `cm_keep` (no paste / `path=`). Else skip keep.
2. Same batch: `cm_note` / `cm_log_decision` / `cm_done` (+ `attach`) as needed.
3. Copy/move/delete/rename leftovers: REFERENCE Writes.

## 5. Optional host hooks

**Baseline = this Skill + host MCP (`cm_*`).** Hooks / `AGENTS.md` / Stop scripts are **optional enhancements**, not install prerequisites.

- No hook support (DSH, some cloud agents) → still full use: §2 ambient, §4 sweep. Missing hooks is not an error.
- This Skill does **not** require hook config; hooks do **not** replace §4 (scripts default to session-only; knowledge cards still need the model + this Skill).
- Install recipes (private client `integrations/`): L1 `AGENTS.md` snippet, L2 Stop remind (Cursor / Claude / Codex), L3 session-sweep (guest HTTP Bearer). Details: REFERENCE **Optional host hooks**.

## Typical Workflows

Connect: REFERENCE. **Daily:** §2 → work → §4 before yield. Empty shelf: REFERENCE Existing memory.
