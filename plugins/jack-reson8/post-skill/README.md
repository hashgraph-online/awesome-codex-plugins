# Post · share images that look native and sell

English | [简体中文](https://github.com/jack-reson8/post-skill/blob/main/README.zh-CN.md) | [日本語](https://github.com/jack-reson8/post-skill/blob/main/README.ja.md) | [한국어](https://github.com/jack-reson8/post-skill/blob/main/README.ko.md) | [Tiếng Việt](https://github.com/jack-reson8/post-skill/blob/main/README.vi.md) | [हिन्दी](https://github.com/jack-reson8/post-skill/blob/main/README.hi.md)

**Give Claude today's facts. Get a Xiaohongshu / X image set that looks like real app screens, reads like a person with jokes, and pushes your product and your series.**

<table><tr>
<td><img src="docs/frame-1.jpg" width="170"></td>
<td><img src="docs/frame-2.jpg" width="170"></td>
<td><img src="docs/frame-3.jpg" width="170"></td>
<td><img src="docs/frame-4.jpg" width="170"></td>
<td><img src="docs/frame-5.jpg" width="170"></td>
</tr></table>
<sub>Day 1 of a building-in-public series ("make Claude earn back its own $200 subscription"), made with this skill.</sub>

Most AI-made post images fail the same way: gradient cards, emoji lists, a "designed" scene that screams template. This skill came out of 7 rounds of real rejections ("ugly", "looks AI-made", "doesn't look like Claude", "too serious") until the set was accepted. The method that fixed it is what it encodes:

| Step | What Claude does |
|---|---|
| 1 · Brief | `brief.md`: the post's GTM job, series identity, and a list of true facts with sources — nothing else may appear in an image |
| 2 · References | Grids the platform's top covers by likes, studies App Store screenshot sets of tasteful apps, writes 3 takeaways (gate) |
| 3 · Storyboard | One row per frame: headline, evidence, floating card, joke, GTM role. Required: cover with series lockup, product frame with real output + price, full-bleed number page, follow hook |
| 4 · Copy | Plain first, then 1–3 jokes from a pattern library (rhetorical-question titles, one-line beats, deadpan, callbacks, contrast endings) |
| 5 · Build | Real mobile screenshots, pixel-faithful UI mocks (X, Claude, iOS lock screen, Google, Stripe), figures that aren't tables, App Store poster template |
| 6 · Review | Contact sheet at thumbnail size against a checklist |
| 7 · Hand-off | Sheet + 2–3 title options. Publishing stays with you |

## Install

**As a Claude Code plugin (recommended)**

```bash
claude plugin marketplace add jack-reson8/post-skill
claude plugin install post@post-skill
```

**As a plain skill**

```bash
git clone https://github.com/jack-reson8/post-skill
cp -R post-skill/plugins/post/skills/post ~/.claude/skills/
```
Needs Google Chrome (headless rendering) and Python 3 with Pillow for contact sheets.

**Codex** (CLI or the ChatGPT desktop app):

```bash
codex plugin marketplace add jack-reson8/post-skill
codex plugin add post@post-skill
```

Or copy `plugins/post/skills/post` into `~/.codex/skills/`. The skill follows the open [Agent Skills](https://agentskills.io) standard, so it works in Claude Code, Codex and any agent that reads SKILL.md.

**Other agents** (Cursor, Gemini CLI, GitHub Copilot and other agents supported by the skills CLI):

```bash
npx skills add jack-reson8/post-skill
```

## Honesty rules built in
True facts only; dialogue mocks are reconstructions of real conversations; never fake other people's messages, payments, likes or views.

## License
MIT. UI mocks imitate third-party apps for commentary-style posts; their names and marks belong to their owners.

Made by [@jack-reson8](https://github.com/jack-reson8) · sibling skills: [pro-motion](https://github.com/jack-reson8/pro-motion), [skill-skill](https://github.com/jack-reson8/skill-skill)
