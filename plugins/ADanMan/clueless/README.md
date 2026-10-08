<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" width="180" alt="clueless">
  </picture>
</p>

<h1 align="center">clueless</h1>

<p align="center">
  <em>Tell your agent you know nothing. Watch it get careful.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/ADanMan/clueless?style=flat-square&color=111111&label=stars" alt="Stars">
  <img src="https://img.shields.io/github/v/release/ADanMan/clueless?style=flat-square&color=111111&label=release" alt="Release">
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20AGENTS.md-111111?style=flat-square" alt="Works with">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
</p>

<p align="center">
  <sub><a href="README.ru.md">Русский</a></sub>
</p>

---

You've noticed it too. Say "I don't really understand this, just do it properly for me" and the answer gets *better*. The model stops assuming you'll catch its mistakes. It starts naming the thing you didn't know to ask about. It flags the step that would have cost you your data.

That's not a fluke. It's a responsibility flip: once the model believes nobody will review its work, it becomes the reviewer.

**clueless makes the flip deliberate and always on.**

## Before / after

You ask for a signup form. You say you're not a programmer.

Without clueless, you get working code, and at the very bottom, under *"a few things worth knowing (no action needed)"*, a note that the session secret is still `change-this-to-a-random-long-string`. You copy-paste. It ships.

With clueless:

```
Do this
  1. Create .env with SESSION_SECRET=<generated below>. The server refuses to start without it.
  ...
Careful
  - users.db holds real people's emails. Back it up, never commit it, never email it.
  - No password reset yet. For a course site that is your #1 support ticket. Say so and I'll add it before launch.
Check it worked
  Sign up twice with the same email. The second attempt must say "already exists".
Decided for you
  - SQLite over Postgres: one file, zero setup, fine under a few hundred students.
  - bcrypt cost 12 over 10: slower by 300 ms, safer if the file ever leaks.
Only you can decide
  - Where this will be hosted (assumed Render; the steps differ for a VPS).
```

Same model. Same prompt. More survivors in [examples/](examples/).

## What it actually does

Before every answer, the agent asks itself four things it normally skips when it thinks you'll review the result:

1. **What would an expert have asked that this user didn't?** Then it answers those, with safe defaults, inside the deliverable.
2. **What here is irreversible or expensive?** Data loss, money, security, legal, locked-out customers, deadlines. Those go at the top, in plain words, never in a trailing note.
3. **What did I just decide on their behalf?** Every tool, provider, rate, or default it picked gets named, with the alternative and a one-line why.
4. **How will they know it worked?** It verifies itself if it can. If only you can, it gives you one check that fails visibly.

Then it delivers in a fixed shape: **Do this → Careful → Check it worked → Decided for you → Only you can decide.** The last block is capped at three items, each pre-filled with the assumption it made, so silence is a valid answer.

It is not "explain more". It is *be the only adult in the room*.

## Numbers

Three "I know nothing, do it for me" prompts (home backups, first-year freelancer taxes, signup form for a non-programmer), three runs each, same model, with and without the skill. Each answer graded against a fixed list of what a domain expert would insist on. A point only counts if the answer says it clearly and actionably, not if it's buried under "context, no action needed".

| | baseline | clueless |
|---|:-:|:-:|
| Expert-level points stated clearly | 12 / 63 | **47 / 63** |
| Present but buried | 13 / 63 | 4 / 63 |
| Absent | 38 / 63 | 12 / 63 |

| Prompt | baseline, per run | clueless, per run |
|---|:-:|:-:|
| home backups | 3, 3, 2 of 7 | 7, 6, 6 of 7 |
| first-year freelancer taxes | 2, 1, 1 of 7 | 4, 4, 4 of 7 |
| signup form, non-programmer | 0, 0, 0 of 7 | 5, 5, 6 of 7 |

n=3 per prompt per arm, one model, graded by a separate model against a fixed checklist. Small, but the runs agree with each other. What it still misses every time: password reset for the course site, W-9/1099 paperwork, the first-year tax safe-harbor rule. Full method, checklists, all 18 verbatim answers and the grades: [benchmarks/](benchmarks/).

The baseline answers were competent. What they lacked was the shape: caveats at the bottom, decisions unnamed, no way to verify.

## Install

### Claude Code

```
/plugin marketplace add ADanMan/clueless
```
```
/plugin install clueless@clueless
```

Two separate prompts. Same in the Claude Code desktop app's Code tab.

### Codex

```bash
codex plugin marketplace add ADanMan/clueless
codex plugin add clueless@clueless
```

### Cursor

Copy [`.cursor/rules/clueless.mdc`](.cursor/rules/clueless.mdc) into your project's `.cursor/rules/`. It is `alwaysApply`.

### Anything that reads `AGENTS.md`

OpenCode, Jules, Amp, CodeWhale, Qoder, Swival and friends pick up [`AGENTS.md`](AGENTS.md) from the repo root. Copy it into your project, or run from a checkout.

### Uninstall

`/plugin remove clueless` (Claude Code), `codex plugin remove clueless` (Codex), or delete the copied rule file. Nothing is written outside the plugin folder.

## Commands

| Command | What it does |
|---------|--------------|
| `/clueless [lite \| full \| ultra \| off]` | Set how much responsibility the agent takes. No argument reports the current level. |
| `/clueless-blindspots` | One-shot: what you're not seeing in the plan, code or document in front of you. Tagged list, highest stakes first. |
| `/clueless-help` | Quick reference. |

| Level | What changes |
|-------|--------------|
| **lite** | Deliver as usual, then add only *Decided for you* and *Only you can decide*. |
| **full** | The whole contract. Default. |
| **ultra** | Also challenges the task itself in the first line, the way a professional would: "You asked for X; people in your position usually need Y." |

## FAQ

**Isn't this just "explain like I'm five"?**
No. ELI5 changes the vocabulary. clueless changes who is responsible. The answer can be terse; what it can't be is unreviewed.

**Can I use it with [ponytail](https://github.com/DietrichGebert/ponytail)?**
Yes. ponytail governs how much the agent builds; clueless governs how much it takes responsibility for. Lazy code, carefully handed over.

**Does it make the agent ask more questions?**
The opposite. Questions you can't answer are decisions the agent dodged. It decides, states the default, and lists at most three things only you can settle, each with its assumption filled in.

**What if I actually am an expert?**
Then don't say you're clueless. The skill also backs off on its own the moment you start reviewing its output line by line.

**Why "clueless"?**
Because that's what you typed, and it worked.

## Calibration hook

Claude Code loads the bundled `UserPromptSubmit` hook automatically. It asks the
model to assess review ability for the current domain using the pattern catalog:
explicit inability, delegated choices, mixed expertise, ambiguous wording,
learning, and quoted/negated signals. It never selects a mode in code, stores
prompts, calls another model, or grants permissions. Node.js is required for the
hook; other adapters use the skill rules without the hook.

Disable the reminder with `CLUELESS_CALIBRATION=off` in the environment before
starting Claude Code. Explicit clueless off/level commands take priority even
while the reminder runs. The hook's context uses additional tokens each turn.

The existing benchmark numbers describe the earlier skill versions, not this
calibration hook. Runtime tests cover its input/output and failure behaviour;
classification accuracy and long-session benefits are not yet measured.

## Development

```bash
npm test
```

The compact ruleset lives in [`AGENTS.md`](AGENTS.md). The Cursor rule is a copy; `scripts/check-rule-copies.js` fails the test suite if they drift. The Claude Code and Codex plugins load the full skills from [`skills/`](skills/).

## License

[MIT](LICENSE).

## Star History

<a href="https://www.star-history.com/#ADanMan/clueless&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=ADanMan/clueless&type=Date&theme=dark" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=ADanMan/clueless&type=Date" />
 </picture>
</a>
