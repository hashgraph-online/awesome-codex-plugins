# Codex Skin Packs

[![skills.sh](https://skills.sh/b/channelerh/codex-skin-packs)](https://www.skills.sh/channelerh/codex-skin-packs/codex-skin-pack-installer)

Verified public-safe Codex theme and skin packs, packaged as a Codex plugin and
a standalone Skills.sh / `npx skills` installer.

Each pack includes:

- `background.png`
- `theme.json`
- `README.md`
- restore guidance

The gallery shows sanitized Codex Home, Task, Diff, and Composer states so you
can judge readability before applying a pack. This repository does not include
private Codex workspace screenshots, task lists, chats, sidebars, file paths, or
project files.

Start here if you want one pack that is already getting the most usage signal:
https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=caishen-readable-primary

Then install it with Codex:

```bash
npx skills add ChannelerH/codex-skin-packs --skill codex-skin-pack-installer --global --agent codex --yes
```

```text
Use $codex-skin-pack-installer to install the caishen-readable Codex skin pack and tell me how to restore the default theme.
```

Native Codex App theme path, no runtime skin:

```text
codex-theme-v1:{"codeThemeId":"absolutely","theme":{"accent":"#d96b42","contrast":60,"fonts":{"ui":"Avenir Next, SF Pro Text","code":"SF Mono"},"ink":"#35251c","opaqueWindows":true,"semanticColors":{"diffAdded":"#2f8f63","diffRemoved":"#c85a42","skill":"#b77b24"},"surface":"#fffdfa"},"variant":"light"}
```

This `Caishen Readable Light` import keeps Codex on the official App theme
surface. It is under review here:
https://github.com/shaw-baobao/codex-themes/pull/2

Installer page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-pack-installer?utm_source=github-readme&utm_medium=repo&utm_campaign=skill-installer

Codex Theme Skill page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-theme-skill?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-theme-skill

Website:
https://codex-theme-gallery.howardhua.chatgpt.site?utm_source=github-readme&utm_medium=repo&utm_campaign=homepage

Theme index:
https://codex-theme-gallery.howardhua.chatgpt.site/themes?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-index

Codex themes:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-themes?utm_source=github-readme&utm_medium=repo&utm_campaign=search-pages

Codex skins:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skins?utm_source=github-readme&utm_medium=repo&utm_campaign=search-pages

Install guide:
https://codex-theme-gallery.howardhua.chatgpt.site/install-codex-theme?utm_source=github-readme&utm_medium=repo&utm_campaign=install-guide

Release downloads: https://github.com/ChannelerH/codex-skin-packs/releases/tag/v0.1.0

Safety checklist: [SAFETY.md](SAFETY.md)

Agent install prompts: [INSTALL-WITH-CODEX.md](INSTALL-WITH-CODEX.md)

Compatibility / directory notes: [COMPATIBILITY.md](COMPATIBILITY.md)

Codex Dream Skin alternatives:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-dream-skin-alternatives?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-dream-skin-alternatives

GitHub alternatives guide:
[docs/codex-dream-skin-alternatives.md](docs/codex-dream-skin-alternatives.md)

For directory maintainers:

- Real release zips are available in [v0.1.0](https://github.com/ChannelerH/codex-skin-packs/releases/tag/v0.1.0).
- The installer is available through Skills.sh / `npx skills` and the Codex plugin workflow.
- Public previews use sanitized Codex states, not private workspace screenshots.
- Codex Dream Skin `.cds-theme.zip` compatibility is available for `caishen-readable`.
- `.codexskin` compatibility is not claimed yet; the `caishen-readable` draft source and remaining preview gap are tracked in [COMPATIBILITY.md](COMPATIBILITY.md).

Skills.sh listing:
https://www.skills.sh/channelerh/codex-skin-packs/codex-skin-pack-installer

Install as a Codex Plugin:

```bash
codex plugin marketplace add ChannelerH/codex-skin-packs --ref main --sparse .agents/plugins --sparse plugins/codex-skin-pack-installer
codex plugin add codex-skin-pack-installer@codex-skin-packs
```

Then ask Codex:

```text
Use $codex-skin-pack-installer to install the caishen-readable Codex skin pack and tell me how to restore the default theme.
```

Install with the standard Agent Skills CLI:

```bash
npx skills add ChannelerH/codex-skin-packs --skill codex-skin-pack-installer --global --agent codex --yes
```

Then ask Codex:

```text
Use $codex-skin-pack-installer to install the caishen-readable Codex skin pack and tell me how to restore the default theme.
```

Legacy Codex Skill installer fallback:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo ChannelerH/codex-skin-packs --path skills/codex-skin-pack-installer --name codex-skin-pack-installer
```

Then ask Codex:

```text
Use $codex-skin-pack-installer to install the caishen-readable Codex skin pack and tell me how to restore the default theme.
```

Machine-readable theme feed:
https://codex-theme-gallery.howardhua.chatgpt.site/theme-feed.json?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-feed

Launch / directory submission kit:
https://codex-theme-gallery.howardhua.chatgpt.site/launch-kit.md?utm_source=github-readme&utm_medium=repo&utm_campaign=launch-kit

External listings:

- [Show HN: Public-safe skin packs for the Codex desktop app](https://news.ycombinator.com/item?id=49002037)
- [Codex Skin Pack Installer awesome-agent-skills submission](https://github.com/VoltAgent/awesome-agent-skills/pull/827) is open to add the installer Skill to a 28k+ star cross-agent skills directory.
- [Caishen Readable HeiGe Codex Skin Studio preset submission](https://github.com/HeiGeAi/heige-codex-skin-studio/pull/18) is open to add the pack as a built-in one-click preset in a 300+ star Codex / ChatGPT desktop skin switcher.
- [Caishen Readable Light native Codex App theme submission](https://github.com/shaw-baobao/codex-themes/pull/2) is open to add a low-friction `codex-theme-v1:` import path derived from the Caishen Readable palette.
- [Caishen Readable Get Codex Theme submission](https://github.com/ViisOpen/get-codex-theme/pull/3) is open to add the pack as a validated free theme with responsive assets, HTML/CSS preview evidence, and `npx get-codex-theme` compatibility.
- [Mythic Guardian Noir](https://codexthemes.ai/skins/mythic-guardian-noir)
- [Caishen Lite Codex Skin Pack](https://codexthemes.ai/themes/caishen-lite-codex-skin-pack)
- [TIANQIAN1238/codex-skin-gallery](https://github.com/TIANQIAN1238/codex-skin-gallery) indexes all six packs as Dream Skin Pack entries.
- [Caishen Readable review draft](https://github.com/lixiaobaivv/Codex-Skin-Store/pull/17) is open for Codex-Skin-Store review.
- [Caishen Readable `.codexskin` submission prep](https://github.com/Wangnov/awesome-codex-skins/issues/11) is open with the `.codexskin` standard repository.
- [Caishen Readable Codex Theme Gallery proposal](https://github.com/983033995/Codex-Theme-Gallery/issues/3) is open for package-intake guidance.
- [Codex Skin Gallery awesome-list submission](https://github.com/mcpso/awesome-codex-themes/pull/3) is open for Awesome Codex Themes review.
- [ChannelerH Codex skin packs awesome-list submission](https://github.com/mcpso/awesome-codex-themes/pull/5) is open to add this repository to the Runtime CDP Skins section.
- [Codex Skin Pack Installer catalog submission](https://github.com/jMerta/codex-skills/pull/9) is open for the Codex Skills catalog.
- [Codex Skills Registry catalog submission](https://github.com/vadimcomanescu/codex-skills/pull/8) is open for an installable `npx codex-skills-registry` catalog.
- [Caishen Readable AutoSkin theme submission](https://github.com/Finderchangchang/codex-autoskin/pull/3) is open to add the pack as a built-in AutoSkin theme for direct switching.
- [Caishen Readable Codex Skin Skill package submission](https://github.com/aiwenjie777/codex-skin-skill/pull/4) is open to add the pack as a bundled data-only macOS skin package.
- [Caishen Readable Codex Skin Manager preset submission](https://github.com/ZhjGo/codex-skin-manager/pull/2) is open to add the pack as a bundled manager preset with cleanup markers.
- [Caishen Readable public-safe starter recipe](https://github.com/kongxcer555/codex-skin-builder/pull/1) is open to add a reproducible starter recipe to a Codex skin-builder Skill.
- [Caishen Readable Codex Skin Switcher theme submission](https://github.com/bytefer/codex-skin-switcher/pull/1) is open to add the pack as a built-in macOS/Windows switcher theme.
- [Caishen Readable Codex NN built-in theme submission](https://github.com/slovx2/Codex-NN/pull/4) is open to add the pack as a built-in theme in a visual Codex theme manager.
- [Caishen Readable Codex Dream Skin preset submission](https://github.com/xnydl/codex-dream-skin/pull/5) is open to add the pack as a macOS bundled preset in a Dream Skin distribution.
- [Caishen Readable CodeDrobe source theme example](https://github.com/CodeDrobe/skills/pull/3) is open to add the pack as a copyable, packable Codex theme example for the CodeDrobe Skill.
- [Caishen Readable ReTheme source example](https://github.com/duxweb/ReTheme/pull/5) is open to add the pack as a validator-passing ReTheme source package example for ChatGPT/Codex desktop theming.
- [Caishen Readable public-safe starter pack reference](https://github.com/moonlin1213/codex-dream-skin-studio-skill/pull/4) is open to add the pack as a no-private-screenshot starter reference for a Dream Skin Studio Skill.
- [Caishen Readable upstream Dream Skin preset](https://github.com/Fei-Away/Codex-Dream-Skin/pull/197) is open to add the pack as a bundled macOS/Windows preset in the largest Codex Dream Skin repository.
- [Caishen Readable Theme Inject package](https://github.com/codecnmc/codex-theme-inject/pull/2) was closed by the maintainer as incompatible; keep using the release ZIP or installer Skill path instead of the Theme Inject package path.
- [Caishen Readable codex-skin.dev submission](https://github.com/EricsXian/codex-skin/issues/1) is open for an independent Codex skin gallery listing with theme page, preview, package, and installer links.
- Caishen Readable was submitted to CodexSkins.org for moderation as an installable public-safe package with the gallery page, preview image, and release zip.
- [Caishen Readable starter pack reference](https://github.com/wxqdoit/codex-dream-skin-marketplace/pull/1) is open for a Codex Dream Skin Marketplace plugin README path aimed at users who need a safe first pack before bringing their own media.
- [Caishen Readable bundled theme submission](https://github.com/houyuhang915-sudo/Codex-Skin-Manager/pull/1) is open to add the pack as a real schema 2 macOS/Windows bundled theme in a cross-platform Codex Skin Manager.
- [Caishen Readable CodeSkin theme submission](https://github.com/lntomF/codexskin/issues/2) is open for Windows CodeSkin users as a public-safe wallpaper import candidate.
- [Caishen Readable portable `.cds-theme.zip` submission](https://github.com/charmber/codex-skin/issues/1) is open for Codex Dream Skin users who want an importable package validated by the upstream theme-package script.
- [Caishen Readable Codex Skin Lab catalog candidate](https://github.com/zhoufeiii/codex-skin-lab/issues/1) is open for a desktop theme-manager catalog listing; Codex Skin Lab currently requires mirrored `codexskinlab.com` asset URLs.
- [Codex Skills Library submission](https://github.com/proflead/codex-skills-library/pull/9) is open for another Codex-focused skill discovery surface.
- [Terminal Skills catalog submission](https://github.com/TerminalSkills/skills/pull/532) is open with a skill plus a problem-first use case for safe Codex desktop skin installs.

![Codex Skin Gallery](assets/og.jpg)

## For Get Codex Theme users

If you use `get-codex-theme`, follow the Caishen Readable free-theme proposal:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=get-codex-theme-users
- Get Codex Theme PR: https://github.com/ViisOpen/get-codex-theme/pull/3
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip

The submitted pack includes responsive backgrounds, HTML/CSS preview evidence,
visual tokens, and an asset license. It has passed `get-codex-theme` strict
theme validation.

## For Windows Theme Inject users

The `codecnmc/codex-theme-inject` package PR was closed as incompatible, so do
not treat that path as supported yet. Use the release ZIP or installer Skill
instead:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-inject-users
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip
- Closed Theme Inject PR: https://github.com/codecnmc/codex-theme-inject/pull/2

Download the release zip above and keep `theme.json` and `background.png`
together.

## For CodeSkin users

If you use `lntomF/codexskin`, start with the public-safe Caishen Readable
wallpaper submission:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=codeskin-users
- Direct background image: https://codex-theme-gallery.howardhua.chatgpt.site/theme-packs/caishen-readable/background.png?utm_source=github-readme&utm_medium=repo&utm_campaign=codeskin-users
- CodeSkin submission issue: https://github.com/lntomF/codexskin/issues/2

CodeSkin derives palette and contrast from imported wallpapers, so this
submission is a safe import candidate rather than a bundled code patch.

## For ReTheme users

If you are testing ReTheme source packages, start with the Caishen Readable
source example:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=retheme-users
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip
- ReTheme PR: https://github.com/duxweb/ReTheme/pull/5

The ReTheme contribution is a public-safe source example, not a signed
community-theme package. Use it to inspect the scoped CSS, manifest, and assets
before packaging your own theme.

## For Codex Dream Skin users

If you already use Codex Dream Skin, start with the Caishen Readable upstream
preset proposal:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=dream-skin-users
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip
- Portable `.cds-theme.zip`: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.cds-theme.zip
- Largest upstream PR: https://github.com/Fei-Away/Codex-Dream-Skin/pull/197
- Alternate macOS preset PR: https://github.com/xnydl/codex-dream-skin/pull/5

The upstream preset is under review for bundled macOS and Windows support. Until
it is merged, import the portable `.cds-theme.zip`, download the release zip, or
use the installer Skill path.

The portable Codex Dream Skin package has been validated with:

```bash
node macos/scripts/theme-package.mjs validate --archive caishen-readable.cds-theme.zip
```

## For Codex Skin Lab users

If you use Codex Skin Lab, follow the Caishen Readable catalog candidate:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-lab-users
- Portable `.cds-theme.zip`: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.cds-theme.zip
- Catalog issue: https://github.com/zhoufeiii/codex-skin-lab/issues/1

Codex Skin Lab's current catalog validator requires `codexskinlab.com` image,
detail, and download URLs, so this is a catalog candidate until the maintainer
mirrors the public-safe assets.

## Packs

### Mythic Guardian Noir

Dark mythic focus skin with a quiet left side for readable Codex panels.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/mythic-guardian-noir?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Mythic Guardian Noir](packs/mythic-guardian-noir/background.png)

### Global Founder Bright

Bright overseas growth skin for shipping, analytics, and business work.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/global-founder-bright?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Global Founder Bright](packs/global-founder-bright/background.png)

### Caishen Lite

Soft fortune skin that keeps the main working area calm and readable.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-lite?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Caishen Lite](packs/caishen-lite/background.png)

### Caishen Max

More fortune, more gold, more visual punch for short immersive sessions.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-max?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Caishen Max](packs/caishen-max/background.png)

### Export Night

Dark export-ops skin with charts, ports, and midnight commerce energy.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/export-night?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Export Night](packs/export-night/background.png)

### Caishen Readable

Soft low-strain fortune skin.

Theme page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=theme-page

![Caishen Readable](packs/caishen-readable/background.png)

## Usage

Download a pack folder, keep `theme.json` and `background.png` together, then
use the theme JSON in your Codex Dream Skin workflow.

You can also copy the install prompt from the website and ask Codex to apply the
pack, verify Home / Task / Diff / Composer readability, and explain how to
restore the default appearance.

## Why public-safe?

Codex theme screenshots can accidentally expose private project names, chats,
task lists, and file paths. These packs ship only public artwork, reproducible
theme files, and sanitized demo previews.

## License

MIT. This is an independent experiment and is not affiliated with OpenAI.
