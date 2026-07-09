# ArmorCodex Plugin Assets

This directory holds the visual assets the Codex plugin manifest
(`.codex-plugin/plugin.json`) references. All files are PNG and live at the
plugin root per the published spec.

## Current assets

| Path | Manifest field | Purpose |
| --- | --- | --- |
| `assets/armoriq-logo.png` | `interface.composerIcon` and `interface.logo` | Icon shown in the Codex composer UI and on plugin detail pages. |

## Optional follow-up

Drop additional screenshots here and add them to `interface.screenshots` in
`.codex-plugin/plugin.json` when ready. Suggested set, in order:

- `screenshot-policy.png` (policy management view)
- `screenshot-intent-drift.png` (intent drift block)
- `screenshot-audit.png` (audit trail)

Notes:

- All paths must be relative and start with `./` per the spec.
- Screenshot entries must be PNG and stored under `./assets/`.
- ArmorIQ brand color: `#00E5CC` (teal).
