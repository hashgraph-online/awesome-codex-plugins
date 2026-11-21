# Licensing

Research, not legal advice.

## Paper Shaders license by version

| npm versions | Published | License |
|---|---|---|
| 0.0.10 – 0.0.46 | 2024-10-16 → 2025-08-18 | MIT |
| 0.0.47 – 0.0.76 | 2025-09-01 → 2026-04-15 | PolyForm Shield 1.0.0 (the LICENSE switched on 2025-08-22, commit `8925330`) |
| 0.0.77 – 0.0.82 | 2026-07-02 → 2026-10-21 | Apache-2.0 (switched on 2026-06-27, commit `931beca`) |

This skill pins **0.0.82**. Never pin 0.0.47–0.0.76: PolyForm Shield forbids using the software in a product that competes with Paper's. When you bump the version, check the `license` field of the new release on npm and its `LICENSE` file first.

## What Apache-2.0 allows

- Commercial use, modification and redistribution, including in client and ad videos.
- No on-screen credit. Apache-2.0 sets conditions on redistributing the code, not on what the code renders.
- Redistributing the code (vendoring `dist/` into a project, bundling it into an app) means shipping its `LICENSE` and `NOTICE` with that copy and marking files you changed.
- No trademark rights (section 6). Do not call a product "Paper Shaders" or suggest Paper endorses it; naming the library in credits or docs is fine.

## This skill's files

- Code and docs: MIT, like the rest of `vargHQ/skills`.
- `assets/presets/*.json` and `assets/paper-shaders.params.json`: derived from Paper Shaders 0.0.82, so `NOTICE` carries Paper's attribution and `LICENSE-paper-shaders` holds the Apache-2.0 text.
- The skill bundles no Paper Shaders code; the templates load it from npm or jsDelivr.

## What users bring

- Logos and stills passed to image presets must be the user's own or licensed for the use. Do not apply a shader to another company's logo without permission.
- Photos of people through `halftone-overlay` or `paper-finish` need the same consent as the photo itself.
