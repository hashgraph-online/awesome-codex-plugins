# Hook Events Reference

Complete documentation for all Claude Code hook events.

## PreToolUse

**When:** After Claude creates tool parameters, before tool execution
**Can Block:** Yes

### Input Schema

```json
{
  "session_id": "string",
  "transcript_path": "/path/to/session.jsonl",
  "cwd": "/current/directory",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash|Write|Edit|Read|Glob|Grep|Task|WebFetch|WebSearch|mcp__*",
  "tool_input": { /* tool-specific */ },
  "tool_use_id": "toolu_01ABC..."
}
```

### Tool-Specific Inputs

**Bash:**
```json
{
  "command": "npm test",
  "description": "Run test suite",
  "timeout": 120000,
  "run_in_background": false
}
```

**Write:**
```json
{
  "file_path": "/absolute/path/to/file.txt",
  "content": "file content"
}
```

**Edit:**
```json
{
  "file_path": "/absolute/path/to/file.txt",
  "old_string": "original text",
  "new_string": "replacement",
  "replace_all": false
}
```

**Read:**
```json
{
  "file_path": "/absolute/path/to/file.txt",
  "offset": 0,
  "limit": 100
}
```

### Output: Decision Control

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Explanation",
    "updatedInput": { "field": "modified value" },
    "additionalContext": "Context added for Claude"
  }
}
```

| Decision | Effect |
|----------|--------|
| `allow` | Bypass permission system, execute immediately |
| `deny` | Block execution, reason shown to Claude |
| `ask` | Show permission dialog to user |

---

## PostToolUse

**When:** Immediately after tool completes successfully
**Can Block:** No (tool already ran)

### Input Schema

```json
{
  "session_id": "string",
  "transcript_path": "/path/to/session.jsonl",
  "cwd": "/current/directory",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { /* original input */ },
  "tool_response": { /* tool result */ },
  "tool_use_id": "toolu_01ABC..."
}
```

### Output: Feedback to Claude

```json
{
  "decision": "block",
  "reason": "Linting errors found. Fix before continuing.",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Error on line 42: missing semicolon"
  }
}
```

---

## PermissionRequest

**When:** Permission dialog is about to be shown
**Can Block:** Yes (auto-allow or auto-deny)

### Output: Auto-Resolve Permission

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow|deny",
      "updatedInput": { "command": "safe-command" },
      "message": "Reason for denial",
      "interrupt": false
    }
  }
}
```

---

## UserPromptSubmit

**When:** User submits prompt, before Claude processes
**Can Block:** Yes

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "User's input text"
}
```

### Output: Add Context or Block

**Add context (simple):** Print to stdout with exit 0
```bash
echo "Current time: $(date)"
exit 0
```

**Add context (JSON):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Project is in maintenance mode until 5pm"
  }
}
```

**Block prompt:**
```json
{
  "decision": "block",
  "reason": "Cannot process: contains sensitive data"
}
```

---

## Stop

**When:** Claude finishes responding (not on user interrupt)
**Can Block:** Yes (force continue)

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "Stop",
  "stop_hook_active": true,
  "transcript_path": "/path/to/session.jsonl"
}
```

**Important:** Check `stop_hook_active` to prevent infinite loops.

### Output: Force Continue

```json
{
  "decision": "block",
  "reason": "Tests are failing. Fix the errors in src/auth.ts"
}
```

### Prompt-Based Stop Hook

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop. Context: $ARGUMENTS. Check if all tasks complete.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

LLM responds: `{"ok": true}` or `{"ok": false, "reason": "Tasks incomplete"}`

---

## SubagentStop

**When:** Subagent (Task tool) finishes
**Can Block:** Yes

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_transcript_path": "/path/to/subagents/agent-def456.jsonl"
}
```

---

## SubagentStart

**When:** Subagent is spawned
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore|Plan|Bash|custom-name"
}
```

---

## SessionStart

**When:** Session begins or resumes
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact",
  "model": "claude-sonnet-4-6",
  "agent_type": "agent-name"
}
```

### Matchers

- `startup` - New session
- `resume` - From --resume, --continue, /resume
- `clear` - After /clear
- `compact` - After compaction

### Persisting Environment Variables

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export API_KEY=xxx' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

---

## SessionEnd

**When:** Session terminates
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "SessionEnd",
  "reason": "clear|logout|prompt_input_exit|other"
}
```

---

## Notification

**When:** Claude Code sends notifications
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "notification_type": "permission_prompt|idle_prompt|auth_success|elicitation_dialog"
}
```

### Example: Custom Desktop Notifications

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          { "type": "command", "command": "notify-send 'Claude Code' 'Permission needed'" }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          { "type": "command", "command": "notify-send 'Claude Code' 'Waiting for input'" }
        ]
      }
    ]
  }
}
```

---

## PreCompact

**When:** Before context compaction
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "PreCompact",
  "trigger": "manual|auto",
  "custom_instructions": ""
}
```

### Matchers

- `manual` - From /compact command
- `auto` - Automatic due to full context

---

## Setup

**When:** Invoked with --init, --init-only, or --maintenance
**Can Block:** No

### Input Schema

```json
{
  "session_id": "string",
  "hook_event_name": "Setup",
  "trigger": "init|maintenance"
}
```

### Matchers

- `init` - From --init or --init-only
- `maintenance` - From --maintenance

Has access to `CLAUDE_ENV_FILE` for persisting environment.

---

## MCP Tool Naming

MCP tools follow pattern: `mcp__<server>__<tool>`

```json
{
  "matcher": "mcp__memory__.*",
  "hooks": [{ "type": "command", "command": "log-memory-ops.sh" }]
}
```

Examples:
- `mcp__memory__create_entities`
- `mcp__filesystem__read_file`
- `mcp__github__search_repositories`
