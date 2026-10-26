# 人话 renhua · make AI write Chinese like a person

English | [简体中文](https://github.com/jack-reson8/renhua/blob/main/README.zh-CN.md) | [日本語](https://github.com/jack-reson8/renhua/blob/main/README.ja.md) | [한국어](https://github.com/jack-reson8/renhua/blob/main/README.ko.md) | [Tiếng Việt](https://github.com/jack-reson8/renhua/blob/main/README.vi.md) | [हिन्दी](https://github.com/jack-reson8/renhua/blob/main/README.hi.md)

**A Claude skill that writes Xiaohongshu posts, X posts, diaries, product copy and comment replies in a real person's voice: no AI tells, a bit of internet flavor, a little humor.**

Note: the skill writes **Chinese** content (人话 means "plain human speech"). It is for people who publish in Chinese; this README is translated for everyone else.

AI-written Chinese is easy to spot: emoji checklists, parallel triplets, slogan-style uplift endings, "不是……而是……" ("not X but Y") constructions, and the stock closing question. This skill was distilled from 407 real messages typed by one indie developer (rhythm, favorite words, how they judge things). You can swap in your own voice (see below). It also ships with three reference files:

| File | What it contains |
|---|---|
| `plugins/renhua/skills/renhua/SKILL.md` | How the source developer talks, the 8 kinds of AI tells to delete, a 5-step writing flow, platform differences, AI-sounding vs human side-by-sides |
| `…/references/examples.md` | Real viral Xiaohongshu titles sorted by structure (contrast + self-deprecation / identity + challenge + deadline / "I built X, tested it" / one-line meme), in a college-student voice vs a tech-creator voice |
| `…/references/insight.md` | How to write the core insight and the punchline: topic sentence echoed at the end, result first, six shapes of closing line, insight paragraphs backed by data (taken apart from a thesis-defense draft that was approved) |
| `…/references/humor.md` | 17 internet-flavor techniques: sentence patterns of 量子位, 差评, CZ, 孙宇晨, 曾颖, 邵艾伦, levelsio, Marc Lou, 半佛仙人, 王登科 and 和菜头, each with an original example |

## Install

**Claude Code plugin (recommended)**

```bash
claude plugin marketplace add jack-reson8/renhua
claude plugin install renhua@renhua
```

**Plain skill folder**

```bash
git clone https://github.com/jack-reson8/renhua
cp -R renhua/plugins/renhua/skills/renhua ~/.claude/skills/
```

**Codex** (CLI or the ChatGPT desktop app):

```bash
codex plugin marketplace add jack-reson8/renhua
codex plugin add renhua@renhua
```

You can also copy `plugins/renhua/skills/renhua` to `~/.codex/skills/`.

**Other agents** (works with Cursor, Gemini CLI, GitHub Copilot and other agents supported by the skills CLI):

```bash
npx skills add jack-reson8/renhua
```

The skill follows the open [Agent Skills](https://agentskills.io) standard, so Claude Code, Codex and any agent that can read SKILL.md can use it.

## Use your own voice
In `SKILL.md`, replace the section 「他实际怎么说话」 ("how he actually talks") with your own patterns: export your chats with an AI, keep only the lines you typed yourself, and count your common words, sentence length, punctuation habits and the way you judge things. The rest (AI-tell removal, steps, example library, humor techniques) can be used as is.

## Related skills
[post-skill](https://github.com/jack-reson8/post-skill) for images, [pro-motion](https://github.com/jack-reson8/pro-motion) for motion videos, [skill-skill](https://github.com/jack-reson8/skill-skill) for writing skills.

MIT License
