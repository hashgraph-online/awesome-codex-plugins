# Session File Format

Source: https://pi.dev/docs/latest/session-format

Sessions are JSONL files. Each line is a JSON object with a `type`. Entries form a tree through `id` / `parentId`, enabling in-place branching without new files.

## Location

```text
~/.pi/agent/sessions/--<path>--/<timestamp>_<uuid>.jsonl
```

`<path>` is the working directory with `/` replaced by `-`. Delete sessions by removing the `.jsonl` file, or from `/resume` with Ctrl+D (Pi uses the `trash` CLI when available).

## Versions

- v1: linear entry sequence (legacy, auto-migrated on load)
- v2: tree structure with `id`/`parentId`
- v3: renamed the `hookMessage` role to `custom` (extensions unification)

Existing sessions auto-migrate to v3 when loaded.

## Content Blocks

`TextContent { type: "text", text }`, `ImageContent { type: "image", data (base64), mimeType }`, `ThinkingContent { type: "thinking", thinking }`, `ToolCall { type: "toolCall", id, name, arguments }`.

## Message Types

Base (from `pi-ai`):

- `UserMessage` — `role: "user"`, `content` string or `(Text|Image)[]`, `timestamp` (Unix ms)
- `AssistantMessage` — `content: (Text|Thinking|ToolCall)[]`, `api`, `provider`, `model`, `usage`, `stopReason` ∈ `stop`/`length`/`toolUse`/`error`/`aborted`, optional `errorMessage`, `timestamp`
- `ToolResultMessage` — `toolCallId`, `toolName`, `content: (Text|Image)[]`, optional `details`, optional `usage` (nested LLM work performed by the tool), `isError`, `timestamp`
- `Usage` — `input`, `output`, `cacheRead`, `cacheWrite`, `totalTokens`, and `cost` with the same four fields plus `total`

The exported pi-ai `StopReason` type also includes `"pending"`, but that value is reserved for partial messages in streaming events. Terminal `done`/`error` messages replace it with a completion reason before Pi persists the assistant message, so `"pending"` should never appear in session JSONL.

Extended (from `pi-coding-agent`):

- `BashExecutionMessage` — `command`, `output`, `exitCode`, `cancelled`, `truncated`, optional `fullOutputPath`, optional `excludeFromContext` (true for `!!`)
- `CustomMessage` — `customType`, `content`, `display`, optional `details`
- `BranchSummaryMessage` — `summary`, `fromId`
- `CompactionSummaryMessage` — `summary`, `tokensBefore`

`AgentMessage` is the union of all seven.

## Entry Types

All entries except the header extend `SessionEntryBase { type, id (8-char hex), parentId (null for the first entry), timestamp (ISO string) }`.

- `session` — header, first line, metadata only (no `id`/`parentId`): `version`, `id`, `timestamp`, `cwd`, plus `parentSession` for sessions created via `/fork`, `/clone`, or `newSession({ parentSession })`
- `message` — wraps an `AgentMessage` in `message`
- `model_change` — `provider`, `modelId`
- `thinking_level_change` — `thinkingLevel`
- `compaction` — `summary`, `tokensBefore`, plus optional `usage`, `details`, `fromHook`, `firstKeptEntryId` (old format), and `retainedTail`
- `branch_summary` — `summary`, `fromId`, plus optional `usage`, `details`, `fromHook`
- `custom` — `customType`, `data`; extension state, **not** in LLM context. Renderable in the transcript via `pi.registerEntryRenderer(customType, renderer)`
- `custom_message` — `customType`, `content`, `display`, optional `details`; extension-injected and **in** LLM context
- `label` — `targetId`, `label` (set `label` to `undefined` to clear)
- `session_info` — `name`; set via `/name`, `--name`/`-n`, or `pi.setSessionName()`. Shown in `/resume` instead of the first message

`retainedTail` is a materialized `AgentMessage[]` kept after compaction. Newer harness-generated compactions include it so context rebuilds from that checkpoint without walking entries before the compaction. It is optional only for backward compatibility with sessions that store only `firstKeptEntryId`.

## Context Building

`buildContextEntries()` walks from the current leaf to the root and produces the active entry list honoring compaction:

1. Collect all entries on the path.
2. If a `CompactionEntry` is on the path: include the compaction entry first; if `retainedTail` is present it acts as a self-contained checkpoint and entries after the compaction are included; otherwise include entries from `firstKeptEntryId` to the compaction, then entries after it.
3. Preserve non-message entries in the selected range so interactive mode can render them.

`buildSessionContext()` builds the LLM message list on top of that: it extracts the current model and thinking level from the full path, then converts entries — `message` → stored `AgentMessage`, `compaction` → `compactionSummary` plus `retainedTail` when present, `branch_summary` → `branchSummary`, `custom_message` → `CustomMessage`, `custom` → no context message.

## SessionManager API

Static creation: `create(cwd, sessionDir?)`, `open(path, sessionDir?)`, `continueRecent(cwd, sessionDir?)`, `inMemory(cwd?)`, `forkFrom(sourcePath, targetCwd, sessionDir?)`.

Static listing: `list(cwd, sessionDir?, onProgress?)`, `listAll(onProgress?)`.

Session management: `newSession({ parentSession? })`, `setSessionFile(path)`, `createBranchedSession(leafId)`.

Appending (each returns an entry ID): `appendMessage`, `appendThinkingLevelChange`, `appendModelChange`, `appendCompaction(summary, firstKeptEntryId, tokensBefore, details?, fromHook?)`, `appendCustomEntry(customType, data?)`, `appendSessionInfo(name)`, `appendCustomMessageEntry(customType, content, display, details?)`, `appendLabelChange(targetId, label)`.

Tree navigation: `getLeafId`, `getLeafEntry`, `getEntry`, `getBranch(fromId?)`, `getTree`, `getChildren`, `getLabel`, `branch(entryId)`, `resetLeaf()`, `branchWithSummary(entryId, summary, details?, fromHook?)`.

Context and info: `buildContextEntries`, `buildSessionContext`, `getEntries`, `getHeader`, `getSessionName`, `getCwd`, `getSessionDir`, `getSessionId`, `getSessionFile` (undefined in memory), `isPersisted`.

## Parsing

Read the file line by line and switch on `entry.type`; treat `entry.version ?? 1` on the header, and ignore unknown types for forward compatibility. For TypeScript definitions inspect `node_modules/@earendil-works/pi-coding-agent/dist/` and `node_modules/@earendil-works/pi-ai/dist/`.
