# DCG and RCH: Production Hook Examples

Real-world PreToolUse hooks from production systems.

## Combined Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "dcg" },
          { "type": "command", "command": "rch" }
        ]
      }
    ]
  }
}
```

Both hooks run in parallel on every Bash command.

---

## DCG (Destructive Command Guard)

**Purpose:** Safety hook that blocks dangerous commands before execution.

### What DCG Blocks

**Git Commands:**
- `git reset --hard` - Destroys uncommitted work
- `git checkout -- <path>` - Discards local changes
- `git restore` (without --staged) - Discards changes
- `git clean -f` - Deletes untracked files
- `git push --force` - Rewrites remote history
- `git branch -D` - Force-deletes branch
- `git stash drop/clear` - Destroys stashes

**Filesystem:**
- `rm -rf` outside of /tmp, /var/tmp, $TMPDIR

**Additional Packs:**
- `containers.docker` - Container destruction
- `kubernetes.kubectl` - Cluster operations
- `databases.sql` - DROP, TRUNCATE, DELETE without WHERE
- `cloud.terraform` - Infrastructure destruction

### Installation

```bash
# Install via Homebrew
brew install dcg

# Or from source
cargo install destructive_command_guard
```

### Configuration

```bash
# Environment variables
DCG_VERBOSE=0-3        # Verbosity (0=quiet, 3=trace)
DCG_QUIET=1           # Suppress non-error output
DCG_NO_COLOR=1        # Disable colors
DCG_FORMAT=text|json|sarif
DCG_CONFIG=/path      # Explicit config file
DCG_HOOK_TIMEOUT_MS   # Evaluation timeout
```

### How It Works

1. Receives JSON hook input via stdin
2. Parses the `tool_input.command` field
3. Evaluates against pattern packs
4. Returns exit 2 with explanation if blocked
5. Returns exit 0 if allowed

### Example Output (Blocked)

```
🛡️  DCG blocked: git reset --hard

This command destroys uncommitted work. Alternatives:
  • git stash          - Save changes temporarily
  • git diff > backup  - Export changes first
  • git reset --soft   - Keep changes staged
```

---

## RCH (Remote Compilation Helper)

**Purpose:** Intercepts build commands and offloads to faster remote workers.

### What RCH Intercepts

- `cargo build`, `cargo test`, `cargo check`
- `make`, `cmake --build`
- `go build`, `go test`
- `npm run build`, `yarn build`
- Other configurable patterns

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code                                             │
│  ─────────────                                          │
│  1. Claude wants: cargo build --release                 │
│                        │                                │
│                        ▼                                │
│  2. PreToolUse hook fires → RCH receives JSON           │
│                        │                                │
│                        ▼                                │
│  3. RCH detects: "This is a cargo command"              │
│                        │                                │
│                        ▼                                │
│  4. RCH routes to remote worker via SSH                 │
│     - Syncs project files                               │
│     - Executes on fast machine                          │
│     - Streams output back                               │
│                        │                                │
│                        ▼                                │
│  5. Returns JSON: permissionDecision: "allow"           │
│     with updatedInput containing modified command       │
└─────────────────────────────────────────────────────────┘
```

### Installation

```bash
# Quick start
rch hook install && rch daemon start

# Verify
rch status --workers --jobs
```

### Commands

```bash
rch hook install     # Install PreToolUse hook
rch hook test        # Test with sample cargo build
rch daemon start     # Start local daemon
rch daemon stop      # Stop daemon
rch workers probe    # Test worker connectivity
rch workers add      # Add new worker
rch config show      # Show configuration
rch doctor           # Run diagnostics
```

### Configuration

```bash
# Environment variables
RCH_PROFILE=dev|prod|test
RCH_LOG_LEVEL=trace|debug|info|warn|error
RCH_DAEMON_SOCKET=/path/to/socket
RCH_SSH_KEY=/path/to/key
RCH_TRANSFER_ZSTD_LEVEL=1-22
```

### Config Precedence

1. Command-line arguments
2. Environment variables
3. Profile defaults (RCH_PROFILE)
4. .env / .rch.env files
5. Project config (.rch/config.toml)
6. User config (~/.config/rch/config.toml)
7. Built-in defaults

---

## Hook Interaction

DCG and RCH work together:

1. **DCG runs first** (parallel, but faster)
   - If DCG blocks → command never reaches RCH
   - If DCG allows → continues to RCH

2. **RCH evaluates**
   - If build command → intercept and route
   - If not build → pass through unchanged

3. **Results merged**
   - Both can modify the command
   - Both can add context
   - Any block is final

---

## Writing Your Own Hook Like DCG/RCH

### Minimal Rust Structure

```rust
use serde::{Deserialize, Serialize};
use std::io::{self, Read};

#[derive(Deserialize)]
struct HookInput {
    tool_name: String,
    tool_input: ToolInput,
}

#[derive(Deserialize)]
struct ToolInput {
    command: String,
}

#[derive(Serialize)]
struct HookOutput {
    #[serde(rename = "hookSpecificOutput")]
    hook_specific_output: HookSpecificOutput,
}

#[derive(Serialize)]
struct HookSpecificOutput {
    #[serde(rename = "hookEventName")]
    hook_event_name: String,
    #[serde(rename = "permissionDecision")]
    permission_decision: String,
    #[serde(rename = "permissionDecisionReason")]
    permission_decision_reason: String,
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();

    let hook_input: HookInput = serde_json::from_str(&input).unwrap();

    if should_block(&hook_input.tool_input.command) {
        eprintln!("Blocked: dangerous command");
        std::process::exit(2);
    }

    // Allow
    std::process::exit(0);
}
```

### Minimal Python Structure

```python
#!/usr/bin/env python3
import json
import sys

def main():
    input_data = json.load(sys.stdin)
    command = input_data.get('tool_input', {}).get('command', '')

    if is_dangerous(command):
        print("Blocked: dangerous command", file=sys.stderr)
        sys.exit(2)

    # Allow with modification
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Safe command",
            "updatedInput": {
                "command": modify_command(command)
            }
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

---

## Troubleshooting

### DCG Not Blocking

```bash
# Check DCG is in path
which dcg

# Test manually
echo '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' | dcg
echo $?  # Should be 2
```

### RCH Not Intercepting

```bash
# Check daemon running
rch daemon status

# Check worker connectivity
rch workers probe --all

# Test hook manually
rch hook test
```

### Hook Format Error

```
hooks.PreToolUse: Expected array, but received object
```

**Fix:** Use new array format:
```json
// Wrong
{"PreToolUse": {"tools": ["Bash"], "hooks": [...]}}

// Correct
{"PreToolUse": [{"matcher": "Bash", "hooks": [...]}]}
```
