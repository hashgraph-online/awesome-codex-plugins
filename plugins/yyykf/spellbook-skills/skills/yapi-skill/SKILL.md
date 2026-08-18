---
name: yapi-skill
description: Python stdlib scripts for the YApi OpenAPI (no Java/Docker/MCP) — search interfaces, query details, and sync/upsert one interface's docs from a YApi-native payload (often converted from OpenAPI). Read-modify-write with dry-run preview; creates/updates only — never deletes, preserves manual edits; no source-code parsing or full re-import.
---

# Yapi Search and Query Skill

## Overview

You can directly use Python scripts to call the Yapi API, search for Yapi interfaces to locate the `interfaceId`, or get detailed information of a specific interface (request parameters, response body, description in Markdown). Prefer using this skill instead of starting the `yapi-mcp-server` (Java/Docker).

Beyond reading, this skill can also **write**: sync (upsert) a single interface's docs into YApi from a YApi-native payload — typically converted from an OpenAPI contract. Writing is read-modify-write (only managed fields are overwritten; existing writable fields are re-sent to best-preserve un-managed content like mock / test cases / status — verified end-to-end: `up` is merge semantics, fields not sent are preserved), dry-run by default (a preview artifact is written to a file; only a compact summary is printed), and never deletes (YApi's OpenAPI has no delete endpoint).

**Core principle:** Configure environment -> choose search / query / sync as needed -> for sync, convert to a payload, dry-run to preview, then apply.

**Announce at start:** "I am using the yapi-skill to search/query or sync Yapi interface details."

## Prerequisites

This skill depends on a local configuration file (`base_url` + `projectId -> token`).
If you haven't initialized it, don't know how to get the token, or need to switch between multiple environments, please read first:
- `skills/yapi-skill/references/initialization.md`

Configuration paths support the following override methods:
- Environment variable: `YAPI_SKILL_CONFIG=/path/to/config.json`
- Single command execution: `--config /path/to/config.json` (takes effect for `searchInterfaces.py` / `getInterfaceDetail.py`)

> For Windows users, if the `python3` command is not available, try using `py -3` or `python`.

## Workflow

### Step 1: Decide the Target (Search or Query Details)

Determine whether you need to first find a specific interface (using the search function) or if you already have the specific interface ID or URL to query the detailed information.

### Step 2: Execute the Query

#### Scenario A: Get Interface Details Directly (Recommended)

Use this when you already know the specific interface URL or the `projectId` and `interfaceId`.

```bash
python3 skills/yapi-skill/scripts/getInterfaceDetail.py \
  --url 'http://yapi.example.com/project/1650/interface/api/414469' \
  --format markdown
```

Description:
- `--url` supports directly pasting the interface page URL (the script will automatically parse `projectId/interfaceId`).
- `--format` supports `json` (for secondary processing) and `markdown` (for readability).
- It also supports `--projectId` + `--interfaceId` (when you already have the IDs).

> Security warning: The Markdown output may contain example request headers/example values from the interface definition (e.g., `Authorization` example). Please sanitize it yourself before sharing it externally.

#### Scenario B: Search for Interfaces (Locate interfaceId)

Use this when you only know the interface keyword or path.

```bash
python3 skills/yapi-skill/scripts/searchInterfaces.py --keyword login --format markdown
```

Common parameters:
- By default, it searches all projects in the `project_tokens` of the configuration file. (Use `--projectName` to narrow the scope).
- `--projectName`: Fuzzy filter by project name (Optional).
- `--keyword`: Fuzzy search by interface title (Optional).
- `--path`: Fuzzy search by interface path (Optional).
- `--format json|markdown`: Defaults to `json`.
- `--config <path>`: Specify the configuration file path (Overrides default path, Optional).

## Write / Sync Workflow

Use this to push an interface's docs into YApi from a contract (e.g. OpenAPI). The scripts are source-agnostic primitives; deciding *which* interfaces to sync is your job.

**Safety rules (always):**
- Only touch interfaces you explicitly target — one interface per `upsertInterface.py` call. Never enumerate-and-sync a whole spec blindly.
- Dry-run first (the default). Read the field-level diff from the preview artifact, show it to the user, get confirmation, then re-run with `--apply`.
- Creates/updates only — YApi's OpenAPI cannot delete. `up` is read-modify-write and re-sends existing writable fields to best-preserve un-managed content (mock, test cases, status — verified end-to-end: `up` merges, so fields not sent are preserved); remove stale interfaces manually in the YApi UI.

### Step 1: Build a YApi-native payload

If the source is OpenAPI, convert one operation to a payload file (large schemas stay in files, off your context):

```bash
python3 skills/yapi-skill/scripts/openapiToYapiPayload.py \
  --spec /path/to/preview-merged.json --path /admin/ad/campaign/create --method post \
  --out .yapi-sync/payload-create.json
```

- JSON spec only; use a dereferenced/"merged" doc (no remaining `$ref`/`allOf`).
- It prints the operation's `tag` — pass it as `--category` in Step 2/3.
- For non-OpenAPI sources, hand-write the payload JSON with YApi-native fields: `title`, `path`, `method`, `req_query`, `req_headers`, `req_params`, `req_body_other`, `res_body`, `markdown`.

### Step 2: Dry-run (preview, no write)

```bash
python3 skills/yapi-skill/scripts/upsertInterface.py \
  --projectId 1650 --payload .yapi-sync/payload-create.json --category '广告投放计划'
```

- Probes YApi by `path`+`method`: 1 match → update, 0 → create, multiple → stops and asks for an explicit `--interfaceId`.
- Writes a preview artifact (full final payload + field-level diff) and prints a compact summary. Open the artifact to review what markdown/schema will be overwritten.

### Step 3: Apply (after confirmation)

```bash
python3 skills/yapi-skill/scripts/upsertInterface.py \
  --projectId 1650 --payload .yapi-sync/payload-create.json --category '广告投放计划' --apply
```

- Update keeps the interface's existing category (no moving). Create places it under `--category` (auto-created if missing).

## Quick Reference

| Purpose | Command | Key Parameters |
| --- | --- | --- |
| Get Details | `python3 scripts/getInterfaceDetail.py` | `--url` or `--projectId`/`--interfaceId` |
| Search Interfaces | `python3 scripts/searchInterfaces.py` | `--keyword`, `--path`, `--projectName` |
| Convert OpenAPI→payload | `python3 scripts/openapiToYapiPayload.py` | `--spec`, `--path`, `--method`, `--out` |
| Sync (upsert) interface | `python3 scripts/upsertInterface.py` | `--projectId`, `--payload`, `--category`, `--apply` |

## Common Mistakes

**Incomplete initialization configuration**
- **Problem:** Missing token or environment info causes request failure.
- **Fix:** Read `skills/yapi-skill/references/initialization.md` first to complete configuration.

**Sharing unsanitized Markdown**
- **Problem:** Leaking sensitive example data (e.g., real Tokens or passwords).
- **Fix:** Manually remove sensitive content from Markdown before sharing.

**Syncing interfaces you didn't intend to**
- **Problem:** Pushing every path in a big merged spec overwrites unrelated interfaces (and their manual edits).
- **Fix:** Target only explicitly-decided interfaces, one upsert call each; review the dry-run diff before `--apply`.

**Expecting delete or full re-import**
- **Problem:** YApi's OpenAPI token cannot delete, and a full re-import clobbers manual edits.
- **Fix:** This skill only creates/updates per-interface via read-modify-write; delete stale interfaces manually in the YApi UI.

## Example

```bash
# Search for interfaces
python3 skills/yapi-skill/scripts/searchInterfaces.py --keyword submit_order --format markdown

# Get interface details
python3 skills/yapi-skill/scripts/getInterfaceDetail.py --url 'http://yapi.example.com/project/123/interface/api/456' --format markdown
```
