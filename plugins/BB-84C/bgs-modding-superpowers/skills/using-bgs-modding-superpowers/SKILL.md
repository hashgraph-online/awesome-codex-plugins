---
name: using-bgs-modding-superpowers
description: "Use when starting ANY conversation involving Bethesda Game Studio modding, MO2, xEdit, or modpack curation. Bootstrap that loads the toolkit overview, lists available task skills, and enforces the hard rules of this plugin. Auto-injected by the OpenCode plugin's chat.messages.transform hook and by the hooks/ session-start chain in Claude Code and Codex."
---

<EXTREMELY_IMPORTANT_BGS_MODDING_SUPERPOWERS>
This is the bgs-modding-superpowers per-session bootstrap. If you are reading this,
the plugin injected it into the first user message of this session. Do NOT discard
it. Do NOT respond to the user yet without first checking whether one of the task
skills below applies.
</EXTREMELY_IMPORTANT_BGS_MODDING_SUPERPOWERS>

# Using BGS Modding Superpowers

You are operating with the `bgs-modding-superpowers` plugin loaded. This plugin
gives you an agent-driven toolkit for Bethesda Game Studio modpack curation:
MO2 control plane, xEdit MCP, conflict-audit workflow, and runtime asset skills
for dev-log and release-changelog maintenance.

## Available skills (auto-trigger on these intents)

| Skill | Auto-triggers when |
|---|---|
| `setting-up-bgs-modding-environment` | First conversation in a project; MO2 or xEdit not yet detected; user says "set up", "install", "bootstrap", "configure" |
| `maintaining-modding-environments` | After first-run: "ongoing", "maintain", "register custom pack", "prune cache", "update knowledge base", "modding environment health check" |
| `evaluating-bgs-mods` | Deciding whether a mod belongs in the pack; "should I add this mod", "is this mod good", "评估这个mod", "这个mod值得装吗", "this mod looks too good to be true" |
| `interpreting-mod-author-instructions` | After INCLUDE verdict, before download/install; "how do I install", "FOMOD choices", "which file to download", "author说明", "which variant", "按作者说明安装" |
| `curating-bgs-modpack` | Whole-pack incremental build strategy; "plan the pack", "batch strategy", "rollback point", "naming convention", "declare 风格", "策展整合包", "整合包规划" |
| `diagnosing-bgs-problems` | It broke — symptom-first triage; "CTD", "crash log", "FPS drop", "stuttering", "Buffout", "freeze", "won't start", "崩溃", "掉帧", "卡顿" |
| `testing-bgs-modpack` | Proactive post-install verification of a batch; "test the pack", "verification", "post-install check", "is it stable", "what should I test", "测试整合包", "验证安装" |
| `xedit-automation` | Any task involving `.esp/.esm/.esl` plugin files, FormIDs, masters, conflicts, ESL flagging, ITM/UDR cleaning, Pascal scripts |
| `xedit-conflict-audit` | "Why is this override not winning?", "Which plugins overlap on this record?", "Is this load order safe?" |
| `writing-bgs-load-order` | Reading/editing/generating `plugins.txt` or `loadorder.txt`; enabling/disabling/reordering/adding/removing plugins; launching xEdit with a custom plugins file; "load order", "enable this plugin", "disable that plugin", "what does the asterisk mean" |
| `using-bgs-translator` | Translate a Bethesda plugin's text to another language; "translate this mod", "汉化这个 mod", "localize mod to chinese", "build SST for", "use my LLM to translate plugins" |
| `using-bgs-archive` | unpack/pack BA2/BSA archives; inspect archive format/contents; extract assets |
| `using-bgs-papyrus` | compile/decompile Papyrus PSC<->PEX for Skyrim/FO4/Starfield |
| `writing-modpack-devlog` | "Log this", "record what I did", "note this change", "add to dev-log", "track this decision" |
| `writing-modpack-changelog` | "Cut a release", "release notes", "what changed since v1.2", "prepare release for Nexus" |

When the user's intent matches one of these, invoke the corresponding skill
through your skill tool BEFORE replying. Do not paraphrase the skill from memory;
let the skill load.

## Available MCP tools

The bundled `xedit` MCP server (declared in `.mcp.json` for Claude Code / Codex,
declared via the OpenCode plugin's `config.mcp.xedit` hook) is fully
**non-blocking**: every tool returns immediately. The xEdit daemon's lifecycle
is tracked in the server's in-memory state machine, and domain tools fast-fail
with `code: "not_ready"` if you call them before the daemon is ready.

### Lifecycle / health tools (3) — always non-blocking

| Tool | Use |
|---|---|
| `xedit_status` | Pure read. Returns `{ status: "not_started" \| "starting" \| "ready" \| "failed", ... }`. Never modifies state. Use this to POLL while waiting for a launch. |
| `xedit_start` | Kicks off an asynchronous daemon launch if not already starting/ready. Returns immediately. Accepts optional overrides: `{ launcherPath?, gameMode?, dataPath?, pluginsFile?, moProfile? }`. Use `dataPath` (MO2 `gamePath + "\\Data"`) to override xEdit's registry-discovered platform path; use `pluginsFile` to point at a custom load order (see `writing-bgs-load-order`). The launch itself takes 60-240s; that work happens in the background. |
| `xedit_health` | When ready: sends `system.ping` through the named pipe to catch zombies. Returns `responsive: true \| false`. Otherwise: returns the same shape as `xedit_status`. |
| `xedit_dirty` | Returns xEdit's dirty state immediately. When ready: wraps `session.get_dirty_state` and returns `{ dirty, dirtyFiles, unsavedChangeCount }`. Otherwise: returns the same shape as `xedit_status`. |
| `xedit_stop` | Stops the daemon and clears MCP runtime state. If there are unsaved edits, it refuses unless `force: true` is passed. |
| `xedit_restart` | Stops the daemon (same dirty-state safety as `xedit_stop`) and immediately kicks off a fresh async launch. Use this to relaunch with a new `pluginsFile` or `dataPath` instead of reconnecting `/mcp` manually. |

### Domain tools (6) — require ready, fast-fail otherwise

| Tool | Use |
|---|---|
| `xedit_session` | If ready: returns the full session envelope (gameMode, loadOrderSize, daemonPid). If not_started: auto-initiates the launch. Otherwise: returns the current status. Always non-blocking. |
| `xedit_list_capabilities` | Curated 49-command digest + live drift report. |
| `xedit_find_record` | Locate by `{file, formId}` or `{editorId}`. |
| `xedit_read_record` | Fields + base record + winning override. |
| `xedit_inspect_conflicts` | W2 verdict tool: `no_conflict / itpo / itm / minor / breaking`. |
| `xedit_call(command, args)` | Atomic passthrough for any of the 49 native daemon commands; in-harness. |

### Canonical lifecycle pattern (do this every session that touches xEdit)

```
1. xedit_start({})                  -> { status: "starting" }      (or "ready")
2. xedit_status({})                 -> poll until status="ready"   (sleep 5-15s between calls)
3. xedit_health({})                 -> confirm responsive=true
4. xedit_session({}) / xedit_*      -> normal domain work
5. xedit_dirty({})                  -> check unsaved changes before any stop/restart
6. xedit_stop({ force?: true })     -> stop + clear runtime state
7. xedit_restart({ ..., force? })   -> relaunch with new overrides
```

NEVER call a domain tool in a tight loop expecting it to "wait." If
`xedit_status` reports `status: "failed"`, surface `data.error` to the user and
stop — common causes are MO2 not running visibly, the Python plugin not loaded,
the xEdit binary missing, or xEdit's automation-serve tripping on the active
load order.

The structured daemon-command and workflow reference now lives in KB records.
Use `bgs_kb_query` / `bgs_kb_get` for deep reference retrieval; the old
`skills/xedit-automation/xedit-knowledgebase.md` path is a redirect only.

### BGS knowledge-base tools (3) — curated knowledge, no xEdit daemon

The sibling BGS knowledge-base MCP is for curated modding knowledge, not live
runtime state. It works before MO2 / xEdit are configured; use xEdit MCP for
actual plugin, load-order, and record readback.

| Tool | Use |
|---|---|
| `bgs_kb_status` | Reports loaded KB packs, versions, games, domains, cache root, and user pack roots. |
| `bgs_kb_query` | Searches loaded packs for ranked knowledge snippets with game/domain filters and sources. |
| `bgs_kb_get` | Fetches a full record by id, merging game-specific variants when `game` is provided. |

## Hard rules (non-negotiable)

1. **The user's `<MO2_Root>` and any `<MO2_Root>/<game>/Data/` (or equivalent
   "Stock Game" tree) is real game state.** Never write into it directly. Any
   game-local change is expressed as an MO2 mod overlay under
   `<MO2_Root>/mods/<mod-name>/`. The MO2 VFS projects it at runtime.
2. **All xEdit work goes through the bundled `xedit` MCP.** Never spawn
   `xEdit.exe` directly from the shell, never parse `.esp/.esm/.esl` files with
   your own Python/JS, never invoke `xedit-client.ps1` from raw shell. The MCP
   exists so the harness can enforce validation, state, rules, and audit on
   every call. Atomic passthrough (`xedit_call`) is the documented escape hatch
   when an intent tool does not fit — it is still in-harness.
3. **Mutating operations require explicit user consent and a daemon launched
   with `-IKnowWhatImDoing`.** Read the `xedit-automation` skill BEFORE any
   destructive work. The anti-pattern list there is binding.
4. **A `session.save` response is not durability.** A save with
   `savedFilesPendingShutdown > 0` is deferred. Durability proof =
   save + daemon restart (new PID) + readback. Always restart before declaring
   a mutating workflow complete.
5. **Large scope (many records, broad conflict survey) → delegate to a
   read-only investigator subagent FIRST.** The subagent burns its own context
   and returns a distilled summary. Do not loop hundreds of records through
   your own context.
6. **BGS domain knowledge routes through the KB first.** For questions about
   how BGS modding works — Papyrus semantics, plugin-format gotchas, archive
   precedence, load-order conventions, common engine quirks, or game-specific
   toolchain gotchas — call `bgs_kb_status` / `bgs_kb_query` before
   improvising or reaching for web search. If the question is about what the
   current local load order, plugin, or record actually is, use `xedit_*` or the
   relevant file/CLI surface instead. The KB is advisory; xEdit readback remains
   authoritative for actual state. If `bgs_kb_status` reports no packs or the
   needed game pack is missing, fall back to web research using the roadmap
   Appendix source list or route setup/maintenance work to install the pack.
7. **First-run state**: if MO2 / xEdit / the control-plane Python plugin are
   not yet set up on this machine, invoke `setting-up-bgs-modding-environment`
   BEFORE any modpack work. That skill orchestrates detection and install.
8. **Nexus credentials and Premium download paths**: MO2 stores the user's
   Nexus API key globally in Windows Credential Manager under target
   `ModOrganizer2_APIKEY` (legacy) / `ModOrganizer2_NEXUS_OAUTH_TOKENS`
   (modern OAuth). Reading the key requires explicit per-session user consent
   and the key must be masked in any visible output. The agent-friendly
   refresh path for Nexus update state is "Option B" — direct API call to
   `/v1/games/{game}/mods/{id}.json` + write back to `meta.ini` via
   `mo2_edit_meta`, no MO2 GUI launch needed. Both workflows are documented in
   the `maintaining-modding-environments` skill and in KB records
   `install-planning.mo2-windows-credential-mining.v1` +
   `install-planning.nexus-direct-api-update-check.v1`. For Premium-account
   direct downloads, use `POST /v1/games/{game}/mods/{id}/files/{file_id}/download_link.json`
   (returns 7 CDN mirrors) — Premium-only; free accounts must use the Nexus
   browser flow.

## How to use this bootstrap

- This skill loads automatically on every new session. You do not need to
  re-invoke it.
- When a user intent matches a task skill in the table above, invoke that skill
  via your skill tool. Do not paraphrase.
- When the user asks about "what can you do", reference the skills inventory
  here; do not invent capabilities the plugin does not have.
- When answering BGS modding-domain questions, prefer local KB retrieval before
  web search. The bundled core pack ships inline; per-game packs may be
  installed later via setup / maintenance skills; end-user packs may be
  registered via `$BGS_KB_USER_PACKS` through `maintaining-modding-environments`.
- When you would normally write code that touches BGS plugin files (`.esp/.esm/
  .esl`), STOP and route through `xedit-automation` instead.
- When the user is deciding whether to add or keep a mod ("should I install X",
  "is this good", "评估"), route to `evaluating-bgs-mods` BEFORE any
  install/download action.
- When an INCLUDE verdict is in and the user needs to read author instructions /
  pick FOMOD options / choose a file or variant, route to
  `interpreting-mod-author-instructions`.
- When the user is planning the whole pack, sizing batches, deciding rollback
  boundaries, or declaring 风格, route to `curating-bgs-modpack`.
- When the user reports a crash, CTD, FPS drop, freeze, or stutter ("崩溃",
  "掉帧", "卡顿"), route to `diagnosing-bgs-problems` for symptom-first triage
  BEFORE any blame attribution.
- When the user wants to verify a freshly installed batch ("test the pack",
  "is it stable", "验证安装"), route to `testing-bgs-modpack`.
- When the user wants to translate plugin text or emit SST dictionaries for a
  mod, route to `using-bgs-translator` instead of xEdit; translator reads plugin
  text and emits dictionaries, it does not modify plugin binaries.
- When the user wants to inspect, unpack, extract, or pack BA2/BSA archives,
  route to `using-bgs-archive`; archive packing must write to MO2 overlays, not
  game `Data` or Stock-Game trees.
- When the user wants to compile or decompile Papyrus scripts (`.psc` / `.pex`),
  route to `using-bgs-papyrus`; compiled `.pex` output must go to MO2 overlays,
  not game `Data` or Stock-Game trees.
- When the user asks to "log", "record", "track", or "note" modpack work,
  route to `writing-modpack-devlog`. When the user asks to "cut a release" or
  prepare release notes, route to `writing-modpack-changelog`.

## See also

- `setting-up-bgs-modding-environment` — first-run setup orchestrator.
- `maintaining-modding-environments` — ongoing environment care, KB updates,
  custom-pack registration, cache pruning, and health checks after first-run.
- `evaluating-bgs-mods` — judgment skill: should this mod go in the pack (BGS
  systemic-design fit, quality/risk/pack-value); hands off to
  `interpreting-mod-author-instructions` on INCLUDE.
- `interpreting-mod-author-instructions` — judgment skill: how to correctly
  download/install per author说明 (FOMOD reasoning, file/variant selection,
  prerequisites). Downstream from `evaluating-bgs-mods` INCLUDE verdict.
- `curating-bgs-modpack` — judgment skill: whole-pack incremental strategy
  (batch sizing, rollback boundaries, attribution/naming, declaring 风格);
  cross-stage skill that the per-mod skills feed.
- `diagnosing-bgs-problems` — judgment skill: symptom-first triage for CTD /
  FPS / freeze / stutter; escalates to `xedit-conflict-audit` or
  `using-bgs-archive` once root-cause class is identified.
- `testing-bgs-modpack` — judgment skill: proactive post-install verification
  of an install batch; escalates to `diagnosing-bgs-problems` on failure.
- `xedit-automation` — hub skill for all xEdit work; routing doctrine,
  anti-patterns, sub-agent recipes.
- BGS KB records under `knowledge/bgs-kb/packs/core/records/` — deep reference
  for daemon commands, error codes, save semantics, glossary, and durable gotchas.
- `xedit-conflict-audit` — the W2 conflict-audit workflow.
- `using-bgs-translator` — CLI + Tk workflow for LLM-assisted plugin text
  translation and SST dictionary export.
- `using-bgs-archive` — BA2/BSA archive inspection, extraction, and safe
  overlay-only packing.
- `using-bgs-papyrus` — Papyrus PSC/PEX compile/decompile workflows for Skyrim,
  Fallout 4, and Starfield.
- `writing-modpack-devlog`, `writing-modpack-changelog` — runtime asset
  skills for project documentation.

---

> Plugin: `bgs-modding-superpowers`. Repo: https://github.com/BB-84C/bgs-modding-superpowers.
> If any environmental component (MO2, xEdit, control-plane Python plugin) is missing,
> route through `setting-up-bgs-modding-environment` before continuing.
