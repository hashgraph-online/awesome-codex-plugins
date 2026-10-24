<p align="right">
  <strong>English</strong> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <img src="assets/hero.png" alt="Off the Wall: a pixel-art parrot on a terminal, quoting your past corrections" width="100%" />
</p>

<h1 align="center">Off the Wall</h1>

<p align="center">
  <strong>Stop telling your coding agent the same thing twice.</strong>
  <br/>
  <sub>A plugin for <strong>Claude Code</strong> and <strong>Codex</strong> that puts your own past corrections in front of the next answer.</sub>
</p>

<p align="center">
  <a href="https://github.com/toranalytics/off-the-wall/actions/workflows/ci.yml"><img alt="tests" src="https://img.shields.io/github/actions/workflow/status/toranalytics/off-the-wall/ci.yml?branch=main&label=tests&style=flat-square"></a>
  <a href="https://github.com/toranalytics/off-the-wall/releases"><img alt="release" src="https://img.shields.io/github/v/release/toranalytics/off-the-wall?style=flat-square"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-green?style=flat-square"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-d97757?style=flat-square">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-10a37f?style=flat-square">
  <img alt="no dependencies" src="https://img.shields.io/badge/dependencies-0-blue?style=flat-square">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#why-off-the-wall">Why</a> ·
  <a href="#see-what-you-correct-most">Your report</a> ·
  <a href="#what-the-agent-sees">How it works</a> ·
  <a href="#cheaper-subagents">Routing</a> ·
  <a href="#evidence">Evidence</a> ·
  <a href="#settings">Settings</a> ·
  <a href="#privacy">Privacy</a>
</p>

**Your corrections, quoted word for word before the agent answers. A one-minute report of what you correct most. Subagents on cheaper models.**

Every correction you make ("stop asking, just pick one", "did you actually run the tests?") is usually forgotten by
the next session. Off the Wall keeps those messages and quotes the most relevant ones back to the agent, in your own
words, before each answer. It runs on the Claude or ChatGPT plan you already pay for and needs no API key.

> Off the Wall is new (0.1). The numbers below come from one person's history; run the report on yours.

> Beta note: the evidence is exploratory, from one person’s text replays, not a general guarantee of fewer corrections, lower costs or better task completion. Automated host or plugin notices can be mistaken for user replies. Check source messages locally before sharing aggregate report counts.

---

## Why Off the Wall?

| Problem | What happens | Off the Wall |
| :-- | :-- | :-- |
| Repeated corrections | You say "stop asking, just do it" for the tenth time this month | Your past words go in front of the next answer |
| Rules that do not stick | Corrections are summarised into neat one-line rules that change little | Quotes, not summaries. Summaries did no better than random rules ([evidence](#evidence)) |
| Every subagent on the big model | Searches and greps run on the most expensive model | The orchestrator names a model for each subagent; 43–61% cheaper in our test |
| Another bill | Memory tools often need an API key | Judging runs through the `claude` or `codex` CLI you already use |

## Quick Start

**1. Install**

Claude Code, at the prompt:

```
/plugin install off-the-wall --marketplace toranalytics/off-the-wall
```

Codex:

```bash
codex plugin marketplace add toranalytics/off-the-wall
codex plugin add off-the-wall@off-the-wall
```

Then open `/hooks` in Codex once and trust the Off the Wall hooks. Codex skips plugin hooks until they are trusted.

**2. Try the report on the example history** (no history of your own needed)

```bash
git clone https://github.com/toranalytics/off-the-wall && cd off-the-wall
node bin/otw.mjs report --host claude --claude-dir examples/claude-history --days 0
```

**3. Run it on your own history and start recall from it**

```bash
node bin/otw.mjs report --seed
```

Requires Node 18 or newer. Tested on macOS with Claude Code 2.1.301 and codex-cli 0.162.1.

## See what you correct most

<p align="center">
  <img src="assets/report.svg" alt="Off the Wall report output: 9 of 20 replies were corrections, grouped by kind, with the quotes" width="92%" />
</p>

`report` reads the Claude Code and Codex history already on your machine (`~/.claude/projects`,
`~/.codex/sessions`) and has a small model mark which of your replies corrected how the agent worked. It prints
the kinds you corrected most, with your own words under each. The image above is the real output on
[the example history](examples/claude-history). About 20 turns go into one judge call; in testing, 100 turns
took about 50 s on Codex and 65 turns about 75 s on Claude.

`--seed` saves what it found, so recall starts with your next prompt instead of after weeks of use.

At the end it prints a link that opens a prefilled post in this repo's
[Discussions](https://github.com/toranalytics/off-the-wall/discussions/categories/show-and-tell) with your top three
kinds and their counts. Only the counts and kind names go in; none of your quoted words. Posting it is up to you, and
it is the quickest way to tell me whether your #1 matches mine.

## What the agent sees

<p align="center">
  <img src="assets/context.svg" alt="The block Off the Wall adds before the agent answers: six of your past corrections, verbatim, and an instruction to predict your objection" width="92%" />
</p>

| Event | Claude Code | Codex |
| :-- | :-- | :-- |
| Each prompt | up to 6 past corrections quoted, each cut at 200 characters: the 3 most like the request, then the latest | same |
| Each prompt | the previous answer and your new message are judged in a detached process; a correction is saved | same |
| Turn end | the end of the answer is kept for that judge | same |
| Session start | the routing rule is added | the routing rule is added |
| Subagent start | a general-purpose `Agent` call with no `model` is sent back once per turn (forks and named agent types pass) | a `spawn_agent` call with no `model` or `reasoning_effort` is sent back once per turn |

Nothing waits on a model call: the judge runs in a detached process next to your prompt, which never waits for it. The block is written in
Korean when your prompt is in Korean (the wording that was measured) and in English otherwise.

## Cheaper subagents

<p align="center">
  <img src="assets/routing.svg" alt="Cost of the same delegation: $0.171 and $0.173 with routing, $0.300 and $0.439 without" width="92%" />
</p>

The main model acts as an orchestrator and picks the subagent's model by what the written task leaves to it.

| Class | When | Claude Code | Codex |
| :-- | :-- | :-- | :-- |
| small | retrieval or reshaping: find, grep, list, extract, convert | `haiku` | the fast model on your account, `reasoning_effort: low` |
| mid | a stated goal and criteria: investigate, review, implement, test | `sonnet` | the workhorse model, `medium` |
| large | the subagent decides what the problem is: root cause, design, migration | `opus` | the frontier model, `high` |

Work that takes only a few steps is cheapest done by the main model itself. Codex model names differ by account,
so Off the Wall reads the list Codex keeps for you (`~/.codex/models_cache.json`) and sorts it into the three classes
by each model's description. For Codex, the rule also says to pass `fork_turns: "none"` when the subagent does not
need the conversation. Otherwise the whole history is copied into it, and on a different model none of it is
cached.

## Evidence

<p align="center">
  <img src="assets/evidence.svg" alt="Wins, ties and losses against nothing attached: actual correction 36/3/0, Off the Wall 25/11/3, random rules 18/15/6, distilled rules 14/17/8" width="92%" />
</p>

All measured numbers come from one person's real history, so treat them as a first result, not a general law. The
9-of-20 report above comes from the made-up example session.

**Quoting beats summarising.** 39 real requests were replayed. In reality, each was followed by a correction that
can be judged from the text. Opus 5.5 answered each request under each condition. A Sonnet grader compared two
answers at a time, blind, and was asked twice with the order swapped; a win needed both orders to agree. Quotes
with the "predict the objection" line: 25 wins, 11 ties, 3 losses against nothing attached (p < 0.001), and 17 wins,
14 ties, 8 losses against random rules (p = 0.11 on 39 cases: a lean, not yet a settled result). The distilled rules
did not beat the random ones.

**Routing.** On 30 held-out real delegations, Opus following the three classes picked the hand-labelled model 28
times and never a weaker one. The "do small work yourself" line was added after that measurement. The cost
comparison above is one task with 2 runs per arm: an indication, not an average. The Codex model mapping follows
the same classes by analogy and has not been measured.

<details>
<summary><strong>The judge: how well it finds corrections</strong></summary>

- Single turn ends: on 56 hand-labelled turn ends, Claude Haiku had precision 0.82 and recall 0.72.
- Batch judge used by `report`: compared with the single judge on 100 turn ends (50 corrections, 50 not), two
  runs per model. The judge model mattered and the batch size did not, so the defaults are Haiku and the Codex
  workhorse model.

| judge (pairs per call) | agrees with single judge | overlap of two runs |
| :-- | --: | --: |
| Claude Haiku (20) | 84, 90 | 0.83 |
| Claude Sonnet (20) | 81, 71 | 0.60 |
| gpt-6.1-sol (20) | 88, 88 | 0.92 |
| gpt-6-luna (20) | 61, 56 | 0.38 |
| gpt-6-luna (5) | 64, 66 | 0.39 |

- On the example history, two report runs found the same 9 corrections out of 20 replies; one of the 9 got a
  different category.

</details>

## Settings

`~/.otw/config.json`, every key optional. What you set here wins over what is detected:

```json
{
  "recall": true,
  "capture": true,
  "routing": true,
  "judge": { "claude": "haiku", "codex": "gpt-6.1-sol" },
  "models": {
    "claude": { "small": "haiku", "mid": "sonnet", "large": "opus" },
    "codex": { "small": "gpt-6-luna", "mid": "gpt-6.1-sol", "large": "gpt-6-astra" }
  }
}
```

`node bin/otw.mjs status` shows what is stored.

## Privacy

Everything stays in `~/.otw` on your machine:
- `corrections.jsonl`
- per-session state
- `log.jsonl`

The only thing that leaves is the judge's call, which goes through your own `claude` or `codex` CLI. Delete
`~/.otw` to forget everything.

## Limits

- Windows: tests and a hook smoke run pass in CI (Node 18–22), but no live Claude Code or Codex session has been run on Windows.
- The judge sometimes misses (Claude Haiku: precision 0.82, recall 0.72). On Codex, live sessions installed from this
  repository caught 2 of 2 corrections with the default judge; the earlier gpt-6-luna judge caught 1 of 2.
- Recall quotes your words to the model only. They are not shown to you during the session.

## Development

```bash
npm test                          # node --test, no dependencies
node scripts/make-assets.mjs      # redraws the README images from real outputs and the measured numbers
OTW_DEBUG=1 claude ...       # logs every hook event to ~/.otw/log.jsonl
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are listed in [CHANGELOG.md](CHANGELOG.md).

## Listed in

- [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins)
- [awesome-ai-plugins](https://github.com/hashgraph-online/awesome-ai-plugins)
- [awesome-ai-agent-tools](https://github.com/michielhdoteth/awesome-ai-agent-tools)
- [Awesome-Vibe-Coding](https://github.com/0xWelt/Awesome-Vibe-Coding)
- [awesome-vibe-coding-resources](https://github.com/acvnace/awesome-vibe-coding-resources)
- [awesome-coding-agents](https://github.com/kailiu42/awesome-coding-agents)
- [awesome-agent-memory](https://github.com/mnemoverse/awesome-agent-memory)

Community plugin directory: [Claude & Codex Plugins](https://claudecodexplugins.com/plugins/toranalytics/off-the-wall/off-the-wall).

## License

MIT © [Junebeom Seo](https://github.com/toranalytics)

[Privacy](https://github.com/toranalytics/off-the-wall#privacy)
