# Hook Patterns and Recipes

Common patterns for Claude Code hooks.

## Auto-Format on File Write

### TypeScript/JavaScript with Prettier

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.ts || \"$f\" == *.tsx || \"$f\" == *.js ]] && npx prettier --write \"$f\"; } || true"
          }
        ]
      }
    ]
  }
}
```

### Go with gofmt

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.go ]] && gofmt -w \"$f\"; } || true"
          }
        ]
      }
    ]
  }
}
```

### Rust with rustfmt

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.rs ]] && rustfmt \"$f\"; } || true"
          }
        ]
      }
    ]
  }
}
```

### Multi-Language Formatter

```bash
#!/bin/bash
# ~/.claude/hooks/auto-format.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path')

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx)
    npx prettier --write "$FILE" 2>/dev/null
    ;;
  *.go)
    gofmt -w "$FILE" 2>/dev/null
    ;;
  *.rs)
    rustfmt "$FILE" 2>/dev/null
    ;;
  *.py)
    black "$FILE" 2>/dev/null || ruff format "$FILE" 2>/dev/null
    ;;
esac
exit 0
```

---

## File Protection

### Block Sensitive Files

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | grep -qE '(\\.env|\\.git/|credentials|secrets|password)' && { echo 'Blocked: sensitive file' >&2; exit 2; } || exit 0"
          }
        ]
      }
    ]
  }
}
```

### Block Production Paths

```bash
#!/bin/bash
INPUT=$(cat)
PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path')

BLOCKED_PATTERNS=(
  "/prod/"
  "/production/"
  "deploy/"
  ".env.production"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if [[ "$PATH" == *"$pattern"* ]]; then
    echo "Blocked: production file $PATH" >&2
    exit 2
  fi
done
exit 0
```

---

## Command Validation

### Block Dangerous Git Commands

```python
#!/usr/bin/env python3
import json
import sys
import re

DANGEROUS_PATTERNS = [
    r'git\s+reset\s+--hard',
    r'git\s+clean\s+-[fd]',
    r'git\s+push\s+.*--force',
    r'git\s+checkout\s+--\s+\.',
    r'git\s+branch\s+-D',
]

input_data = json.load(sys.stdin)
command = input_data.get('tool_input', {}).get('command', '')

for pattern in DANGEROUS_PATTERNS:
    if re.search(pattern, command):
        print(f"Blocked: dangerous git command", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
```

### Suggest Better Commands

```python
#!/usr/bin/env python3
import json
import sys
import re

SUGGESTIONS = [
    (r'\bgrep\b(?!.*\|)', "Use 'rg' (ripgrep) instead of grep"),
    (r'\bfind\s+\S+\s+-name\b', "Use 'fd' or 'rg --files' instead of find"),
    (r'\bcat\s+\S+\s*\|\s*grep', "Use 'rg pattern file' directly"),
]

input_data = json.load(sys.stdin)
command = input_data.get('tool_input', {}).get('command', '')

for pattern, suggestion in SUGGESTIONS:
    if re.search(pattern, command):
        print(f"Suggestion: {suggestion}", file=sys.stderr)
        # Non-blocking - just advice
        break

sys.exit(0)
```

---

## Logging and Auditing

### Log All Commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Structured JSON Logging

```bash
#!/bin/bash
INPUT=$(cat)
TIMESTAMP=$(date -Iseconds)
LOG_ENTRY=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '{timestamp: $ts, tool: .tool_name, input: .tool_input}')
echo "$LOG_ENTRY" >> ~/.claude/hooks.jsonl
exit 0
```

### Log to Syslog

```bash
#!/bin/bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.file_path // "unknown"')
logger -t claude-code "Tool: $TOOL, Target: $CMD"
exit 0
```

---

## Custom Notifications

### Desktop Notification (Linux)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send -u critical 'Claude Code' 'Permission required'"
          }
        ]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Waiting for your input'"
          }
        ]
      }
    ]
  }
}
```

### macOS Notification

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Awaiting input\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### Slack/Discord Webhook

```bash
#!/bin/bash
INPUT=$(cat)
MSG=$(echo "$INPUT" | jq -r '.message')
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"Claude Code: $MSG\"}" \
  2>/dev/null
exit 0
```

---

## Context Injection

### Add Project Context at Session Start

```bash
#!/bin/bash
# SessionStart hook
if [ -f "$CLAUDE_PROJECT_DIR/.claude/context.md" ]; then
  cat "$CLAUDE_PROJECT_DIR/.claude/context.md"
fi

# Add git status
echo "Current branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo "Modified files: $(git status --porcelain 2>/dev/null | wc -l || echo 0)"

exit 0
```

### Add Context from External Tool

```python
#!/usr/bin/env python3
import json
import subprocess
import sys

# Get current issues
result = subprocess.run(['gh', 'issue', 'list', '--limit', '5', '--json', 'title,number'],
                        capture_output=True, text=True)

if result.returncode == 0:
    issues = json.loads(result.stdout)
    if issues:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"Open issues: {json.dumps(issues)}"
            }
        }
        print(json.dumps(output))

sys.exit(0)
```

---

## Stop Hook: Ensure Quality

### Run Tests Before Stopping

```python
#!/usr/bin/env python3
import json
import sys
import subprocess

input_data = json.load(sys.stdin)

# Prevent infinite loops
if input_data.get('stop_hook_active'):
    sys.exit(0)

# Check if tests pass
result = subprocess.run(['npm', 'test'], capture_output=True, timeout=60)

if result.returncode != 0:
    output = {
        "decision": "block",
        "reason": f"Tests failing. Fix before stopping. Error: {result.stderr.decode()[:500]}"
    }
    print(json.dumps(output))

sys.exit(0)
```

### Check for Uncommitted Changes

```bash
#!/bin/bash
INPUT=$(cat)

# Skip if already in stop loop
if echo "$INPUT" | jq -e '.stop_hook_active' > /dev/null 2>&1; then
  exit 0
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  echo '{"decision":"block","reason":"Uncommitted changes detected. Commit or stash before finishing."}'
fi

exit 0
```

---

## Prompt-Based Hook (LLM Evaluation)

### Intelligent Stop Decision

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop. Context: $ARGUMENTS\n\nCheck:\n1. Are all requested tasks complete?\n2. Are there any errors that need fixing?\n3. Is follow-up work needed?\n\nRespond: {\"ok\": true} to stop, or {\"ok\": false, \"reason\": \"explanation\"} to continue.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## Environment Setup

### Load nvm/Node Version

```bash
#!/bin/bash
# SessionStart hook with CLAUDE_ENV_FILE

ENV_BEFORE=$(export -p | sort)

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

# Use project's node version
if [ -f ".nvmrc" ]; then
  nvm use 2>/dev/null
fi

# Persist environment changes
if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

### Activate Python Virtualenv

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  if [ -d ".venv" ]; then
    echo 'export VIRTUAL_ENV=".venv"' >> "$CLAUDE_ENV_FILE"
    echo 'export PATH=".venv/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
  fi
fi
exit 0
```

---

## Skill/Agent Scoped Hooks

### In SKILL.md Frontmatter

```yaml
---
name: secure-deployment
description: Deploy with security checks
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/.claude/hooks/deploy-check.sh"
          once: true  # Only runs once per session
---
```

### In Subagent Definition

```yaml
---
name: code-reviewer
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/lint-check.sh"
---
```
