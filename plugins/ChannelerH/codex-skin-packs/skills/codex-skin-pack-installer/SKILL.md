---
name: codex-skin-pack-installer
description: Install Codex themes and Codex skin packs with npx skills. Use this skill when a user wants Codex to find, download, validate, apply, switch, remix, or restore Codex desktop themes such as caishen-lite, mythic-guardian-noir, global-founder-bright, export-night, caishen-readable, or caishen-max. It stages verified public-safe theme packs from ChannelerH/codex-skin-packs, checks theme.json/background.png, preserves the native Codex layout, avoids private workspace screenshots, and provides restore guidance.
---

# Codex Skin Pack Installer

Install verified Codex theme and skin packs without publishing private workspace screenshots or editing the signed app bundle.

This is a Skills.sh / `npx skills` installer for public-safe Codex desktop themes. It is meant for users searching for "Codex theme", "Codex skin", "install Codex theme", or "Codex Dream Skin packs" who want a real downloadable theme pack instead of a private screenshot.

## Quick Start

Install this skill:

```bash
npx skills add ChannelerH/codex-skin-packs --skill codex-skin-pack-installer --global --agent codex --yes
```

Use the helper script to download and stage a pack:

```bash
python3 "$CODEX_SKILL_DIR/scripts/fetch_skin_pack.py" caishen-lite
```

The script downloads from the public GitHub release, validates the zip, extracts it to `~/.codexthemes/packs/<slug>` by default, and writes a source manifest.

List available packs:

```bash
python3 "$CODEX_SKILL_DIR/scripts/fetch_skin_pack.py" --list
```

## Workflow

1. Identify the requested pack slug. If the user gives a vague style, list available packs and pick the closest match.
2. Run `scripts/fetch_skin_pack.py <slug>` unless the user already has a local pack folder.
3. Inspect the staged folder. It must contain `theme.json`, `background.png`, and preferably `README.md`.
4. Apply the staged pack through the user's active Codex theme manager or Codex Dream Skin workflow. Do not modify `app.asar`, signed application bundles, private task data, or private screenshots.
5. Verify the Codex Home, Task, Diff, and Composer states for readability. If a live UI check is not possible, say that clearly and provide the staged path plus manual apply guidance.
6. Always finish with the restore path: use the active theme manager's restore command or restore the default Codex appearance from the saved/original theme state.

## Pack Slugs

- `caishen-lite` - soft fortune skin with readable working areas.
- `caishen-readable` - lower-strain fortune skin.
- `caishen-max` - brighter fortune skin for short immersive sessions.
- `global-founder-bright` - bright international growth/workspace skin.
- `export-night` - dark export-ops skin.
- `mythic-guardian-noir` - dark mythic focus skin.

## Safety Rules

- Do not upload or publish the user's real Codex workspace screenshots.
- Do not include task names, chats, sidebars, file paths, emails, keys, or project names in public assets.
- Do not claim the pack is official OpenAI software.
- Do not patch `app.asar` or the signed Codex application bundle.
- Keep `theme.json` and `background.png` together; a background without matching theme colors is not a complete skin.

## Useful Prompts

Apply a staged pack:

```text
Apply the Codex skin pack staged at STAGED_PATH.
Use the active Codex theme manager or Codex Dream Skin workflow.
Keep the native Codex layout interactive.
Do not upload private workspace screenshots.
Verify Home, Task, Diff, and Composer readability.
Tell me the restore path before finishing.
```

Restore default appearance:

```text
Restore my Codex desktop theme to the default appearance.
Use the active Codex theme manager's restore path.
Verify the sidebar, home screen, task view, diff view, and composer are back to readable native styling.
Do not modify app.asar or the signed application bundle.
```
