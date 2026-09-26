## Summary

- Adds one line to Community Plugins > Tools & Integrations (alphabetical: Codex Be Serious → **Codex Discord Bridge** → Codex Mem), per CONTRIBUTING
- No catalog files (`plugins.json`, `marketplace.json`, `plugins/`) touched; the generator mirrors the bundle from the source repo

## Scanner evidence (plugin-scanner 3.3.0, pinned wheel SHA `ff82b660…34fc37db`)

Scan against the mirrored package dir (`codex-packages/codex-discord-bridge`):

- `plugin-scanner scan`: **Final Score: 93/100 (A - Excellent)** — critical:0, high:0, medium:0, low:0, info:6
- `plugin-scanner lint`: `policy_pass=True`, effective_score=91 (info-level interface-asset suggestions only)
- `plugin-scanner verify`: **Verification: PASS**

## Plugin repo

https://github.com/yaffalhakim1/codex-discord-bridge

Rust serenity bridge connecting Discord to the Codex app-server (JSON-RPC over WebSocket): live-streamed replies, button-based approvals, thread-per-conversation mapping, bounded reconnect supervisor. Ships `.codex-plugin/plugin.json` + one setup skill; MIT, SECURITY.md included.
