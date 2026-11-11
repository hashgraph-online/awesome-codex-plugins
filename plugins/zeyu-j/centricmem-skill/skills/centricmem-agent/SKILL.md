---
name: centricmem-agent
description: "Organises and retrieves Markdown memory on the hosted CentricMem librarian (search, notes, decisions, transcripts). Use when starting a session, resuming after context compress / checkpoint / new chat, filing Non-Micro work, searching project memory, connecting an agent key, or refreshing this Skill. On session start, compare the loaded copy (see REFERENCE Skill refresh) against cm_health / ambient skill_latest and refresh if stale."
requirements:
  mcps:
    - centricmem
license: MIT
compatibility: "Requires host MCP at https://mem.centricmem.com/mcp. Floors use the pre-1.0 0.21.x numbering; every 1.0.x satisfies them all. librarian >=0.21.50: a card is summary + key points (a keep stub is not a card); a folder is cm_keep card:false then cm_import items; archive zip is optional; share: shelf ids; cm_move takes whole paths (never lessons.md or #); cm_delete {file,shelf} a card, heading= for one ##; cm_rename {file,shelf,title}; omitting the cm_library id lists shelves; skipExisting and copy-aside FTS skip. >=0.21.51 Codex OAuth. >=0.21.55 applicant HTTPS callbacks. >=0.21.56 OAuth key picker and the ChatGPT Approve hop. >=1.0.6 host-ops detail (cm_ops)."
metadata:
  version: "1.0.42"
  compatible_cli: ">=0.21.50"
  changelog_url: https://github.com/zeyu-j/centricmem-skill/blob/main/CHANGELOG.md
---

# CentricMem Agent Skill

**Names:** product/CLI = `centricmem`; GitHub install package = `centricmem-skill`; this Agent Skill folder = `centricmem-agent` (keep that folder name — it is not a second product).
Handover (when / loop). Schemas win. Branches: [REFERENCE.md](REFERENCE.md).
**Library** → **Shelf** → **Card** (summary + key points). No Inbox / `unclassified`. One key = grants. Never paste keys in chat (REFERENCE **Bearer: where plaintext is OK vs not** — claim may write a private local MCP file; docs/plans use `${VAR}` or URL-only). Hooks and wrappers resolve the key from process env → nearest `.env` up from cwd → `~/.centricmem/.env`; hook broken but MCP fine → `CENTRICMEM_TOKEN=` in `.env`, never in a prompt.
**Style** of a card (voice, length, evidence density) is yours + this agent's — not a CentricMem house voice. Structure only: REFERENCE **Card contract**.

## Quick path
`cm_health` → `cm_ambient` **with `shelf=`** → `cm_note` / `cm_log_decision` with the same `shelf=`. The rest of this file is for when those three are blocked.
**Health:** `library:null` with valid `auth` / `grants` means connected with no shelf selected, not "no shelves exist." Call `cm_ambient` with `cwd=` or a named `shelf=` and choose from `libraries=`.
**Shelf:** `suggested_shelf=` is a cwd heuristic, not authority. If the session is not about that shelf, use the one whose charter matches and say which you chose.
**Wrap-up:** decision unlogged? friction unlogged? stale card cited (>90d, volatile fact)? If all three are no, stop.

## Do not (full list: REFERENCE)

- Don't wait for "log this" / close / wrap up to file a finished chunk — sweep before you yield (§4)
- Don't write `unclassified` — pick or create a named shelf; don't treat this git checkout as the memory disk
- Don't put secrets / keys in cards, and never ask the human to paste a key or transcript in chat
- Never echo a credential value — fingerprint to confirm (`9352... len=64 fp=5E4ED29C`), never dump `mcp.json` / `config.toml` / `*.env` whole, never redact by length threshold. A key in the transcript → say so that turn and rotate it. (REFERENCE **Never echo a credential**)
- Don't stop after a title-only card — every card needs summary + key points
- Don't confuse a dead session with a key problem — transport failure → re-handshake path (§0); refusal (401/403) → rotation. Never call a key unrotated from the store alone: compare card, env, and whether this host is on OAuth.

## When to Use

Start or resume; search; file Non-Micro; connect / refresh Skill. Recipes: REFERENCE.
**Daily:** §2 → work → §4 before yield. Connect: REFERENCE. Empty shelf once: REFERENCE Existing memory.

## 0. Reach

1. MCP only `https://mem.centricmem.com/mcp`: `cm_health` `cm_ambient` `cm_doctor` `cm_search` `cm_show` `cm_note` `cm_log_decision` `cm_done` `cm_keep` `cm_library` `cm_copy` `cm_move` `cm_delete` `cm_rename` `cm_import` `cm_index` `cm_ops`. No curl / CLI-write / bootstrap.
2. Missing tools or short grants → **connect this turn**. REFERENCE **Reach**. Remote/cloud is **not** "paste key only": OAuth if this agent receives the browser login; paste Bearer only when it cannot. Listed OAuth hosts only: an unlisted callback shape leaves the host stuck on "connecting", so prefer `/connect?device=` and send that callback shape to zeyu@poppyg.com (REFERENCE "Approved, but the agent stays connecting").
   Tools that vanish mid-session or a load-time `discover` failure = the MCP **session** died, not the key: probe `centricmem doctor` (its own request), re-handshake (goose: disable/enable centricmem or restart host), retry once. While the session is dead, nothing here is loaded either.
3. `cm_show` = card on the **hosted** shelf (not a local junction file). `grants=["*"]` = full access. Extra `mode=read` = view-only (search/show only). A `share:` shelf can be read-only — owner can share read-only; re-share with a different level to change it (writes then 403). `ACADEMIC.md` beside this → follow it. Upsert corpus paths: REFERENCE **Import shapes** (`bundle.imported` + `rel_path`, never bare `items=`). Host-specific install, refresh or failure detail: `cm_ops` — read it when a host detail actually blocks you (librarian >=1.0.6; served on request, not shipped in every copy).
4. **Writes — `items=` and `bundle` are different contracts.** `cm_note` / `cm_log_decision` / `cm_done` file cards; `cm_import` with `items=` (or `package.items`, or a zip) adds **new cards under `imported/kept/`** and nothing else; `cm_import` with **`bundle: {version: 1, …}`** also writes library files — `context` → **`active_context.md`**, `rules` → **`AGENTS.md`**, plus `decisions` / `lessons` / `sessions` / `imported` / `research`. Unknown top-level slot → **`400 BAD_IMPORT_BUNDLE`** (names slot + allowed list). Slot table: REFERENCE **Writes**.

## 1. Classify

Skip (Micro): typo, one-liner, no durable fact. Sweep (Non-Micro): implement / ops / research / architecture / decision — ≥2 real turns **or** one turn that shipped / decided.

## 2. Start

Prefer `cm_ambient` with **`shelf=`** (or `library=`) first — it already carries grants / mode / skill_latest / Recent / Session. That shapes **Recent decisions / Session tail / Curate**, not only later write routing. Ambient with only an unmatched `cwd` and no `shelf=` often shows empty Recent/Session — that is not "the shelf is empty." When ambient/doctor returns **`suggested_shelf=`** (cwd basename matches a shelf id), **use that id on every write this session** — do not wait for the human to name it. Optional durable bind (full-access `*` key): `cm_library {id, sourceDir: <absolute cwd>}` so later ambient cwd-matches. When `library=(none)` and no suggestion: pick from `libraries=` or mint (`cm_library`), same turn as the first Non-Micro write. `cm_health` only when tools are missing, connect is needed, or ambient is unhealthy / unreachable. Unreachable: say once — no bootstrap. Named shelf for writes.

**Host parity before the first card.** `centricmem doctor` names this host and what it can do: `parity` carry on; `armed-off` say the one command that fixes it and do not claim the hook fired; `stale` = local copy older than the CLI; `ceiling` / `unprobed` are normal. Only the CLI sees this — `cm_doctor` cannot read host config. An inject surface that exists but is not live = a session that will not remember itself — fix before filing, not after.

**Resume = new session.** Compress, checkpoint restore, or new chat on same task → ambient first (health only if needed).

Once after ambient (or health): refresh if `skill_latest` newer. **Load path ≠ refresh path** — read the version of the copy **this host loads**, not a sibling skills dir (plugin-tree hosts: `<host-plugins-dir>/centricmem-skill/package.json`; npx `-g` / `~/.agents` does not update that tree). Install morphologies: REFERENCE Skill refresh — adapt, never invent a fourth shared hub. After a disk refresh: **re-read this SKILL.md and Do not** before the next write — installing newer ≠ acting on it. Name the key once (`mode=read` → view-only). Don't log → skip sweep.

## 3. During

**chunk** = accepted unit (verified fragment, locked decision, evidenced lesson, delivery). Any in this reply → same-turn sweep. Not the whole task.
**yield** = any reply end (incl. progress).

Search/show/ambient while working; hold half-finished. **Chunk done → sweep before you yield.** Cards need summary + key points — keep stubs ≠ cards (REFERENCE Writes). Voice/density: theirs + yours (REFERENCE **Card contract**), not a CentricMem template.

## 4. Sweep — single source

No wrap-up wait; Agent close does not run this; Don't log / Skill done → skip. **Gate:** Non-Micro chunk this reply, zero `cm_*` this session, no Don't log → **sweep before you yield**.

| File now | File at wrap-up |
|---|---|
| Locked decision; method-changing lesson; finished chunk | Version-tied stats; unverified conclusions |

Same `lessons.md` title → 409; rewrite = `cm_delete` then write (REFERENCE). Early wrong write costs more.

MCP down: hold **CentricMem deferred sweep**; connect (REFERENCE); file after health. Say so once, keep working without memory, and never fake a card, pick a local hub, or treat a leftover copy of the hub as the shelf.

`shelf=` / `library=` (REFERENCE **Shelf routing**):
1. Transcript plaintext exists → Shell-read → `cm_keep` (no paste / `path=`). Else skip keep.
2. Same batch: `cm_note` / `cm_log_decision` / `cm_done` (+ `attach`) as needed.
3. Copy/move/delete/rename leftovers: REFERENCE Writes.
