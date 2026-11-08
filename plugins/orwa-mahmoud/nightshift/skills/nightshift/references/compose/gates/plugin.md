# Claude or Codex plugin — a plugin manifest

## Detect

`.claude-plugin/` or `.codex-plugin/` at the work-target root, or `plugins/<name>/`. A nested manifest at `plugins/<name>/.claude-plugin/` or `plugins/<name>/.codex-plugin/` is a match when no stack matched.

Match: plugin

## Item gate

`bats -r tests/` when tests exist; tracked `*.sh` through `shellcheck -x`; `claude plugin validate . --strict`

## Site inspection

repeat the item gate

## Notes

The commands need bats, shellcheck, and the plugin validator installed. This stack is used only when no stack matched.
