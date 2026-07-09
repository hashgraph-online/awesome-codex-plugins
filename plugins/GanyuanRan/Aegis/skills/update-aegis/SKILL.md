---
name: update-aegis
description: Use when the user says `aegis:update`, asks to update or upgrade an installed Aegis method-pack, wants the latest Aegis version, or asks whether Aegis is current on this host.
---

# Update Aegis

Update the installed Aegis Method Pack for the current AI coding host.

This skill is host maintenance. Do not edit the target project just because the
user asked to update Aegis.

## Default Semantics

- `aegis:update` updates the current host's registered Aegis installation.
- Updating every registered host requires an explicit `--all` request.
- If more than one host is registered and the current host cannot be identified,
  ask one concrete question before updating.
- Do not update a development checkout when the installed method-pack root is a
  separate path.
- Do not perform background automatic updates. The local registry may record
  `updateMode`, but this skill only performs explicit user-triggered updates.

## Evidence First

From the installed method-pack root, inspect the host-scoped registry:

```bash
python scripts/aegis-update.py status --json
```

If the registry is missing, register the current host before updating. Use the
host's install guide and actual discovery path rather than guessing.

If `~/.config/aegis/config.toml` already declares `method_pack_root`, prefer
that canonical root when registering additional hosts. Host-specific discovery
paths, copied skill directories, plugin caches, or adapter payloads should be
treated as generated / host-managed views into the same Aegis body, not as
separate editable checkouts.

Codex example:

```bash
python scripts/aegis-update.py register \
  --host codex \
  --sync-mode junction \
  --discovery-root ~/.agents/skills/aegis \
  --reload-hint "restart Codex"
```

Copy-based host example:

```bash
python scripts/aegis-update.py register \
  --host codebuddy \
  --sync-mode copy-skills \
  --discovery-root ~/.codebuddy/skills \
  --reload-hint "restart CodeBuddy"
```

Prefixed direct-child host example:

```bash
python scripts/aegis-update.py register \
  --host copilot \
  --sync-mode junction \
  --discovery-shape direct-child \
  --discovery-root <target-repo>/.github/skills \
  --discovery-name-prefix aegis- \
  --reload-hint "restart Copilot session or reopen the repository"
```

Kimi Code CLI direct-child host example:

```bash
python scripts/aegis-update.py register \
  --host kimi-code \
  --sync-mode junction \
  --reload-hint "restart Kimi Code CLI"
```

When `--discovery-root` is omitted for `kimi`, `kimi-code`, or
`kimi-code-cli`, the updater uses `$KIMI_CODE_HOME/skills` or, when
`KIMI_CODE_HOME` is unset, `~/.kimi-code/skills`.

Plugin-managed hosts can be registered, but the updater reports that the host
plugin manager owns the update path:

```bash
python scripts/aegis-update.py register \
  --host opencode \
  --sync-mode plugin-managed \
  --reload-hint "restart OpenCode"
```

## Update Commands

Current or explicitly selected host:

```bash
python scripts/aegis-update.py update --host <host> --json
```

All registered hosts, only when the user explicitly asks for all-host update:

```bash
python scripts/aegis-update.py update --all --json
```

Preview without touching files:

```bash
python scripts/aegis-update.py update --host <host> --dry-run --json
```

If the installed checkout has local changes, do not overwrite them. Either ask
the user how to proceed or, with explicit permission, preserve them with:

```bash
python scripts/aegis-update.py update --host <host> --stash --json
```

## Completion Evidence

Treat the update as complete only when the updater reports the selected host and
the post-update doctor verification succeeds. For link-based discovery roots
(`junction`, `symlink`, or `repo-only`), the updater passes `discoveryRoot`
through to `aegis-doctor.py --discovery-root`; when a registered direct-child
view declares `discoveryNamePrefix`, the updater also passes
`--discovery-name-prefix`. For copy-based hosts, it verifies that copied Aegis
skill directories exist after the copy step, then runs doctor against the
method-pack root.

When multiple registered hosts share the same `methodPackRoot`, the updater now
reuses a single method-pack checkout update and then refreshes each host's
exposure or verification path separately.

Report:

- selected host / installation id
- previous and final commit when available
- whether the install was updated or already current
- sync mode used
- doctor verification result
- restart or reload hint

If the updater skips a `plugin-managed` host, state that the host plugin manager
owns the update path and give the reload or reinstall hint.
