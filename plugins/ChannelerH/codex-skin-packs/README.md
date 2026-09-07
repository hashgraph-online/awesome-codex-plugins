# Codex Skin Packs

[![skills.sh](https://skills.sh/b/channelerh/codex-skin-packs)](https://www.skills.sh/channelerh/codex-skin-packs/codex-skin-pack-installer)

Verified public-safe Codex theme and skin packs, packaged as a Codex plugin and
a standalone Skills.sh / `npx skills` installer.

## External discovery paths

These are public discovery paths, not endorsements or official OpenAI channels:

- [Awesome AI Plugins](https://github.com/hashgraph-online/awesome-ai-plugins#development--workflow) lists `Codex Skin Pack Installer` and includes a marketplace JSON entry.
- [Awesome Codex Plugins](https://github.com/hashgraph-online/awesome-codex-plugins#development--workflow) lists the same installer for Codex plugin users.
- [Awesome Codex Plugins simple list](https://github.com/noahfraiture/awesome-codex-plugins#plugins) merged the same installer with a copyable Codex plugin command.
- [ReTheme](https://github.com/duxweb/ReTheme/tree/main/docs/theme-example/caishen-readable) merged `Caishen Readable` as a validator-passing public source package example.
- [DevBytes covered the installer](https://devbytes.co.in/news/for-codex-users-install-and-verify-skin-packs-with-ease) with `Caishen Readable` as the first pack to try.
- GitHub topic pages such as [`openai-codex`](https://github.com/topics/openai-codex?o=desc&s=updated) and [`npx-skills`](https://github.com/topics/npx-skills) surface this repository for Codex/Skills discovery.

## Official theme compatibility

OpenAI now documents native Codex appearance controls for base theme,
accent/background/foreground colors, UI fonts, code fonts, and shareable custom
themes:

- Codex app Appearance: https://developers.openai.com/codex/changelog#themes
- Codex Settings source mirror: https://developers.openai.com/codex/llms-full.txt
- Codex CLI `.tmTheme` support: https://developers.openai.com/codex/cli-customization#syntax-highlighting-and-themes
- Native-vs-skin guide: https://codex-theme-gallery.howardhua.chatgpt.site/official-codex-themes?utm_source=github-readme&utm_medium=repo&utm_campaign=official-codex-themes

Use the native Codex theme import when you only need colors and fonts. Use these
skin packs when you want public-safe artwork, downloadable release assets,
installer prompts, compatibility files, and explicit restore guidance.

## 30-second try path

Use the readable Caishen pack first. It has the clearest install path and the
most current usage signal.

Install the Skill:

```bash
npx skills add ChannelerH/codex-skin-packs --skill codex-skin-pack-installer --global --agent codex --yes
```

Then ask Codex:

```text
Use $codex-skin-pack-installer to install the caishen-readable Codex skin pack.
Download and inspect the pack first, preserve the native Codex layout, verify readability, and tell me the restore path.
```

- Live install page: https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-pack-installer?utm_source=github-readme&utm_medium=repo&utm_campaign=quick-start
- Caishen Readable preview: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=quick-start
- Standard zip: https://codex-theme-gallery.howardhua.chatgpt.site/theme-packs/caishen-readable.zip
- DreamSkin Studio import guide: https://codex-theme-gallery.howardhua.chatgpt.site/dreamskin-studio?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-import
- DreamSkin Studio tracked package: https://codex-theme-gallery.howardhua.chatgpt.site/api/download/caishen-readable-dreamskin?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-import
- DreamSkin Package v1 JSON fixture: [compat/dreamskin-package-v1](compat/dreamskin-package-v1)
- Codex Dream Skin import: https://codex-theme-gallery.howardhua.chatgpt.site/theme-packs/caishen-readable.cds-theme.zip
- CodeDrobe import: https://codex-theme-gallery.howardhua.chatgpt.site/theme-packs/caishen-readable.codedrobe-theme

This is an independent, unofficial package set. It contains original artwork and
theme files only, not private Codex screenshots, chats, task names, or file
paths.

Each pack includes:

- `background.png`
- `theme.json`
- `README.md`
- restore guidance

The gallery shows sanitized Codex Home, Task, Diff, and Composer states so you
can judge readability before applying a pack. This repository does not include
private Codex workspace screenshots, task lists, chats, sidebars, file paths, or
project files.

<details>
<summary>Native imports, compatibility links, and long-tail pages</summary>

Native Codex App theme path, no runtime skin:

```text
codex-theme-v1:{"codeThemeId":"absolutely","theme":{"accent":"#d96b42","contrast":60,"fonts":{"ui":"Avenir Next, SF Pro Text","code":"SF Mono"},"ink":"#35251c","opaqueWindows":true,"semanticColors":{"diffAdded":"#2f8f63","diffRemoved":"#c85a42","skill":"#b77b24"},"surface":"#fffdfa"},"variant":"light"}
```

Paste-ready import file:
[native-themes/caishen-readable-light.codex-theme.txt](native-themes/caishen-readable-light.codex-theme.txt)

Raw theme JSON:
[native-themes/caishen-readable-light.json](native-themes/caishen-readable-light.json)

Tracked release downloads:

- https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable-light.codex-theme.txt
- https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable-light.codex-theme-v1
- https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable-light.json
- https://codex-theme-gallery.howardhua.chatgpt.site/dreamskin-studio?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-import
- https://codex-theme-gallery.howardhua.chatgpt.site/api/download/caishen-readable-dreamskin?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-import
- https://codex-theme-gallery.howardhua.chatgpt.site/theme-packs/caishen-readable.codedrobe-theme

This `Caishen Readable Light` import keeps Codex on the official App theme
surface. It is under review here:
https://github.com/shaw-baobao/codex-themes/pull/2

Installer page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-pack-installer?utm_source=github-readme&utm_medium=repo&utm_campaign=skill-installer

Codex Theme Skill page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-theme-skill?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-theme-skill

Codex Skin Builder page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-builder?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-builder

Codex Skin Maker page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-maker?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-maker

Codex Skin Studio page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-studio?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-studio

Codex Skin Download page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-download?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-download

Codex Skin Generator page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-generator?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-generator

Install Codex Skin page:
https://codex-theme-gallery.howardhua.chatgpt.site/install-codex-skin?utm_source=github-readme&utm_medium=repo&utm_campaign=install-codex-skin

Codex Skin Manager page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-manager?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-manager

Codex Skin Switcher page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-switcher?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-switcher

Codex Theme Generator page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-theme-generator?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-theme-generator

Codex Theme Import page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-theme-import?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-theme-import

Codex Appearance Settings page:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-appearance-settings?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-appearance-settings

Change Codex Theme page:
https://codex-theme-gallery.howardhua.chatgpt.site/change-codex-theme?utm_source=github-readme&utm_medium=repo&utm_campaign=change-codex-theme

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

Install Codex skin:
https://codex-theme-gallery.howardhua.chatgpt.site/install-codex-skin?utm_source=github-readme&utm_medium=repo&utm_campaign=install-codex-skin

Codex skin manager:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-manager?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-manager

Codex skin switcher:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-skin-switcher?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-skin-switcher

Release downloads: https://github.com/ChannelerH/codex-skin-packs/releases/tag/v0.1.0

Safety checklist: [SAFETY.md](SAFETY.md)

Agent install prompts: [INSTALL-WITH-CODEX.md](INSTALL-WITH-CODEX.md)

Compatibility / directory notes: [COMPATIBILITY.md](COMPATIBILITY.md)

Codex Dream Skin alternatives:
https://codex-theme-gallery.howardhua.chatgpt.site/codex-dream-skin-alternatives?utm_source=github-readme&utm_medium=repo&utm_campaign=codex-dream-skin-alternatives

GitHub alternatives guide:
[docs/codex-dream-skin-alternatives.md](docs/codex-dream-skin-alternatives.md)

</details>

For directory maintainers:

- Real release zips are available in [v0.1.0](https://github.com/ChannelerH/codex-skin-packs/releases/tag/v0.1.0).
- The installer is available through Skills.sh / `npx skills` and the Codex plugin workflow.
- The plugin is listed in [Awesome Codex Plugins](https://github.com/hashgraph-online/awesome-codex-plugins#development--workflow) and its generated marketplace entry references `codex-skin-pack-installer`.
- The plugin is also listed in [Awesome AI Plugins](https://github.com/hashgraph-online/awesome-ai-plugins#development--workflow), including the public marketplace JSON entry for cross-assistant plugin discovery.
- The plugin is merged into the simpler [Awesome Codex Plugins list](https://github.com/noahfraiture/awesome-codex-plugins#plugins) as another source-visible Codex plugin discovery path.
- Public previews use sanitized Codex states, not private workspace screenshots.
- DreamSkin Studio `.dreamskin` compatibility is available for `caishen-readable`; package publishing to dreamskin.cc still requires an authenticated publisher and rights confirmation.
- Experimental DreamSkin Package v1 JSON-envelope fixture files are available in [compat/dreamskin-package-v1](compat/dreamskin-package-v1) for `Fei-Away/Codex-Dream-Skin#108` implementers.
- Codex Dream Skin `.cds-theme.zip` compatibility is available for `caishen-readable`.
- CodeDrobe `.codedrobe-theme` compatibility is available for `caishen-readable` after upstream requested theme-market submission.
- `.codexskin` compatibility is not claimed yet; the `caishen-readable` draft source and remaining preview gap are tracked in [COMPATIBILITY.md](COMPATIBILITY.md).

Skills.sh listing:
https://www.skills.sh/channelerh/codex-skin-packs/codex-skin-pack-installer

Install from the Awesome Codex Plugins marketplace:

```bash
codex plugin marketplace add https://github.com/hashgraph-online/awesome-codex-plugins.git --ref main --sparse .agents/plugins --sparse plugins
codex plugin add codex-skin-pack-installer@awesome-codex-plugins
```

Install from the Awesome AI Plugins marketplace:

```bash
codex plugin marketplace add https://github.com/hashgraph-online/awesome-ai-plugins.git --ref main --sparse .agents/plugins --sparse plugins
codex plugin add codex-skin-pack-installer@awesome-ai-plugins
```

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
- [DevBytes: For Codex users: Install and verify skin packs with ease](https://devbytes.co.in/news/for-codex-users-install-and-verify-skin-packs-with-ease) covers the installer flow and recommends Caishen Readable as the first pack to try.
- [Awesome AI Plugins marketplace listing](https://github.com/hashgraph-online/awesome-ai-plugins#development--workflow) includes `codex-skin-pack-installer` for broader agent/plugin discovery.
- [Awesome Codex Plugins simple list](https://github.com/noahfraiture/awesome-codex-plugins#plugins) now includes `Codex Skin Pack Installer` after [PR #8](https://github.com/noahfraiture/awesome-codex-plugins/pull/8) merged.
- [Codex Skin Pack Installer awesome-agent-skills submission](https://github.com/VoltAgent/awesome-agent-skills/pull/827) is open to add the installer Skill to a 28k+ star cross-agent skills directory.
- [Caishen Readable HeiGe Codex Skin Studio preset submission](https://github.com/HeiGeAi/heige-codex-skin-studio/pull/18) is open to add the pack as a built-in one-click preset in a 300+ star Codex / ChatGPT desktop skin switcher.
- [Caishen Readable Codex Styler built-in theme submission](https://github.com/xuhuanstudio/codex-styler/pull/34) is open to add the pack as a built-in theme in an open-source Codex theme editor and skin creator.
- [Caishen Readable Codex Theme Creator preset submission](https://github.com/swording-k/codex-theme-creator/pull/3) is open to add the pack as a bundled Dream Skin preset in a desktop theme creator and manager.
- [Caishen Readable Codex Theme Studio preset submission](https://github.com/JasonSTong/codex-theme-studio/pull/1) is open to add the pack as a bundled preset in a 100+ star local-first Codex theme studio.
- [Caishen Readable CC Theme registry candidate](https://github.com/quanzhankeji/cc-theme-themes/issues/1) is open for a future `.cctheme` preset release path in a deterministic package registry.
- [Caishen Readable Light native Codex App theme submission](https://github.com/shaw-baobao/codex-themes/pull/2) is open to add a low-friction `codex-theme-v1:` import path derived from the Caishen Readable palette.
- [Caishen Readable Get Codex Theme submission](https://github.com/ViisOpen/get-codex-theme/pull/3) is open to add the pack as a validated free theme with responsive assets, HTML/CSS preview evidence, and `npx get-codex-theme` compatibility.
- [Fortune Desk Caishen ACT theme candidate](https://github.com/rwang23/awesome-codex-theme/pull/3) is open to move the Caishen direction into the Awesome Codex Theme Manager review/generation flow after its Reddit launch traffic.
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
- [Caishen Readable AutoSkin built-in theme](https://github.com/Finderchangchang/codex-autoskin/tree/master/themes/caishen-readable) is merged into `Finderchangchang/codex-autoskin` for direct switching from the AutoSkin engine.
- [Caishen Readable AutoSkin README index](https://github.com/Finderchangchang/codex-autoskin/pull/5) is merged, so AutoSkin's built-in theme table now links the source pack.
- [Caishen Readable Codex Skin Skill package submission](https://github.com/aiwenjie777/codex-skin-skill/pull/4) is open to add the pack as a bundled data-only macOS skin package.
- [Caishen Readable Codex Skin Manager preset submission](https://github.com/ZhjGo/codex-skin-manager/pull/2) is open to add the pack as a bundled manager preset with cleanup markers.
- [Caishen Readable public-safe starter recipe](https://github.com/kongxcer555/codex-skin-builder/pull/1) is open to add a reproducible starter recipe to a Codex skin-builder Skill.
- [Caishen Readable Codex Skin Switcher theme submission](https://github.com/bytefer/codex-skin-switcher/pull/1) is open to add the pack as a built-in macOS/Windows switcher theme.
- [Caishen Readable Codex NN built-in theme submission](https://github.com/slovx2/Codex-NN/pull/4) is open to add the pack as a built-in theme in a visual Codex theme manager.
- [Caishen Readable Codex Dream Skin preset submission](https://github.com/xnydl/codex-dream-skin/pull/5) is open to add the pack as a macOS bundled preset in a Dream Skin distribution.
- [Caishen Readable CodeDrobe source theme example](https://github.com/CodeDrobe/skills/pull/3) is open to add the pack as a copyable, packable Codex theme example for the CodeDrobe Skill.
- [Caishen Readable ReTheme source example](https://github.com/duxweb/ReTheme/tree/main/docs/theme-example/caishen-readable) is merged as a validator-passing ReTheme source package example for ChatGPT/Codex desktop theming after [PR #5](https://github.com/duxweb/ReTheme/pull/5).
- [Caishen Readable public-safe starter pack reference](https://github.com/moonlin1213/codex-dream-skin-studio-skill/pull/4) is open to add the pack as a no-private-screenshot starter reference for a Dream Skin Studio Skill.
- [Caishen Readable upstream Dream Skin preset](https://github.com/Fei-Away/Codex-Dream-Skin/pull/197) was closed after maintainers moved community intake to DreamSkin Studio; use the `.dreamskin` package for the new import path and publish only after authenticated rights confirmation.
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

- Tester guide: https://codex-theme-gallery.howardhua.chatgpt.site/get-codex-theme?utm_source=github-readme&utm_medium=repo&utm_campaign=get-codex-theme-users
- Source pack page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=get-codex-theme-users
- Get Codex Theme PR: https://github.com/ViisOpen/get-codex-theme/pull/3
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip

The submitted pack includes responsive backgrounds, HTML/CSS preview evidence,
visual tokens, and an asset license. It has passed `get-codex-theme` strict
theme validation. The public `npx get-codex-theme install caishen-readable`
path should be treated as pending until the upstream free-theme PR is merged.

Current PR test path:

```bash
git clone https://github.com/ViisOpen/get-codex-theme.git
cd get-codex-theme
gh pr checkout 3
npm install
node packages/theme-cli/bin/get-codex-theme.mjs validate themes/free/caishen-readable --strict-assets
node packages/theme-cli/bin/get-codex-theme.mjs install themes/free/caishen-readable
node packages/theme-cli/bin/get-codex-theme.mjs apply caishen-readable
node packages/theme-cli/bin/get-codex-theme.mjs status
```

## For Codex AutoSkin users

Caishen Readable is now merged into Codex AutoSkin as a built-in data-only
theme:

- Built-in theme: https://github.com/Finderchangchang/codex-autoskin/tree/master/themes/caishen-readable
- Merged PR: https://github.com/Finderchangchang/codex-autoskin/pull/3
- AutoSkin handoff page: https://codex-theme-gallery.howardhua.chatgpt.site/codex-autoskin?utm_source=github-readme&utm_medium=repo&utm_campaign=autoskin-users
- Source pack page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=autoskin-users

Mac:

```bash
git clone https://github.com/Finderchangchang/codex-autoskin.git
cd codex-autoskin
scripts/autoskin-macos.sh install
scripts/autoskin-macos.sh theme caishen-readable fullscreen
```

Windows:

```powershell
git clone https://github.com/Finderchangchang/codex-autoskin.git
cd codex-autoskin
.\quickstart.ps1
node scripts\set-theme.mjs caishen-readable fullscreen
```

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
- ReTheme source example: https://github.com/duxweb/ReTheme/tree/main/docs/theme-example/caishen-readable
- Merged ReTheme PR: https://github.com/duxweb/ReTheme/pull/5

The ReTheme contribution is a public-safe source example, not a signed
community-theme package. Use it to inspect the scoped CSS, manifest, and assets
before packaging your own theme.

## For Codex Dream Skin users

If you already use Codex Dream Skin or DreamSkin Studio, start with the
Caishen Readable import fixture:

- Gallery page: https://codex-theme-gallery.howardhua.chatgpt.site/themes/caishen-readable?utm_source=github-readme&utm_medium=repo&utm_campaign=dream-skin-users
- DreamSkin Studio import guide: https://codex-theme-gallery.howardhua.chatgpt.site/dreamskin-studio?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-users
- DreamSkin Studio tracked package: https://codex-theme-gallery.howardhua.chatgpt.site/api/download/caishen-readable-dreamskin?utm_source=github-readme&utm_medium=repo&utm_campaign=dreamskin-studio-users
- Release zip: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.zip
- Portable `.cds-theme.zip`: https://github.com/ChannelerH/codex-skin-packs/releases/download/v0.1.0/caishen-readable.cds-theme.zip
- Upstream package-format issue: https://github.com/Fei-Away/Codex-Dream-Skin/issues/108
- Closed upstream preset PR: https://github.com/Fei-Away/Codex-Dream-Skin/pull/197
- Alternate macOS preset PR: https://github.com/xnydl/codex-dream-skin/pull/5

The large upstream project now points community intake toward DreamSkin Studio
instead of preset PRs. The `.dreamskin` fixture contains `manifest.json`,
`theme.json`, and `background.jpg` only; it is useful for local Studio preview
and for format discussion, not a claim of gallery acceptance.

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
