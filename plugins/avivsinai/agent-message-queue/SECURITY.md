# Security Policy

## Security Model

AMQ is designed for **local inter-process communication** on a single machine. It assumes all agents operate under the same user account and share filesystem access.

### Threat Model

AMQ protects against:
- **Partial writes**: Maildir atomic delivery prevents corrupt messages from appearing in inboxes
- **Path traversal**: Agent handles and message IDs are strictly validated to prevent directory escape
- **Permission leakage**: Directories use 0700, files use 0600 (owner-only access)
- **Log injection**: User input is never interpolated into format strings

AMQ does **not** protect against:
- **Malicious agents with same-user access**: If an attacker has shell access as the same user, they can read/write queue files directly
- **Multi-user scenarios**: AMQ is not designed for use across user accounts

### Rooted Delivery Boundary

After `send` or `reply` authorizes a source and destination tree, AMQ opens each
tree once with Go's `os.Root` and performs mailbox delivery, directory sync,
presence touch, and outbox writes relative to that pinned directory capability.
Replacing the authorized path or one of its ancestors with a symlink cannot
redirect those writes outside the opened tree. Relative symlinks that remain
inside the tree continue to work; symlinks that escape it are refused.

This boundary does not defend against filesystem namespace changes below an
already opened root, including privileged bind mounts, or against writing to
pre-existing device files. Those cases require separate mount and file-type
hardening and remain outside the rooted-delivery guarantee.

### Threat model and accepted residuals

AMQ is a **personal, single-user, on-machine** tool: each engineer runs it under
their own account on their own machine. The security bar reflects that. An
attacker who already has the ability to run code as your user, or to swap
symlinks in your home/ancestor directories mid-command, has full control of your
environment; defending the message queue against them would not meaningfully
improve your posture. Accordingly, the following are **accepted residuals**, not
defended against:

- **Untrusted-ancestor / TOCTOU alias swaps.** A different-euid local attacker
  who can retarget an ancestor symlink between commands (cross-command alias
  retarget for `--project`/`--session` routes; ABA swaps of config or message
  files) is out of scope. Legitimate in-tree symlinks continue to work.
- **Bind mounts and device files below an opened root** (as noted above).

What AMQ **does** defend correctness for, because these bite without any
attacker: no duplicate message injection or delivery, no cross-tree leakage from
ordinary misconfiguration, owner-only `0700`/`0600` permissions, and handle/ID
validation. Bugs and reliability are the priority; same-machine security
hardening beyond the above is intentionally out of scope.

### Known Risks

#### TIOCSTI Terminal Injection (`amq wake`)

The `amq wake` command uses TIOCSTI (terminal input character stuffing) to inject notification text into the terminal. This is an **experimental feature** with inherent security considerations:

- TIOCSTI allows a process to inject input characters as if they were typed
- On some systems (hardened Linux kernels), TIOCSTI is disabled for security reasons
- The injected text is user-controlled notification content, not arbitrary commands
- `amq wake` only operates on terminals it owns (verified via session ID check)

If you're concerned about TIOCSTI, use the notify hook fallback instead:
```toml
# ~/.codex/config.toml
notify = ["python3", "/path/to/scripts/codex-amq-notify.py"]
```

### File Permissions

AMQ enforces strict permissions:
- **Directories**: 0700 (owner read/write/execute only)
- **Files**: 0600 (owner read/write only)
- **Handles**: Validated as `[a-z0-9_-]+` (no path separators)
- **Message IDs**: Cannot start with `.`, cannot contain path separators

## Reporting a Vulnerability

Windows runtime is out of scope for cross-tree identity and `.amqrc` authority hardening; it degrades to legacy lexical behavior.

Please report security issues by opening a GitHub Security Advisory for this repository. If that is not available, open a regular issue and label it `security`.

We will acknowledge receipt as soon as possible and work to provide a fix or mitigation.

## Security Updates

- **2026-01-04**: Fixed AppleScript injection in `codex-amq-notify.py` (message titles with quotes could break notification script)
- **2026-01-04**: Fixed `read` command to parse before moving to `cur` (prevents stuck corrupt messages)
- **2026-01-04**: Fixed `setup-coop.sh` to avoid config overwrite when `jq` unavailable
