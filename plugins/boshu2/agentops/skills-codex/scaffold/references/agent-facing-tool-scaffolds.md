# Agent-Facing Tool Scaffolds

Use this reference when the scaffold output will be consumed by agents, installed by shell scripts, or exposed as a tool server.

## Installer Workmanship

Installer scripts must be boring and reversible:

- Detect platform and shell before mutation.
- Print what will change before changing it.
- Use idempotent directory creation and file writes.
- Avoid `curl | sh` in generated docs unless the repo explicitly accepts it.
- Leave an uninstall or rollback path.
- Verify the installed command after mutation.

## Agent-Facing Tool Server Rules

For MCP or similar tool servers:

- Tool names should describe user intent, not implementation internals.
- Inputs should be structured and narrow.
- Errors should explain what the agent can try next.
- Dangerous tools need dry-run or confirmation flows.
- Every tool should have at least one fixture-backed smoke test.

## Rust CLI With Local State

When scaffolding a Rust CLI that stores local state:

- Prefer SQLite for transactional state and JSONL for inspectable event logs.
- Keep migrations explicit and tested.
- Expose `--json` for agent-readable output.
- Separate command parsing from storage logic.

---

**Source:** Adapted from an external skill corpus / `installer-workmanship`, `mcp-server-design`, and `rust-cli-with-sqlite`. Pattern-only, no verbatim text.
