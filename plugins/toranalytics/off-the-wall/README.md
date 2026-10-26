<p align="right">
  <strong>English</strong> | <a href="README.ko.md">한국어</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <img src="assets/hero.png" alt="Off the Wall: a pixel-art parrot on a terminal, quoting your past corrections" width="100%" />
</p>

<h1 align="center">Off the Wall</h1>

<p align="center">
  <strong>Remind your coding agent what you already corrected.</strong>
  <br/>
  <sub>A plugin for <strong>Claude Code</strong> and <strong>Codex</strong> that puts your own past corrections from the same working directory in front of the next answer.</sub>
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
  <a href="#model-selection-for-subagents">Model selection</a> ·
  <a href="#evidence">Evidence</a> ·
  <a href="#settings">Settings</a> ·
  <a href="#privacy">Privacy</a>
</p>

**Your corrections from the same working directory, quoted word for word before the agent answers. A local, model-labelled report of what you correct most. Model-selection guidance for subagents.**

Every correction you make ("stop asking, just pick one", "did you actually run the tests?") is usually forgotten by
the next session. Off the Wall keeps those messages locally and, before an answer, quotes back to the agent in your own
words up to 6 corrections recorded in the same working directory. It uses the `claude` or `codex` CLI you already run,
so it needs no separate API key. That does not mean nothing leaves your machine; see [Privacy](#privacy).

> This is the 0.2.0 unreleased safety candidate, with source published for review. It is not a stable release or a claim of live-product effectiveness. The numbers below come from one person's history with earlier versions; run the report on yours.

> Beta note: the evidence is exploratory, from one person’s text replays, not a general guarantee of fewer corrections, lower costs or better task completion. The input classifier can still mistake automated host or plugin text for a user reply, and it is not a perfect detector of human-written input. Check source messages locally before sharing aggregate report counts, because the counts are model classifications that can be wrong.

---

## Why Off the Wall?

| Problem | What happens | Off the Wall |
| :-- | :-- | :-- |
| Repeated corrections | You say "stop asking, just do it" for the tenth time this month | Your past words go in front of the next answer |
| Rules that do not stick | Corrections are summarised into neat one-line rules that change little | Your own words are quoted instead of summarised. In one small replay, distilled rules did no better than random rules ([evidence](#evidence)) |
| Every subagent on the big model | Searches and greps can run on the most expensive model | Guidance for choosing a model per subagent, and a check that sends back a subagent call with no model argument. It does not guarantee cheaper routing or cost savings |
| Another API key | Memory tools often need their own API key | Judging runs through the `claude` or `codex` CLI you already use, so no separate key. Excerpts are still processed by your provider ([privacy](#privacy)) |

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

`--seed` rereads the history you chose and stores corrections with their provenance (project hash and input origin)
where the host history records a working directory. Turns with no known working directory are not stored (the count of skipped turns is reported)
and are not promoted automatically. See [Scope and legacy records](#scope-and-legacy-records).

Requires Node 18 or newer. Historical: an earlier version was tried on macOS with Claude Code 2.1.301 and codex-cli 0.162.1. This 0.2.0 candidate has only had synthetic launcher and worker checks on macOS. It has not been run in a current live Claude Code or Codex session.

## See what you correct most

<p align="center">
  <img src="assets/report.svg" alt="Report format drawn from archived classifications of the synthetic example history: 9 of 20 candidate replies labelled as possible corrections, grouped by kind, with the quotes. Not a fresh model run" width="92%" />
</p>

`report` reads the Claude Code and Codex history already on your machine (`~/.claude/projects`,
`~/.codex/sessions`) and has a small model mark which of your replies corrected how the agent worked. It prints
the kinds you corrected most, with your own words under each. The labels are produced by a model and can be wrong. The
image above is the archived classification of [the example history](examples/claude-history) shown in the current
report format. That history is synthetic, and the image is not a fresh run of the current CLI or a new model call. It
only shows what the report looks like, not how a model or a user fares with it. About 20 turns go into one judge call;
in earlier-version testing, 100 turns took about 50 s on Codex and 65 turns about 75 s on Claude. The selected excerpts are sent to a model through your own
`claude` or `codex` CLI.

`--seed` saves what it found, so recall can start with your next prompt in that project instead of after weeks of use.

At the end it prints a link that opens a prefilled post in this repo's
[Discussions](https://github.com/toranalytics/off-the-wall/discussions/categories/show-and-tell) with your top three
kinds and their counts. Only the counts and kind names go in; none of your quoted words. The counts are model
classifications and may be wrong, so check the source messages locally and review the post yourself before you
publish anything. Nothing is posted for you.

## What the agent sees

<p align="center">
  <img src="assets/context.svg" alt="Illustration of the format of the block Off the Wall adds before the agent answers: example corrections quoted verbatim and an instruction to predict your objection. The quotes are taken from the example report, not selected for relevance" width="92%" />
</p>

| Event | Claude Code | Codex |
| :-- | :-- | :-- |
| Each prompt | up to 6 past corrections quoted, each cut at 200 characters, only from the same normalized working directory (project key) and only if they pass the match guard. Fewer than 6, or none, is normal; there is no filler from other projects or just the latest | same |
| Each prompt | the previous answer and your new message are judged in a detached process; a correction is saved with the project hash and input origin | same |
| Turn end | the end of the answer is kept for that judge | same |
| Session start | the routing rule is added | the routing rule is added |
| Subagent start | a general-purpose `Agent` call with no `model` is sent back once per turn (forks and named agent types pass) | a `spawn_agent` call with no `model` or `reasoning_effort` is sent back once per turn |

Nothing waits on a model call: the judge runs in a detached process next to your prompt, which never waits for it. The block is written in
Korean when your prompt is in Korean and in English otherwise. The current wording and selector were not part of the
earlier 39-request experiment.

The block also states that history is not permission to act, publish, delete or disclose anything, and that the
current request and safety rules take precedence.

The image above comes from `scripts/make-assets.mjs`, which calls `correctionBlock` directly on quotes from the example
report. It shows the format only. It is not a real selection by relevance, working directory or match guard.

### Scope and legacy records

- Recall needs a working directory and provenance. A prompt with no cwd, or a record with no project key, gets no
  automatic recall.
- Scope is the normalized working directory (stored as a project hash). Subdirectories, moved directories and git
  worktrees are deliberately not grouped together automatically; each is its own project.
- New records carry the project hash and the input origin. Older records without a project, or with an unknown origin,
  stay on disk but are excluded from recall. Nothing is deleted or rewritten.
- `report --seed` can reread the history you pick and tag provenance where the host history has cwd metadata. Reseeding
  only appends records with a known project and origin and reports how many unknown-cwd turns it skipped. It never
  stores new unscoped records, and there is no automatic "safe" promotion.
- The input classifier leaves out text from an explicit meta or non-human source and known automation envelopes, and
  keeps ordinary Markdown and long English text. It is a filter, not a perfect detector of human-written input.
- The match guard decides whether a stored correction is similar enough to the request to be quoted. Its current
  threshold is an initial engineering setting. It is a filter, not a calibrated accuracy figure, and no precision or
  recall is claimed for it.
- There is no memory-management UI or delete command in this iteration. To clear local records, delete files under
  `~/.otw` yourself (see [Privacy](#privacy)). With `capture: false`, new prompt and answer excerpts are not kept
  (corrections already stored are not erased). `node bin/otw.mjs status` shows how many records are scoped and
  origin-tagged and how many are quarantined.

## Model selection for subagents

<p align="center">
  <img src="assets/routing.svg" alt="One historical task, two runs per arm: $0.171 and $0.173 with the model rule, $0.300 and $0.439 without. Not an average and not a guarantee" width="92%" />
</p>

The main model acts as an orchestrator and picks the subagent's model by what the written task leaves to it. Off the Wall
only supplies this guidance and checks for a missing model argument. It does not force a model or guarantee
cheaper routing or any cost saving. The chart is one historical test; see [Evidence](#evidence).

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

All measured numbers come from one person's history, so treat them as a first, exploratory result, not a general law.
The 9-of-20 report above comes from the made-up example session. That public synthetic demo only confirms that the
context is built as described. It says nothing about model or user outcomes.

**One-person text replay, not a general finding.** 39 selected requests from one user's history were replayed as text.
Each had in fact been followed by a correction that could be judged from the text. Opus 5.5 answered each request
under each condition. A Sonnet grader (a model, not a person) compared two answers at a time, blind, and was asked twice
with the order swapped; a win needed both orders to agree. The Off the Wall condition combined 6 quotes with the
"predict the objection" line: 25 wins, 11 ties, 3 losses against nothing attached, and 17 wins, 14 ties, 8 losses
against random rules (a lean on 39 cases, not a settled result). Distilled one-line rules did not beat random ones.
This is not an independent replication. It does not show a benefit in the live product, and because quotes and the
objection-prediction line were tested together, it does not show that quoting alone causes the difference. It
does not support "quoting beats summarising" as a general statement. The 39-request trial did not use the
current selector or the updated block wording.

**Model selection.** On 30 held-out historical delegations, Opus following the three classes picked the hand-labelled
model 28 times and never a weaker one. The "do small work yourself" line was added after that measurement. The
cost chart above is one historical, model-labelled experiment: one task, 2 runs per arm, with the main model and
prices of that time. The two pairs work out to roughly 43% and 61% lower cost, but this is an indication, not an
average, and there is no current or general guarantee of cheaper subagents or any cost saving. The Codex model
mapping follows the same classes by analogy and has not been measured.

<details>
<summary><strong>The judge: how well it finds corrections</strong></summary>

- Single turn ends: on 56 hand-labelled turn ends from one user's history, Claude Haiku had precision 0.82 and recall 0.72.
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

- Earlier version, on the synthetic example history: two report runs found the same 9 corrections out of 20 replies; one of the 9 got a
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

Storage is local, but local storage does not mean nothing leaves your machine. Off the Wall keeps these in `~/.otw`:
- `corrections.jsonl`, including older records that are no longer recalled
- per-session state
- `log.jsonl`
- reporting and sharing counts, which stay on your machine until you choose to open the link and post them

What is sent out, always through your own `claude` or `codex` CLI and so to your own model provider:
- the judge sends excerpts of the assistant's answer and your reply;
- `report` sends the history excerpts it selects;
- recall puts quoted corrections into the host model's context.

There is no publisher telemetry and no separate API key. That is not the same as no provider processing: your
provider still sees these excerpts and your plan's usage or charges can apply. The default event and error logs omit raw
excerpts. With `OTW_DEBUG` set, raw excerpts can be written to `~/.otw/log.jsonl`. History frames that are unknown or too
large fail closed: project and pending state are not guessed from them. Deleting `~/.otw` forgets what Off the Wall stored, but it does not erase your Claude Code
or Codex histories or any copies kept by a provider. There is no delete command yet. Sharing is manual: the Discussions
link only prefills counts and kind names, and you review it before publishing.

## Limits

- Windows: CI covers Node 18/20/22 on Windows, Linux and macOS; see the current PR checks for results. Live Windows Claude Code/Codex sessions remain unverified. The two POSIX configured fake-provider tests are skipped on Windows.
- The judge sometimes misses (Claude Haiku: precision 0.82, recall 0.72, on one user's labels). Historically, on Codex, live
  sessions of an earlier version installed from this repository caught 2 of 2 corrections with the default judge; the earlier gpt-6-luna
  judge caught 1 of 2. That is two cases, not a rate.
- The input classifier and the match guard are filters. Some automated text can still be taken as a reply, and
  some relevant corrections can be left out.
- Scope is per exact working directory. Related folders, moved projects and worktrees do not share recall.
- Recall quotes your words to the model only. They are not shown to you during the session.
- There is no memory-management UI or delete command yet.

## Development

```bash
npm test                          # node --test, no dependencies
node scripts/make-assets.mjs      # redraws the README images from the example report and the recorded numbers
OTW_DEBUG=1 claude ...       # logs every hook event to ~/.otw/log.jsonl; may include raw excerpts
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
- [awesome-context-engineering](https://github.com/yzfly/awesome-context-engineering)
- [awesome-agent-memory](https://github.com/mnemoverse/awesome-agent-memory)

Community plugin directory: [Claude & Codex Plugins](https://claudecodexplugins.com/plugins/toranalytics/off-the-wall/off-the-wall).

## License

MIT © [Junebeom Seo](https://github.com/toranalytics)

[Privacy](https://github.com/toranalytics/off-the-wall#privacy)
