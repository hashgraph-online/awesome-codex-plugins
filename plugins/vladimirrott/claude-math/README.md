# claude-math

Make math in Claude Code and Codex legible.

<p align="center">
  <img src="assets/demo.svg" alt="Without claude-math, LaTeX prints as raw dollar-sign noise; with it, the same answer renders as clean Unicode math." width="760">
</p>

Terminal coding agents do not render LaTeX. In both **Claude Code** and
**OpenAI Codex CLI**, a formula like `$f(x) = \sum_{i=1}^n x_i$` appears as raw
dollar signs and backslashes, exactly the noise you wanted formatting to
remove. This project ships a single skill (`math-unicode`) that instructs the
model to emit math as Unicode glyphs inline. Unicode-capable terminals with a
suitable font render these glyphs directly. It installs as a Claude Code plugin
and, via the identical `SKILL.md`, as a Codex skill (`claude-math install
--codex`).

## Before / after

```
Before:  The qualifying cohort is $Q = \{ (s,r) \in T : n_{s,r} \geq 18 \wedge p^0_{s,r} < 0.9 \}$,
         with $|Q| / |T| \approx 17.3\%$.

After:   The qualifying cohort is Q = { (s,r) ∈ T : n_{s,r} ≥ 18 ∧ p⁰_{s,r} < 0.9 },
         with |Q| / |T| ≈ 17.3 %.
```

## Install

The quickest install is through the plugin marketplace (see below). The npm and manual paths also work.

### via npm

```bash
npm install -g claude-math
claude-math install
```

Symlinks the package into `~/.claude/plugins/local/claude-math`, registers it
in `installed_plugins.json`, and enables it in `settings.json` (atomically;
both files get a `.claude-math.bak` backup on first touch). Restart Claude
Code and the skill loads.

`npx claude-math install` also works: the CLI auto-detects an npx-cache
install path and **copies** rather than symlinks (since the cache directory
is ephemeral). Prefer the global install if you want updates via
`npm update -g claude-math` to propagate automatically.

Other commands:

```bash
claude-math status        # report target, validity, settings state, next-install mode
claude-math uninstall     # remove symlink/dir, deregister, disable
claude-math --help        # full flag list, env overrides
```

Flags: `--force` overrides safety checks (foreign symlinks, non-plugin
directories at the target). `--copy` forces a real copy instead of symlink.

### Manual install

```bash
git clone https://github.com/vladimirrott/claude-math \
  ~/.claude/plugins/local/claude-math
```

Then add `"claude-math@local": true` under `enabledPlugins` in
`~/.claude/settings.json` and a matching entry in
`~/.claude/plugins/installed_plugins.json`. The CLI does both; running it
once is the easiest path.

### Via Claude Code's plugin marketplace (recommended)

```
/plugin marketplace add vladimirrott/claude-math
/plugin install claude-math@vladimirrott
```

The skill normally activates for mathematical output. To load the complete
rule set explicitly in Claude Code, run `/math-unicode` before the request.

### Codex CLI

claude-math works in [OpenAI Codex CLI](https://developers.openai.com/codex/) too — the skill uses the same `name` + `description` `SKILL.md` frontmatter Codex reads. Two install paths:

**Native Codex plugin (recommended — no npm):**

```
codex plugin marketplace add vladimirrott/claude-math
codex plugin add claude-math@vladimirrott
```

Codex installs the plugin (manifest: `.codex-plugin/plugin.json`) and loads its `math-unicode` skill. Restart Codex if it does not appear; invoke with `/skills` or by mentioning `$math-unicode`. Remove with `codex plugin remove claude-math@vladimirrott`.

**Via npm (drops just the skill file):**

```bash
npm install -g claude-math
claude-math install --codex
```

This copies the skill into `~/.agents/skills/math-unicode/` (the current Codex user-skills dir; the older `~/.codex/skills/` path is deprecated but still read for backward compatibility). Use `claude-math status --codex` to check and `claude-math uninstall --codex` to remove. Set `CLAUDE_MATH_CODEX_SKILLS_DIR` to target a non-default skills directory.

Use one path or the other, not both — installing via the plugin *and* the CLI would load two copies of the same skill.

### Hacking on this repo

Working from a clone (before or after publish):

```bash
git clone https://github.com/vladimirrott/claude-math && cd claude-math
node bin/claude-math.js install     # uses the cloned directory directly
node --test test/                   # run the test suite
```

`CLAUDE_CONFIG_DIR=/tmp/somewhere claude-math install` lets you test against
a sandbox without touching your real `~/.claude` state, useful for
contributing.

The `math-unicode` skill triggers on its own when the model writes math for a
surface that cannot render LaTeX. No configuration required. See *Where the
skill should not fire* for the cases where you want it quiet.

## Which glyphs actually render

Unicode having a code point does not mean your terminal draws it. The skill
ships a measured answer rather than a guess: `scripts/measure-font-coverage.mjs`
reads the `cmap` table of twelve monospace fonts, six of the most widely
installed programming fonts (JetBrains Mono, Fira Code, Cascadia Code, Hack,
Source Code Pro, IBM Plex Mono) and six system fonts (DejaVu Sans Mono,
Liberation Mono, Ubuntu Mono, Ubuntu Sans Mono, Noto Mono, Cousine). The counts
live in the skill's *Font coverage* table and the test suite asserts every
published number against the measurement.

The short version:

- Operators, Greek letters and digit sub/superscripts render in every font
  measured. Most output is these.
- Letter sub/superscripts (`xᵢ`, `xᵀ`, `aₙ`) are DejaVu-class. JetBrains Mono,
  Fira Code, Hack and IBM Plex Mono carry none of them, so they arrive through
  fontconfig fallback there, which draws them at another font's width. That is
  why the rules keep `x_i` and `x^T` as equal alternatives.
- A short list of glyphs renders in at most one of the twelve. The skill names
  them under *Glyphs to avoid* with what to write instead.

### Wider coverage, if your font has it

If you run a font with broader Unicode coverage, the portable default leaves
glyphs on the table: Greek indices in particular, where `ᵨ` and `ᵦ` exist and
Liberation Mono and Cousine ship them. Ask for them once per session:

> Use extended glyph coverage from math-unicode.

Or put that line in your `CLAUDE.md` or `AGENTS.md` to make it permanent. The
full opt-in set, with measured coverage per glyph, is in
[`skills/math-unicode/references/extended-glyphs.md`](skills/math-unicode/references/extended-glyphs.md).
Big-operator bounds stay bracketed either way, so `∑[i=1..n]` never becomes the
mixed `∑ᵢ₌₀ⁿ` form.

## Where the skill should not fire

The skill targets surfaces that cannot render LaTeX. Its description says so, so
a host that renders math natively (ChatGPT or Codex on desktop and web) should
not pick it up. That is the model reading its own context, not an enforced
predicate: no host exposes a per-surface switch to a skill today.

To turn it off yourself, Codex takes either of these. In `~/.codex/config.toml`:

```toml
[[skills.config]]
name = "math-unicode"
enabled = false
```

Or, for explicit-only invocation while keeping `$math-unicode` available, add
`skills/math-unicode/agents/openai.yaml` to your installed copy:

```yaml
policy:
  allow_implicit_invocation: false
```

In Claude Code, `/plugin` disables the plugin, and `disable-model-invocation:
true` in the installed `SKILL.md` leaves `/math-unicode` working while stopping
automatic activation.

## Graphical rendering (sixel / kitty): not inside the chat

Rendering math as an actual image (sixel or kitty graphics) is **not possible
inside the Claude Code chat**. The TUI repaints its own screen buffer on every
update and overwrites any graphics escape sequences a plugin emits, and its
line accounting does not know an image's height. So in-chat output stays
Unicode, which is the point of this skill.

Graphics belongs in the host, not in a plugin, and that work is now underway
upstream: [openai/codex#18906](https://github.com/openai/codex/issues/18906)
has two working fork branches rendering LaTeX through the Kitty graphics
protocol (one via typst + mitex, one via `latex` + `dvipng`), and the emerging
consensus there is Unicode-first as the first milestone with a graphics backend
second. A renderer inside the host can do something this skill structurally
cannot: convert only at display time and keep the exact LaTeX in the
transcript, so nothing is lost on resume, export or copy.

This skill is therefore the stopgap for terminals and hosts that do not render
math yet. When native rendering lands where you work, prefer it.

## Why Unicode by default?

| Path | Works in plain terminal | SSH / tmux | CI logs | Copy-paste | Install cost |
|---|---|---|---|---|---|
| Unicode (this skill) | ✓ | ✓ | ✓ | ✓ | 1 file |
| Sixel / kitty graphics | ✗ (not in chat) | partial | ✗ | ✗ images | native host support |
| Pipe through external viewer | ✗ TUI breaks | n/a | ✓ if `--print` | ✓ | shell wrapper |

Unicode is the only approach that preserves text across the distribution
channels a Claude Code session commonly uses, and the only one whose output
stays selectable and greppable: a graphics placement is an image, so you cannot
search or copy the equation out of it. That is why a Unicode path stays useful
even after hosts gain a graphics backend.

## Related issues & prior art

- [anthropics/claude-code#44479](https://github.com/anthropics/claude-code/issues/44479): native LaTeX in terminal output (open)
- [anthropics/claude-code#80702](https://github.com/anthropics/claude-code/issues/80702): Markdown escaping corrupts LaTeX source before it can be rendered (open)
- [openai/codex#18906](https://github.com/openai/codex/issues/18906): Markdown math rendering in the Codex TUI (open; claude-math covers the gap today via `claude-math install --codex`)
- [warpdotdev/warp#9677](https://github.com/warpdotdev/warp/issues/9677): same gap on Warp
- [`markless`](https://github.com/jvanderberg/markless): terminal Markdown viewer with Typst math and kitty/sixel images
- [`mdviewer`](https://github.com/aquele-dinho/mdviewer), [`glowm`](https://github.com/atani/glowm), [`mdterm`](https://www.toolhunter.cc/tools/mdterm): adjacent viewers

## License

MIT.
