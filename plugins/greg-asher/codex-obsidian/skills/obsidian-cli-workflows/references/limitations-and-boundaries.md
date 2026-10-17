# Limitations and Boundaries

## This skill supports

- named one-command workflow orchestration across official Obsidian desktop CLI domain skills
- preview-first execution planning with explicit risk labels
- explicit apply confirmation semantics for mutating workflows
- capability-gated publish workflow checks

## This skill does not cover

- direct command-family execution ownership for note, base, runtime, devtools, sync/publish, or workspace domains
- community/non-official Obsidian CLI tools
- `obsidian://` launcher automation
- Headless Sync automation
- implicit natural-language-only workflow invocation in this release

## Operational limits

- requires Obsidian desktop CLI availability through delegated domain skills
- publish workflow is blocked when local CLI lacks `publish:*` command support
- `vault:open` is intentionally excluded from executable workflow steps in this release
- high-impact workflows require explicit apply confirmation before mutation
