# JSON Output Reference

Complete schemas for hook JSON responses.

## Common Fields (All Hooks)

```json
{
  "continue": true,
  "stopReason": "Why Claude should stop",
  "suppressOutput": false,
  "systemMessage": "Warning shown to user"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `continue` | boolean | If false, Claude stops after hooks run |
| `stopReason` | string | Message shown when continue=false |
| `suppressOutput` | boolean | Hide from verbose mode (ctrl+o) |
| `systemMessage` | string | Warning displayed to user |

---

## PreToolUse

### Allow (Auto-Approve)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Safe operation auto-approved"
  }
}
```

### Deny (Block)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked: dangerous command"
  }
}
```

### Ask (Show Dialog)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "Requires explicit approval"
  }
}
```

### Modify Input

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Modified for safety",
    "updatedInput": {
      "command": "npm run lint -- --fix",
      "timeout": 60000
    }
  }
}
```

### Add Context

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Environment: production. Proceed with caution."
  }
}
```

### Full Example

```json
{
  "continue": true,
  "suppressOutput": true,
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Build command routed to remote worker",
    "updatedInput": {
      "command": "rch-exec cargo build --release"
    },
    "additionalContext": "Build will execute on worker-1 (32 cores)"
  }
}
```

---

## PermissionRequest

### Allow Permission

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow"
    }
  }
}
```

### Allow with Modified Input

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {
        "command": "npm run build:safe"
      }
    }
  }
}
```

### Deny Permission

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Denied: production deployment requires approval",
      "interrupt": false
    }
  }
}
```

### Deny and Stop Claude

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "Critical: manual intervention required",
      "interrupt": true
    }
  }
}
```

---

## PostToolUse

### Provide Feedback (Block)

```json
{
  "decision": "block",
  "reason": "Linting errors found. Fix before continuing.",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Errors:\n- line 42: missing semicolon\n- line 55: unused variable"
  }
}
```

### Add Context Only

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "File formatted successfully with prettier"
  }
}
```

---

## UserPromptSubmit

### Add Context (Simpler)

Just print to stdout:
```bash
echo "Current time: $(date)"
echo "Project: myapp v1.2.3"
```

### Add Context (JSON)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "User is working on feature-auth branch. 3 open PRs pending review."
  }
}
```

### Block Prompt

```json
{
  "decision": "block",
  "reason": "Prompt contains potentially sensitive data. Please rephrase."
}
```

---

## Stop / SubagentStop

### Allow Stop (Default)

No output needed, or:
```json
{}
```

### Force Continue

```json
{
  "decision": "block",
  "reason": "Tests are failing. Run `npm test` and fix errors in src/auth.ts before stopping."
}
```

---

## SessionStart

### Add Context

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project: myapp\nBranch: feature-auth\nOpen issues: 5"
  }
}
```

---

## Setup

### Add Context

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Setup",
    "additionalContext": "Dependencies installed. Database migrations applied."
  }
}
```

---

## Prompt-Based Hook Response

For `type: "prompt"` hooks:

### Allow

```json
{
  "ok": true
}
```

### Block/Deny

```json
{
  "ok": false,
  "reason": "Tasks incomplete. The test suite is still failing."
}
```

---

## Exit Code Behavior Summary

| Exit Code | JSON Parsed? | Effect |
|-----------|--------------|--------|
| 0 | Yes | Success, JSON controls behavior |
| 2 | No | Block, stderr fed to Claude |
| Other | No | Non-blocking error, stderr to verbose |

**Important:** Exit code 2 ignores any JSON output. Use stderr for the message.

---

## Deprecated Fields

These still work but use new format:

| Old | New |
|-----|-----|
| `decision: "approve"` | `permissionDecision: "allow"` |
| `decision: "block"` | `permissionDecision: "deny"` |
| `reason` | `permissionDecisionReason` |

---

## Field Availability by Event

| Field | PreToolUse | PostToolUse | UserPromptSubmit | Stop |
|-------|------------|-------------|------------------|------|
| `continue` | ✓ | ✓ | ✓ | ✓ |
| `decision` | ✓ | ✓ | ✓ | ✓ |
| `permissionDecision` | ✓ | - | - | - |
| `updatedInput` | ✓ | - | - | - |
| `additionalContext` | ✓ | ✓ | ✓ | - |
| `reason` | ✓ | ✓ | ✓ | ✓ |
