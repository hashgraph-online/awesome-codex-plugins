# Self-Test: beads-br

## Purpose

Validate that the documented `br` + `bv` commands exist and that the skill does not reference obsolete flag forms.

## Quick Validation

```bash
# Tool presence + version
which br && br --version
which bv

# Core help surfaces exist
br --help >/dev/null
br sync --help >/dev/null
br config --help >/dev/null
bv --robot-help >/dev/null

# Config keys match docs
br config get issue-prefix --json | jq -e '.key == "issue-prefix"' >/dev/null
br config get sync-branch --json | jq -e '.key == "sync-branch"' >/dev/null

# No obsolete config flag forms in this skill
rg -n "br config --" . && exit 1 || true
rg -n "id\\.prefix|sync\\.branch" . && exit 1 || true
```

