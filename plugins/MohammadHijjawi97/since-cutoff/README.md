<p align="center"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/logo-dark.svg">
  <img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/logo.svg" width="72" height="72" alt="since-cutoff logo">
</picture></p>

<h1 align="center">since-cutoff</h1>

<!-- mcp-name: io.github.MohammadHijjawi97/since-cutoff -->

**Your coding assistant's training data stops before your dependencies' latest releases, so it
can write calls your pinned versions no longer accept. since-cutoff shows where your code uses an
API that changed after the model's training cutoff, and writes the short notes your assistant
needs to avoid the old form.**

The [sample project](https://github.com/MohammadHijjawi97/since-cutoff/tree/main/examples/agent-app)
calls `client.messages.create` and pins anthropic 1.8.0. The latest anthropic release at Claude
Sonnet 4.5's training cutoff was 0.60.0, whose `create` still took `temperature`; 1.8.0 raises
`TypeError` for it. What `scan` prints, trimmed to the anthropic part:

```console
$ uvx since-cutoff scan --model anthropic:claude-sonnet-4-5
Your code uses 2 APIs that changed after claude-sonnet-4-5's training cutoff (2025-07-31)

huggingface-hub 0.34.3 -> 2.0.0 (0.34.3 was the latest release at the cutoff; pyproject.toml pins
  2.0.0)
  ...

anthropic 0.60.0 -> 1.8.0 (0.60.0 was the latest release at the cutoff; pyproject.toml pins 1.8.0)
  Messages.create: temperature, top_k and top_p were removed                          uses this API
    app/main.py   calls create
    Note: `Messages.create()` no longer accepts `temperature`, `top_k` or `top_p` as keyword
          arguments. If the API still needs them, pass them through its `extra_body` or
          `extra_query` argument. since-cutoff found no replacement in anthropic's deprecation
          text. [diff]

2 notes ready: `since-cutoff sync` writes them to AGENTS.md and keeps them in step with
  pyproject.toml.
```

The call in `app/main.py` passes none of these parameters, so it is marked "uses this API", not
"old form": it works today, but an assistant writing for 0.60.0 could add `temperature=0.2` when
it edits the call. The note is what `since-cutoff sync` writes into AGENTS.md so that it does
not; its tag, `[diff]`, says what the note rests on: a static comparison of the two releases'
public APIs. The parameters left the signature, which is not the same as the API dropping the
field, so where the pinned method has an `extra_body` or `extra_query` argument the note says
so instead of telling the assistant to drop the field.

**Try it on your project.** No API key, no model call. In the project root:

```bash
uvx since-cutoff scan
```

It detects your coding model (or pass `--model`), reads your lockfile, takes each dependency's
latest release on or before the model's training cutoff, and compares that release's public API
with the version you pin, statically: no package code runs. The cutoff only chooses which changes
to look at; it says nothing about what the model memorised. Whether your model really gets them
wrong, and whether the notes help, is what
[`since-cutoff run`](https://github.com/MohammadHijjawi97/since-cutoff#measure-your-model)
measures; it calls your model and is optional.

[![PyPI](https://img.shields.io/pypi/v/since-cutoff)](https://pypi.org/project/since-cutoff/)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
[![CI](https://github.com/MohammadHijjawi97/since-cutoff/actions/workflows/ci.yml/badge.svg)](https://github.com/MohammadHijjawi97/since-cutoff/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/LICENSE)
![Status: beta](https://img.shields.io/badge/status-beta-orange)
[![since-cutoff MCP server on Glama](https://glama.ai/mcp/servers/MohammadHijjawi97/since-cutoff/badges/score.svg)](https://glama.ai/mcp/servers/MohammadHijjawi97/since-cutoff)

<p align="center"><a href="https://github.com/MohammadHijjawi97/since-cutoff/releases/download/v0.5.0/since-cutoff-explainer.mp4"><img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/explainer-thumbnail.png" width="560" alt="Watch the 2½-minute explainer (video with voice-over)"></a><br><a href="https://github.com/MohammadHijjawi97/since-cutoff/releases/download/v0.5.0/since-cutoff-explainer.mp4">▶ Watch the 2½-minute explainer (video with voice-over)</a></p>

**English** | [简体中文](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/README.zh-CN.md) | [Español](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/README.es.md) | [Français](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/README.fr.md)

## The problem

Every model has a training cutoff; your lockfile keeps moving. When a library changes its public
API after the cutoff, a model whose training data predates the change can keep writing the old
calls. Some of that code fails at import or call time. Some still runs, because the old form is
only deprecated, or still accepted with a warning.

A few of the changes `since-cutoff scan` finds for Claude Sonnet 4.5 (training cutoff July
2025) in the [sample project](https://github.com/MohammadHijjawi97/since-cutoff/tree/main/examples/agent-app),
which pins six of its nine dependencies to current releases (for the other three, which are
unpinned, the tool uses the latest release):

| library | release at the cutoff | pinned | what changed |
|---|---|---|---|
| anthropic | 0.60.0 | 1.8.0 | `messages.create(temperature=..., top_p=..., top_k=...)` is no longer accepted |
| huggingface-hub | 0.34.3 | 2.0.0 | `hf_hub_download(resume_download=..., force_filename=..., local_dir_use_symlinks=...)` left the signature in 1.0 (2.0.0 still accepts them at run time, ignores them and warns) |
| langchain-core | 0.3.72 | 1.6.5 | `retriever.get_relevant_documents()` and `llm.predict()` removed |
| openai | 1.98.0 | 3.19.2 | 21 breaking changes, 6 new deprecations |

In that project, 7 of 9 dependencies changed their public API after the cutoff. The static diff
flags 310 breaking changes and 23 new deprecations; the project's code uses 2 of the changed
APIs.

It is not one model or one vendor. Across 36 widely used Python AI libraries and 21 models from
OpenAI, Anthropic, Google, xAI, DeepSeek, Qwen, Moonshot and Mistral, even the newest model
tested (Claude Opus 5.5, June 2026 cutoff) predates a public API break in 20 of the 36
([full results](https://mohammadhijjawi97.github.io/since-cutoff/ai-stack.html)):

<p align="center"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/ai-stack-dark.svg">
  <img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/ai-stack.svg" width="860" alt="Bar chart: for each of 21 models from 8 vendors, how many of 36 Python AI libraries broke their public API and how many are on a new major version since the model's training cutoff. From 21 of 36 for GPT-4o (13 of the libraries did not exist yet) to 33 of 36 for models with early-2025 cutoffs, and 20 of 36 for Claude Opus 5.5 (June 2026).">
</picture></p>

since-cutoff does three things about it:

1. **`scan`** finds, for each dependency, the newest release on or before the model's cutoff,
   diffs its public API against the version you pin, and shows which of the changed APIs your
   code uses, where, and a note for each. No model calls, no API key.
2. **`sync`** writes those notes into a marked block in AGENTS.md (or CLAUDE.md) after showing
   you the diff, and keeps them in step with your lockfile; `sync --check` and `status` tell CI,
   pre-commit and your agent when they fall behind. Each note is stated from the API diff and
   tagged with what was checked. No model calls.
3. **`run`**, optional, asks the model short coding tasks that need the changed APIs, with no
   tools and no docs, and scores each answer with a type checker against *both* versions:
   stale, wrong, deprecated or correct. No LLM judges anything. For each failure it writes a
   note, keeps a model-written note only if its example type-checks against your version, and
   re-tests the model on held-out tasks without and with the notes.

The same diff is available to agents through an [MCP server](https://github.com/MohammadHijjawi97/since-cutoff#use-it-from-any-agent-mcp)
and to CI through a [GitHub Action and pre-commit hooks](https://github.com/MohammadHijjawi97/since-cutoff#use-in-ci).

## Quick start

```bash
# the changed APIs your code uses, with a note for each (no model calls, no API key)
uvx since-cutoff scan

# write those notes into AGENTS.md (shows the diff and asks first); run it again after upgrades
uvx since-cutoff sync

# optional: measure which of the changes your model gets wrong, and test the notes (calls it)
uvx since-cutoff run
```

Or install it with `pipx install since-cutoff` (or `pip install since-cutoff`) and run
`since-cutoff`. Run it from your project root: it reads `uv.lock`, `poetry.lock`, `pdm.lock`,
`pylock.toml`, `Pipfile.lock`, `requirements*.txt`, `pyproject.toml`, `Pipfile` or a `.venv`
(not `setup.py` or `setup.cfg`). Without `--model` it uses the model your coding agent is set
up with, from the Claude Code, Codex, Gemini CLI, OpenCode or Aider settings; for any other
model, pass `--model` (see [Choosing the model](https://github.com/MohammadHijjawi97/since-cutoff#choosing-the-model)).
`scan`, `sync` and `status` call no model and need no API key; `run` sends prompts to the model
provider and uses your API credits or Claude Code usage.

What `scan` prints for the sample project:

<p align="center"><img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/scan.svg" width="100%" alt="since-cutoff scan --model anthropic:claude-sonnet-4-5 on the sample project. Your code uses 2 APIs that changed after claude-sonnet-4-5's training cutoff (2025-07-31). huggingface-hub 0.34.3 -> 2.0.0: hf_hub_download, used in app/main.py, no longer has force_filename, local_dir_use_symlinks, resume_download and proxies in its signature; its note is tagged [diff], and a Runtime line says that 2.0.0's source still handles them, so calls passing them may run with a warning. anthropic 0.60.0 -> 1.8.0: Messages.create, called in app/main.py, no longer accepts temperature, top_k and top_p; its note is tagged [diff]. 2 notes ready for AGENTS.md; what uses this API and [diff] mean; 323 more changes in 7 packages that the code does not use."></p>

Both APIs are "uses this API"; a file that passed `resume_download=True` or `temperature=0.2`
would make them "old form". `scan -v` lists every file that uses an API (3 are shown), and
`scan --all` adds every other change, package by package. `scan --json` and
`.since-cutoff/results.json` have the same in `used_apis` (each API, where it is used, its
changes and its note, with the note's tags, the versions it applies to and what was checked),
and `.since-cutoff/report.md` starts with "Used by your code".

### Keep the notes current: sync and status

`since-cutoff sync` (0.4.0 and later) writes the notes that `scan` shows into a marked block: in
AGENTS.md, or in CLAUDE.md when only that file exists, and where a block already is, into that
one (`--target` names another file). It prints a unified diff and asks
`Write this to AGENTS.md? [y/N]`; `--yes` writes without asking, and with no terminal to ask in
it writes nothing. Text outside the block keeps its bytes, CRLF line breaks included, and
`since-cutoff unapply` removes the block. For the sample project, the block ends with:

```markdown
**anthropic 1.8.0** (0.60.0 at the cutoff)
- `Messages.create()` no longer accepts `temperature`, `top_k` or `top_p` as keyword arguments. If the API still needs them, pass them through its `extra_body` or `extra_query` argument. since-cutoff found no replacement in anthropic's deprecation text. [diff]

**huggingface-hub 2.0.0** (0.34.3 at the cutoff)
- `huggingface_hub.hf_hub_download()` no longer accepts `proxies`, `force_filename`, `local_dir_use_symlinks` or `resume_download`; do not pass them. huggingface-hub's deprecation text says there is no replacement for `force_filename`, `local_dir_use_symlinks` or `resume_download`. since-cutoff found no replacement for `proxies` in huggingface-hub's deprecation text. [diff]
<!-- since-cutoff:end -->
```

Above the bullets are the start marker, a meta line (the model, its cutoff, where the versions
come from, a hash of the dependencies and a hash of the block's own text, so that a hand edit
shows) and a header that names the model, the cutoff and the file the versions come from, says
what the tags mean and that no library code was run. The Runtime caveat stays out of the block:
the advice ("do not pass them") is the same either way.

Run `sync` again after you change the lockfile or the code. It adds notes for APIs your code
starts using, checks a bumped package again, and drops a package's notes when it is no longer a
dependency, is no newer than the release at the cutoff, or its changed APIs are no longer used,
and says why. It keeps the model and cutoff the block was written for (so that teammates whose
agents use other models do not rewrite it back and forth) unless you pass `--model` or
`--cutoff`; `--model a,b` uses the earliest of their cutoffs. When nothing changed it writes
nothing, and the file keeps its bytes and modification time.

| command | what it does | exit code |
|---|---|---|
| `since-cutoff sync` | shows the diff, asks, writes | 0 written or up to date; 3 not written (you said no, or there is no terminal to ask in) |
| `since-cutoff sync --yes` | writes without asking | 0 |
| `since-cutoff sync --dry-run` | shows the diff, writes nothing | 0 |
| `since-cutoff sync --check` | writes nothing (for CI and pre-commit) | 0 up to date; 3 out of date |
| `since-cutoff sync --json --yes` | writes without asking; prints JSON proposals and write results | same as `sync --yes` |
| `since-cutoff sync --json --check` | prints JSON proposals; writes nothing | 0 up to date; 3 out of date |
| `since-cutoff sync --json --dry-run` | prints JSON proposals; writes nothing | 0 |
| `since-cutoff status` | compares the block with the lockfile, offline | 0 current, or no block; 3 out of date; 1 broken markers |

When the block was edited by hand, `sync` and `sync --check` show the diff, write nothing and
exit with code 4; `sync --force` replaces it. When a package the notes are about cannot be
checked (PyPI unreachable), `sync` writes nothing and exits with code 1.

`sync --json` requires `--yes`, `--check` or `--dry-run`; without one it exits with code 2
without prompting. Stdout contains only JSON (and stays empty for usage errors); progress,
diffs and errors go to stderr. The object contains `exit_code` and `targets`. Each target
reports `target`, `action`, `changed`, `edited`, `written`, `model`, `cutoff`, `scope`,
`notes`, `changes` (each package's `package`, `done` and `state`), `retest` and `diff_lines`.
`written` distinguishes an applied proposal from a preview or a refused hand edit. The usual
exit codes and `--force` behavior still apply.

`since-cutoff status` reads no network and no code: per package, the version the notes are for
and the version the lockfile has, whether other dependencies changed, and whether the model
your coding agent is set up with has an earlier training cutoff than the notes (with the
`sync --model` command for it). `status --json` is for scripts. `status --hook` prints one line
only when the notes are out of date and always exits with 0, for example:

```text
since-cutoff: the library notes in AGENTS.md are out of date: anthropic 1.8.0 in the notes, 0.60.0 in pyproject.toml. `since-cutoff sync` updates them.
```

More options:

- `sync --scope imported` also notes the changes most likely to matter in each changed package
  your code imports (up to 5 APIs per package), for code that uses none of the changed APIs yet.
  `scan` suggests it when that is the case.
- `sync --suggestions` adds the names in the pinned version that merely look similar to what was
  removed, tagged `[not confirmed]`. The block records both choices, and later syncs keep them.
- Notes that `since-cutoff run --apply` wrote are tagged `[type-checked]`. `sync` keeps each one,
  in place of the note from the diff for the same API, while its package keeps the same version
  and your code still uses that API.

Claude Code reads CLAUDE.md, and reads AGENTS.md only when there is no CLAUDE.md or when
CLAUDE.md imports it with a line `@AGENTS.md`
([memory docs](https://code.claude.com/docs/en/memory)). When the notes go to AGENTS.md and
CLAUDE.md does not import it, `scan` and `sync` say so. Writing to both files is
[#13](https://github.com/MohammadHijjawi97/since-cutoff/issues/13).

### Measure your model

`since-cutoff run` is the optional step that calls a model. It asks the model short tasks that
need the changed APIs, with no tools, no docs and none of your code; scores the answers with a
type checker against both versions; writes a note for each failure; and tests the notes on
held-out tasks ([How it works](https://github.com/MohammadHijjawi97/since-cutoff#how-it-works)).
It uses your API credits or Claude Code usage and can take 5-20 minutes.

```bash
since-cutoff run --quick    # a smaller run: 12 probes, 1 held-out task, 3 regression checks
since-cutoff run --apply    # write this run's notes into the block
```

Without `--apply` the notes are shown, not written. `run --apply` replaces the block with that
run's notes; a later `since-cutoff sync` adds the notes from the diff for the other changed APIs
your code uses, and keeps the run's `[type-checked]` notes while their package's version stays
the same.

### In Claude Code

```text
/plugin marketplace add MohammadHijjawi97/since-cutoff
/plugin install since-cutoff@since-cutoff
```

Then ask Claude to "check which of our dependencies you are out of date on", or run
`/since-cutoff:since-cutoff`. The skill runs `since-cutoff scan` and offers the notes: it runs
`since-cutoff sync --dry-run`, shows you the diff and writes only when you agree. When you ask
it to measure the model, the measuring is done by a fresh, tool-less copy of the model, so the
agent cannot grade itself. The plugin also starts the
[MCP server](https://github.com/MohammadHijjawi97/since-cutoff#use-it-from-any-agent-mcp), so
Claude can look up a library's changes before it writes code, and (0.4.0 and later) runs
`since-cutoff status --hook` when a session starts, which adds one line to the session when the
notes are out of date (the first time, uvx downloads since-cutoff).

### In other coding agents

```bash
npx skills add MohammadHijjawi97/since-cutoff
```

This installs the same skill through the open [skills](https://github.com/vercel-labs/skills)
CLI for Codex, Cursor, Gemini CLI, GitHub Copilot, OpenCode and other agents that read
`SKILL.md`. since-cutoff reads the model from the Codex, Gemini CLI, OpenCode and Aider settings
too; for other agents, tell it which model to use, for example
`since-cutoff scan --model openai:gpt-5.4`.
Add the MCP server as shown below.

Prompts that work well:

- "Which APIs that our code uses changed after your training cutoff?" The agent runs
  `since-cutoff scan` or calls the MCP tool `project_changes`.
- "Add notes about them to AGENTS.md." The agent runs `since-cutoff sync --dry-run`, shows you
  the diff, and runs `since-cutoff sync --yes` when you agree.
- "Measure which of those changes you actually get wrong." The agent asks you first, then runs
  `since-cutoff run --quick`.
- "Before you write the httpx code, check what changed in httpx since your cutoff." The agent
  calls the MCP tool `api_changes`.

### Choosing the model

| `--model` | uses | needs |
|---|---|---|
| `claude-code` (default when no setting names a model) | your Claude Code login (subscription or key), current model | the `claude` CLI |
| `claude-code:sonnet`, `claude-code:claude-haiku-4-5` | a specific Claude model | the `claude` CLI |
| `anthropic:<model>` | Anthropic API | `ANTHROPIC_API_KEY` |
| `openai:<model>` | OpenAI API | `OPENAI_API_KEY` |
| `openrouter:<vendor/model>` | OpenRouter | `OPENROUTER_API_KEY` |
| `deepseek:<model>` | DeepSeek API | `DEEPSEEK_API_KEY` |
| `ollama:<model>` | local Ollama | Ollama running |
| `openai-compatible:<model>` | any OpenAI-compatible server | `--base-url`, optional `OPENAI_API_KEY` |

The "needs" column is for `run`, which calls the model; `scan` and `sync` use only its training
cutoff. Without `--model`, since-cutoff 0.3.0 and later use the model your coding agent is set up
with, and the model line says where it came from ("model from .claude/settings.json"):

1. `SINCE_CUTOFF_MODEL` (a full spec such as `openai:gpt-5.4`) always wins.
2. Inside Claude Code (which sets `CLAUDECODE=1` for the commands it runs), only Claude Code's
   settings count: `ANTHROPIC_MODEL`, then the project's `.claude/settings.local.json` and
   `.claude/settings.json`, then `~/.claude/settings.json`.
3. Elsewhere the most specific setting wins: first `ANTHROPIC_MODEL`, `GEMINI_MODEL` or
   `AIDER_MODEL`, then the project settings, nearest folder first, from the scanned folder up to
   the repository root (never the home folder), then the user settings. In one folder the agents
   count in this order:

| agent | project settings | user settings |
|---|---|---|
| Claude Code | `.claude/settings.local.json`, `.claude/settings.json` | `~/.claude/settings.json` |
| Codex | `.codex/config.toml`, with its selected profile | `$CODEX_HOME/config.toml` or `~/.codex/config.toml` |
| Gemini CLI | `.gemini/settings.json` | `~/.gemini/settings.json` |
| OpenCode | `opencode.json`, `opencode.jsonc` | `~/.config/opencode/` |
| Aider | `.aider.conf.yml`, with Aider's aliases (`4o`, `flash`, `r1`, ...) | `~/.aider.conf.yml` |

When no setting names a model, it uses Claude Code's default model and says so. Only the model
fields are read, and a model name it cannot place stops the run with a message naming the
setting. A model that an agent reaches through another service (GitHub Copilot, Amazon Bedrock,
Vertex AI) is named after its maker, so `run` calls the maker's API (`openai:` needs
`OPENAI_API_KEY`). `sync` keeps the model a block was written for, whatever your agent uses now.

Training cutoffs come from [models.dev](https://models.dev) (a snapshot is bundled for offline
use). `since-cutoff models sonnet` lists them; `--cutoff 2025-07` overrides the date, and
`since-cutoff scan --cutoff 2025-07` without `--model` scans against that date alone. `scan` and
`sync` need only the cutoff, so they also take a model id without a provider
(`claude-haiku-4-5`, `sonnet`) or with any provider models.dev lists (`google:gemini-2.5-pro`,
Amazon Bedrock and Vertex AI ids included); `run` needs a provider from the table above.

## Results

What has been measured so far, each with its scope:

- **One project, one model, since-cutoff 0.1.0**: the card below, Claude Opus 4.6 on the sample
  project. The table after it adds Claude Haiku 4.5 on the same project.
- **Benchmark**: 360 headless Claude Code sessions (`claude-opus-5-5`) on 24 Python tasks with
  hidden tests, protocol frozen before the main run. On the 17 post-cutoff tasks, sessions with
  since-cutoff 0.4.1's notes cost 0.80 times as much as Claude Code alone (95% CI 0.70-0.90),
  with 0.83 times the turns and 0.87 times the wall time. No pass-rate claim: Claude Code alone
  already passed 94.1% of them, above the pre-registered 90% ceiling. The Context7 arms ran
  without an API key and got only "Monthly quota exceeded" from the 215th of 360 sessions on,
  which does not touch the notes-vs-alone comparison. One model, one agent:
  [results](https://mohammadhijjawi97.github.io/since-cutoff/benchmark.html),
  [tasks, protocol and transcripts](https://github.com/MohammadHijjawi97/since-cutoff-benchmark).
- **Reports from independent developers** will be listed here, each with its project, model and
  date. Post yours in [Share your results](https://github.com/MohammadHijjawi97/since-cutoff/discussions/6).

<p align="center"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/hero-dark.svg">
  <img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/hero.svg" width="640" alt="Your coding model learned your libraries before they changed. Claude Opus 4.6 on one sample project, measured with since-cutoff 0.1.0: on 7 of 16 probed API changes it used a name or parameter that has since been removed; with the notes, 5% to 65% of 20 held-out tasks were correct. Try it: uvx since-cutoff scan (no model calls, no API key).">
</picture></p>

Two Claude models on the 9-dependency sample project in
[`examples/agent-app`](https://github.com/MohammadHijjawi97/since-cutoff/tree/main/examples/agent-app),
**measured with since-cutoff 0.1.0**, with Claude Opus 4.6 writing the tasks and notes:

| | Claude Haiku 4.5 | Claude Opus 4.6 |
|---|---|---|
| training cutoff | Feb 2025 | May 2025 |
| API changes probed | 20 | 16 |
| **stale** / wrong / deprecated / correct | **5** / 1 / 2 / 12 | **7** / 0 / 3 / 6 |
| libraries with stale use | 3 of 5 probed | 2 of 4 probed |
| notes written (with an example that type-checks) | 8 (7), about 391 tokens | 10 (7), about 437 tokens |
| **held-out correct, without -> with notes** | **14% -> 57%** (14 pairs) | **5% -> 65%** (20 pairs) |
| previously-correct APIs after notes | 6/6 still correct | 6/6 still correct |

*Held-out* tasks are paraphrases of the task each failing change was probed with; each one is
answered twice, without and with the notes, and scored the same way. The last row re-checks APIs
the model already got right, to catch notes that make things worse.

In this sample the stronger model was not safer: Opus 4.6 wrote APIs that were removed after its
cutoff, including `anthropic.HUMAN_PROMPT` with `client.completions`. Stale code from both runs,
each valid for the comparison release and rejected by the type checker for the pinned one:
`messages.create(temperature=...)` (anthropic 1.8), `hf_hub_download(resume_download=...)`,
`local_dir_use_symlinks=...`, `force_filename=...` and `proxies=...` (huggingface-hub 2.0), and
`client.beta.vector_stores` (openai 3.x). At run time, anthropic 1.8.0 raises `TypeError` for
`temperature`; huggingface-hub 2.0.0 still accepts those four download arguments, ignores them
and warns.

The notes written in the Claude Haiku 4.5 run (excerpt, verbatim; since-cutoff 0.1.0's format):

```markdown
<!-- since-cutoff:start -->
## Library changes after the model's training cutoff

**anthropic 1.8.0**
- `temperature=...` was removed from `messages.create()` in anthropic 1.8.0. Omit the `temperature` parameter entirely; there is no replacement.

**huggingface-hub 2.0.0**
- `hf_hub_download(..., resume_download=True)`: The `resume_download` parameter was removed in huggingface-hub 2.0.0. Omit it; downloads resume automatically.

**openai 3.19.2**
- `client.beta.vector_stores` is removed in openai 3.19.2. Use `client.vector_stores` instead.
<!-- since-cutoff:end -->
```

The huggingface-hub note is not quite right: `resume_download` left the signature in 1.0, not
2.0.0, and 2.0.0 still accepts it at run time, ignores it and warns
([source](https://github.com/huggingface/huggingface_hub/blob/v2.0.0/src/huggingface_hub/utils/_validators.py#L171-L191)).
Omitting it is still the right advice. The note 0.4.0 writes from the API diff for the same
arguments is in [Keep the notes current](https://github.com/MohammadHijjawi97/since-cutoff#keep-the-notes-current-sync-and-status);
the runtime caveat is in the terminal, the report and the JSON, not in the block.

The terminal summary of the Claude Opus 4.6 run, recorded with 0.1.0. The probe results are the
ones in the table above. The diff counts on the card are 0.1.0's ("725 changes flagged"); after
fixes to the diff, `scan` in 0.2.0 reports 513 breaking changes and 48 new deprecations for the
same cutoff. The card's "changes fixed" count and its 95% CI also follow 0.1.0: the interval
belongs to that count, not to the 5% -> 65% rates, and versions up to 0.2.0 counted a change as
fixed even when a held-out answer was already correct without the notes.

<p align="center"><img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/run-opus.svg" width="100%" alt="since-cutoff 0.1.0 run on Claude Opus 4.6: stale API use in 2 of 4 probed dependencies; 16 API changes probed: 7 stale, 0 wrong, 3 deprecated, 6 correct; 10 notes; held-out tasks correct without -> with notes: 5% -> 65% (20 paired tasks); a list of the stale calls"></p>

<details>
<summary>The same summary for the Claude Haiku 4.5 run (also 0.1.0; scan in 0.2.0 reports 491 breaking changes and 50 new deprecations for its cutoff)</summary>
<p align="center"><img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/run.svg" width="100%" alt="since-cutoff 0.1.0 run on Claude Haiku 4.5: stale API use in 3 of 5 probed dependencies; 20 API changes probed: 5 stale, 1 wrong, 2 deprecated, 12 correct; 8 notes; held-out tasks correct without -> with notes: 14% -> 57% (14 paired tasks)"></p>
</details>

Small samples, two models, one project: treat this as a demonstration of the method, not a
benchmark. Every run writes its full report (each task, answer and type-checker error) to
`.since-cutoff/report.md`. To repeat the experiment with the current version (its diff and
ranking changed, so the probes will not be identical):
`cd examples/agent-app && since-cutoff run --model claude-code:claude-haiku-4-5 --task-model claude-code:claude-opus-4-6`.
Since 0.3.0, a run can also save its tasks: add `--tasks-out tasks.json`, and anyone
can repeat the run on exactly the same tasks with `--tasks-from tasks.json`, for another model or
another set of notes. The file names who wrote the tasks (model, prompt version, since-cutoff
version), and a run on reused tasks reports it
([details](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/docs/how-it-works.md#2-probe)).
Results from your own projects are very welcome in
[Share your results](https://github.com/MohammadHijjawi97/since-cutoff/discussions/6).

How the measurement works and what these numbers do and do not show, in more detail:
[the write-up](https://mohammadhijjawi97.github.io/since-cutoff/).

## Use it from any agent (MCP)

`since-cutoff mcp` is an MCP server that lets a coding agent ask "what changed in this library
since my training cutoff?" before it writes code. It has three read-only tools and two prompts:

| tool | answers |
|---|---|
| `api_changes(package, model, symbol=...)` | what changed in one library between the release at the model's cutoff and the latest (or a given) version, hard breaks first |
| `project_changes(project_dir, model)` | the same for every dependency of a project at its pinned version, starting with the changed APIs your code uses: for each, the files that use it (at most 3), its note, the runtime caveat and names that look similar, not confirmed as replacements |
| `model_cutoff(model)` | a model's training cutoff, from [models.dev](https://models.dev) |

| prompt | asks the agent to |
|---|---|
| `check_project(project_dir=".")` | call `project_changes` with its own model id, start with old-form uses, and offer `since-cutoff sync` for AGENTS.md notes |
| `before_upgrade(package, to_version="")` | read the pinned package version, call `api_changes` for the intended upgrade, and list what project code needs to change |

The agent passes its own model id, so the answer covers what changed after that model's training
cutoff. The tools read PyPI and package sources statically: no model calls, no API key, no
package code executed.

**Claude Code**

```bash
claude mcp add --scope user since-cutoff -- uvx since-cutoff@latest mcp
```

**Codex** (`~/.codex/config.toml`)

```toml
[mcp_servers.since-cutoff]
command = "uvx"
args = ["since-cutoff@latest", "mcp"]
startup_timeout_sec = 60
tool_timeout_sec = 900
```

**Cursor** (`~/.cursor/mcp.json`) and **Claude Desktop** (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "since-cutoff": { "command": "uvx", "args": ["since-cutoff@latest", "mcp"] }
  }
}
```

**VS Code** (`.vscode/mcp.json`)

```json
{
  "servers": {
    "since-cutoff": { "type": "stdio", "command": "uvx", "args": ["since-cutoff@latest", "mcp"] }
  }
}
```

**Gemini CLI**

```bash
gemini mcp add --scope user since-cutoff uvx since-cutoff@latest mcp
# or as an extension, which starts the same server:
gemini extensions install https://github.com/MohammadHijjawi97/since-cutoff
```

`@latest` makes `uvx` pick up new releases instead of reusing the first version it cached (the
plugin's own `.mcp.json` pins the exact release). If the client cannot find `uvx`, install
[uv](https://docs.astral.sh/uv/) or give the full path (`which uvx`). The server is listed in the
[MCP Registry](https://registry.modelcontextprotocol.io) as `io.github.MohammadHijjawi97/since-cutoff`.

The first `project_changes` call on a larger project downloads the wheels of every dependency
that changed and can take several minutes (very large packages such as transformers take the
longest). Results are cached, so later calls take seconds. To warm the cache, run
`since-cutoff scan` in the project once; it shares the cache with the server. Clients with a
short default tool timeout may need a longer one, as in the Codex example above.
`project_changes` keeps its answer under about 24,000 characters: changed dependencies that do
not fit get one line each, and passing them in `only` lists their changes.

What `api_changes("huggingface-hub", model="claude-haiku-4-5", to_version="2.0.0")` returns
(real output, trimmed):

```markdown
# huggingface-hub 0.29.1 -> 2.0.0

- From 0.29.1 (2025-02-20): the newest release on or before 2025-02-28 (training cutoff of claude-haiku-4-5, from models.dev)
- To 2.0.0 (2026-09-24): as requested
- 109 breaking changes, 0 new deprecations (dependencies switched 1, removed or moved 56, parameters removed 43, parameters now required 7, changed kind 1, now keyword-only or positional-only 1)

## Dependencies switched

- huggingface-hub requires `httpx2` instead of `requests`; its Requires-Dist lists `httpx2<3,>=2.0.0`, and `requests` only for its `gradio` extra; 6 places in its public API that named `requests` types name `httpx2` types: `get_session()` returns `httpx2.Client`, `HfHubHTTPError(response=...)` takes `httpx2.Response` and `HfFileSystemStreamFile.response` is `httpx2.Response`; `InferenceTimeoutError`, `HfHubHTTPError` and `TextGenerationError` derive from `httpx2.HTTPError` instead of `requests.HTTPError`

## Removed or moved

- `huggingface_hub.InferenceApi` was removed
...

## Parameters removed

- `huggingface_hub.InferenceClient.text_generation(stop_sequences=...)`: parameter `stop_sequences` was removed; the old docs said: Deprecated argument. Use `stop` instead; also changed under 1 other path, e.g. `huggingface_hub.AsyncInferenceClient.text_generation`
...
- `huggingface_hub.snapshot_download(proxies=...)`: parameter `proxies` was removed; 2.0.0's source still handles `proxies` (huggingface_hub/utils/_validators.py:178), so calls passing it may run with a warning; type checkers reject it
...

Not listed: 69 breaking changes, 0 new deprecations (removed or moved 41, parameters removed 28). Narrow with symbol="..." or raise limit.
```

With `symbol="hf_hub_download"` it lists only the 8 changes to that function (`resume_download=`,
`force_filename=`, `local_dir_use_symlinks=` and `proxies=`, on the function and on `HfApi`).
`symbol` also takes a call the way code writes it: `client.messages.create` finds the changes
to `Messages.create`. The diff reads signatures: these four parameters left the signature in
huggingface-hub 1.0, and the answer adds that 2.0.0's source still handles them, so calls
passing them may run with a warning.

## Use in CI

### GitHub Action

Scans the project on each pull request and adds a summary to the job page: the changed APIs your
code uses, with the files that use them, the change, whether in the old form and the
replacement, then, folded, the notes and each dependency's changes. With `check-notes: true` it
also fails the job when the notes in AGENTS.md are out of date. Like `scan`, it only reads PyPI
and models.dev: no model calls, no API key.

```yaml
# .github/workflows/since-cutoff.yml
name: since-cutoff
on:
  pull_request:
    paths: ["**/*.lock", "**/pylock*.toml", "**/requirements*.txt", "**/pyproject.toml", "**/AGENTS.md", "**/CLAUDE.md"]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: MohammadHijjawi97/since-cutoff@v0
        with:
          model: anthropic:claude-sonnet-4-5  # the model your team codes with
          check-notes: true                   # fail when AGENTS.md needs `since-cutoff sync`
```

Without `paths`, the job also runs when a code change starts using a changed API.

| input | default | |
|---|---|---|
| `model` | required | `provider:model` as for `--model`; only its training cutoff is used |
| `working-directory` | `.` | the project directory |
| `only`, `exclude` | | comma-separated PyPI names |
| `cutoff` | | override the training cutoff (`YYYY-MM` or `YYYY-MM-DD`) |
| `fail-on-changes` | `false` | fail the step when a dependency changed its API after the cutoff |
| `check-notes` | `false` | also run `since-cutoff sync --check`, which writes nothing, and fail the job when the notes in AGENTS.md / CLAUDE.md are out of date or the block was edited by hand; the notes keep the model they were written for, and `model` (and `cutoff`) serve a project with no block yet |
| `step-summary` | `true` | add the Markdown summary to the job summary |
| `cache` | `true` | keep PyPI metadata, package sources and API diffs between runs (also when `fail-on-changes` fails the job) |
| `args` | | more `since-cutoff scan` arguments, e.g. `--all-deps --limit 20` |
| `since-cutoff-version` | `0.5.0` | the since-cutoff release to run, or `latest` |

`args: --fail-on old-form --annotate github` fails the job only when your code uses a changed
API in the old form, and annotates each file that uses one: a warning for the old form, a notice
otherwise.

Outputs: `changed-packages` (comma-separated), `changes` (breaking changes), `deprecations`,
`markdown` (the summary's path, for example to post it as a pull request comment), `report`
(the full report's path) and, with `check-notes`, `notes` (`up-to-date`, `out-of-date`,
`edited-by-hand` or `error`). A change reachable under several import paths is counted once.

### pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/MohammadHijjawi97/since-cutoff
    rev: v0.5.0
    hooks:
      - id: since-cutoff-scan
        args: [--model=anthropic:claude-sonnet-4-5]  # add --fail-on=old-form to block the commit
      - id: since-cutoff-sync  # keeps the notes in AGENTS.md current; args: [--check] only checks
```

`since-cutoff-scan` runs when a lockfile, a requirements file or `pyproject.toml` changes, and
prints the scan; give it `--model` in `args`. `since-cutoff-sync` runs when one of those files,
AGENTS.md or CLAUDE.md changes, and updates the notes; when it changes the file, the hook fails,
as pre-commit hooks that change files do: add the file and commit again. With `args: [--check]`
it changes nothing and fails while the notes are out of date. It keeps the model the notes were
written for; for a first block, give it one: `args: [--model=anthropic:claude-sonnet-4-5]`. Both
need PyPI, so skip them on pre-commit.ci (`ci: {skip: [since-cutoff-scan, since-cutoff-sync]}`).
`since-cutoff-status` needs no network: it fails when the notes do not match the lockfile.

### Other CI

```bash
# Markdown summary for any CI; exit code 3 if your code uses a changed API in the old form
since-cutoff scan --model anthropic:claude-sonnet-4-5 --markdown summary.md --fail-on old-form

# exit code 3 if the notes in AGENTS.md are out of date, 4 if the block was edited by hand
since-cutoff sync --check

# measure the model as well (needs its API key, or the claude CLI)
since-cutoff run --quick --fail-on-stale --json > since-cutoff.json
```

`--markdown -` prints the summary to stdout, and only the progress and the report's path to
stderr, as `--json` does. In a file, a pipe or a CI log there is no live progress bar, and the
output is laid out 160 columns wide (`COLUMNS` sets another width). Exit codes:

- `0` ok;
- `1` error (for example, `run` could not probe any API change or score any model answer, or
  `sync` could not check a package its notes are about);
- `2` usage error;
- `3` a check failed: `scan --fail-on changes`, `used` or `old-form` (a dependency changed its
  API after the cutoff, your code uses a changed API, or uses one in the old form;
  `--fail-on-changes` is `--fail-on changes`), `run --fail-on-stale` (stale API use found), or
  notes out of date with `sync --check` or `status` (and `sync`, when it did not write them);
- `4` `sync`: the block was edited by hand, and nothing was written without `--force`;
- `141` the output was closed early (piped into `head`, for example).

## How it works

`scan` and `sync` need no model: they diff the public APIs, find where your code uses the changed
ones and state each change from the diff, tagged with what was checked
([details](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/docs/how-it-works.md#notes-without-a-model-scan-and-sync)).
`run` goes through three stages. The first is the scan and needs no model; in the other two, a
type checker scores every answer and checks every note the model writes:

<p align="center"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/how-it-works-dark.svg">
  <img src="https://raw.githubusercontent.com/MohammadHijjawi97/since-cutoff/main/docs/img/how-it-works.svg" width="640" alt="Three stages. Scan, with no model calls: the lockfile gives your exact versions, then the release at the model's cutoff, then a static API diff with griffe. Probe: short tasks that need the change, the model answers from memory, basedpyright checks the answer against both versions. Write and test notes: a model-written note is kept only if its example type-checks, otherwise the change is stated from the API diff; held-out tasks are answered without and with the notes, and --apply writes a block into AGENTS.md.">
</picture></p>

| outcome | meaning |
|---|---|
| **stale** | the code is valid for the comparison release (the one at the model's cutoff) and invalid for yours, and the error involves an API that changed |
| **wrong** | invalid for your version, but not explained by a change (hallucinated or misused API) |
| **deprecated** | valid, but uses an API marked `@deprecated` in your version |
| **correct** | valid for your version and actually uses the changed API |
| untouched / off-task / invalid / error | not counted in any rate, and always reported |

Since 0.3.0, the held-out result gives the task-level rates without -> with notes
(with the number of paired tasks and API changes behind them), their difference with a 95%
bootstrap interval that resamples API changes, the changes the notes fixed (wrong without,
correct with) with a Wilson 95% interval, the changes they broke, an exact sign test of fixed
against broken, and the held-out pairs not counted, by reason. The regression check reports how
many previously-correct APIs are still correct with the notes.

`run --compare template,signatures` (0.3.0 and later) also answers the held-out tasks and
regression checks with baseline notes that need no model: `template` states each failing change in
one sentence from the API diff, and `signatures` gives the new signature and first docstring
paragraph of each changed API, or of the replacement its library names. All blocks are scored on
the same pairs, against the same answers without notes, and each block's size is shown in tokens,
so a run shows what since-cutoff's own notes add over them.

Everything is scored by a type checker against the exact package versions, each in an isolated
environment with that package's own runtime dependencies. No LLM judges anything, and every
number traces back to `results.json`. Details: [docs/how-it-works.md](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/docs/how-it-works.md).

### What "verified" means

since-cutoff does not use the word "verified" on its own. Each note carries a tag that says what
was checked, and nothing else is claimed:

| tag | what was checked | what was not |
|---|---|---|
| `[diff]` | The change is in a static comparison (griffe) of the public APIs of two releases: the latest release on or before the model's training cutoff, and the version your project pins. The sources are read, not imported. With `[diff]` alone, no replacement is named: the note says what the library's own deprecation text says ("there is no replacement for `resume_download`"), or that since-cutoff found no replacement in it. | Behaviour, and whether a call still runs: the pinned release may still accept a removed parameter with a warning, as huggingface-hub 2.0.0 does for `resume_download`. The terminal, report.md, the MCP tools and the JSON add a "Runtime:" line when the pinned source still handles one; the block does not, since the advice is the same. Whether your model gets it wrong. |
| `[diff + library]` | As `[diff]`, and the library's own deprecation text (a docstring, a parameter's docstring entry, an `@deprecated` message or a `warnings.warn` text, in the older release or, for a deprecation, in the pinned one) states the replacement ("Use `stop` instead"), and that name exists in your pinned version. Text that only mentions a name as advice is quoted under `[diff]`, not taken as a replacement. | That the replacement behaves the same. |
| `[diff + move checked]` | As `[diff]`, and the object at the new path is the same object as far as can be counted: a class or module keeps at least half of the old one's public names, a function keeps its parameters, a value is the same. | Behaviour. |
| `[diff + metadata]` | The older release's Requires-Dist (its wheel's METADATA) lists a library the pinned one does not, and places in the public API that named that library's types (parameters, return types, attributes, base classes, re-exports) name the types of another library the pinned release requires, or of a copy of the old one it ships, with none of the old library left: openai 3.x, anthropic 1.8, huggingface-hub 2.0 and mcp 2.2 take `httpx2` objects where they took `httpx` ones. | Behaviour: whether the pinned release still accepts the old library's objects (openai 3 converts some, anthropic 1.8 raises `TypeError`, according to their sources). The terminal, report.md, the MCP tools and the JSON add an "Installed:" line (whether your project, its virtual environment included, still has the old library) and a "Runtime:" line that points to where the pinned source still names it. |
| `[diff; probable rename]` | A parameter in the same position, with the same annotation, has a new name, and no version note in the pinned release's docstring (`.. versionadded::`, `.. versionchanged::`) says that one was added or the other removed. A guess, labelled as one. | That it is the same parameter. |
| `[type-checked]` | Written by a model during `since-cutoff run` and kept because its example passed the type check below. | Behaviour; that the bullet's explanation is true beyond the names it shows. |
| `[not confirmed]` | Only with `sync --suggestions`: names in the pinned version that look similar to what was removed (the bullet's tag then reads `[diff; not confirmed]`). | That any of them replaces it. |

Tags combine: evidence is joined with `+` (`[diff + library]`), and a guess comes after `;`
(`[diff; probable rename]`, `[diff; not confirmed]`).

Names that merely look similar are never written into the notes by default. The terminal,
report.md and the MCP tools show them as "not confirmed as replacements", and not at all where
the library says there is no replacement; `sync --suggestions` adds them, tagged
`[not confirmed]`.

**The type check behind `[type-checked]`.** A model-written note is kept only when all of these
hold (the model gets two tries):

- its complete example parses and imports the package;
- basedpyright (standard mode, deprecations reported as errors, `# type: ignore` and `# pyright:`
  comments removed) reports no error attributed to that package, and no deprecation of it, when
  the example is checked against the sources of the exact version in your lockfile plus that
  version's runtime dependencies, in an otherwise empty environment;
- every library name the bullet puts in backticks appears in that example or in the API-diff entry
  the note is about;
- the bullet has at most 60 words.

So `[type-checked]` means the imports, names, parameters and argument counts the example uses exist
in your version and are not marked `@deprecated` (PEP 702). Errors outside the package (the
standard library, other libraries) do not block a note. It does not mean that the code behaves
correctly at run time, that the replacement is the one the maintainers recommend, or that the note
helps the model. When a note fails the check, since-cutoff writes the note from the API diff
instead, with its tag.

**Measured** is separate: `since-cutoff run` answers held-out tasks without and with the notes and
reports the counts. Nothing else in since-cutoff says whether a note helps.

**In `run`, an answer counts as correct** when it imports the package, uses the changed API, and
has no "knowledge" error attributed to the package on your version (unknown name, import or
parameter; missing required argument; wrong number of arguments). Pure type-strictness complaints
are ignored. No answer is executed.

The block in AGENTS.md holds the bullets with their tags, and for each package the version its
notes apply to and the release at the cutoff. The rest is in `scan --json` and `results.json`:
`used_apis[]` (each changed API your code uses, where, its changes, its replacements with their
source, and its note with `tags`, `applies_to` and `checks`) and, after `run`, `notes_detail[]`
(each note with the model's example and what the held-out test measured; `verified` is kept,
meaning the same as `checks.example_type_checks`).

## What it runs, sends and stores

- **Runs no package code and no model-written code.** Packages are read statically (griffe with
  inspection off; only `.py`/`.pyi` files are extracted, with path and size checks). The model's
  answers are only type-checked, locally, with basedpyright.
- **Fetches** public package metadata and wheels from PyPI, and model cutoffs from models.dev (a
  snapshot is bundled for offline use). Release lists are cached for 12 hours; when PyPI cannot
  be reached, an older cached copy is used and the scan says from which day it is. Each
  downloaded wheel or sdist is checked against the
  sha256 that PyPI lists before extraction. Git, path, workspace and private-index dependencies
  are never looked up on public PyPI by name. `status` fetches nothing.
- **Sends** prompts only in `run`, and only to the model provider you choose: package names,
  versions, public signatures and docstrings of the changed APIs, the generated tasks and, for
  notes, the model's own answers. Never your source code. `scan`, `sync`, `status`, the MCP
  server, the GitHub Action and the pre-commit hooks send nothing to any model.
- **Shows where your code uses a changed API** (file names for now) in the terminal and in
  `.since-cutoff/`, and sends it nowhere. What you pass on is up to you: `--markdown` and
  `--annotate github` put it in a CI job's summary and annotations, and the MCP tool
  `project_changes` gives it to the agent that asked, which passes tool results to its model.
- **Stores** results in `.since-cutoff/` in your project (it ignores itself in git) and a local
  cache (`since-cutoff cache path` shows it, `since-cutoff cache clear` removes it). `sync` (after
  you agree, or with `--yes`) and `run --apply` write one marked block into AGENTS.md or CLAUDE.md
  and leave the rest of the file byte-for-byte unchanged; `since-cutoff unapply` removes the
  block.
- **No telemetry**, no account, no personal data. Re-runs come from the cache, so they are free
  and reproducible (`--fresh` asks the model again). See [PRIVACY.md](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/PRIVACY.md).

## Limitations

- Python only for now. TypeScript (`.d.ts` diffs, `tsc`) is next
  ([#1](https://github.com/MohammadHijjawi97/since-cutoff/issues/1)).
- A type checker sees wrong names, wrong parameters and PEP 702 deprecations. It cannot see
  behaviour changes behind an unchanged signature, or deprecations that only warn at run time.
  `scan` also lists deprecations declared with a library's own decorator (name containing
  "deprecat") and removed names that a module still serves with a warning through
  `__getattr__`, but `run` does not probe them.
- The diff covers the public API: `_private` names, and test suites, benchmarks and examples
  shipped inside a package, are skipped.
- "Your code uses" is a static name match, file by file: imports (re-exported names included),
  calls, attribute reads and keyword arguments. It does not follow dynamic access such as
  `getattr`, and it names files, not lines, for now
  ([#8](https://github.com/MohammadHijjawi97/since-cutoff/issues/8)). A parameter that became
  required, keyword-only or positional-only is always "uses this API", never "old form", for now.
- A note names a replacement only when the library's own deprecation text states it. Advice that
  is only in a migration guide (anthropic's
  [MIGRATION.md](https://github.com/anthropics/anthropic-sdk-python/blob/main/MIGRATION.md)
  suggests `extra_body` for older models that still take `temperature`) is not in the notes.
- Probes cover a ranked **sample** of the breaking changes (symbols your code already uses
  first), not all of them.
- "The comparison release" is the newest release on or before the cutoff date. Models know
  recent releases less well, so real staleness can start earlier.
- Held-out tasks are paraphrases of the same change: they show that a note fixes *that* change,
  not that the model got better in general.

### What the training cutoff is used for

The cutoff date picks a comparison point. It is not a claim about what a model memorised.
since-cutoff takes the date from models.dev (or `--cutoff`); a month means its last day
(`2025-07` is 31 July 2025). For each dependency it takes the newest final, non-yanked release
uploaded on or before that date (a pre-release only if the package had no final release by then,
never a development release), and diffs that release's public API against your locked version.
That diff is a list of candidates: API changes that the model's training data probably does not
include.

The date decides three things:

- which packages are diffed at all: a package whose locked version is no newer than that release
  has nothing to diff, and a package first released after the date is listed as new;
- in `run`, which versions of that release's own dependencies the old side is type-checked with
  (the newest each requirement allowed on that date);
- the "old" side of every probe in `run`, so an answer that is valid there and invalid for your
  version, with the error on a changed API, is "stale" rather than "wrong".

A model can know a release after its stated cutoff or not know releases shortly before it, so the
scan can list changes the model already handles and miss some it does not. Whether the model
actually writes the old API is shown only by `run`, which asks it: with no tools, told which
version the project pins.

## How it compares

since-cutoff answers one question for one project: which public APIs of the versions you pin
changed since the release a model's training cutoff points to, starting with the ones your code
uses? `since-cutoff run` adds two optional questions: does this model actually get them wrong,
and does a short note fix it? Most tools below answer a different question ("what do the
library's docs say now?") and work well alongside it.

| tool | what it does | how since-cutoff relates |
|---|---|---|
| [Context7](https://github.com/upstash/context7) (MCP server and `ctx7` CLI) | The agent calls `resolve-library-id` and `query-docs` to pull documentation snippets into its context while it works. It serves a specific version (`/org/project/version`) when the library's owners have added that version (git tags or branches, at most 20); otherwise it serves the indexed branch. Works without an API key at a lower, anonymous rate limit. | Complementary. Context7 supplies documentation; it does not read your locked versions or check the code the agent writes. since-cutoff lists which of your pinned APIs changed after the model's cutoff, the ones your code uses first, so you know where a lookup or a note is needed. When you ask Context7, name the version you pin. |
| Other docs servers: [Ref](https://github.com/ref-tools/ref-tools-mcp), [docs-mcp-server](https://github.com/arabold/docs-mcp-server) | Documentation search for agents, at answer time; docs-mcp-server can index docs locally | Same as Context7. |
| [library-skills](https://github.com/tiangolo/library-skills) | Libraries such as FastAPI and Streamlit ship agent skills inside their packages; `uvx library-skills` links the skills of the versions you have installed into `.agents/skills` or `.claude/skills`, so they update with the library | Written by the maintainers and in step with your installed version: when a library ships one, use it. since-cutoff covers packages that ship no guidance, and only states changes to the API surface. |
| Vendor skill plugins, e.g. [pydantic/skills](https://github.com/pydantic/skills) | Claude Code, Codex and Cursor plugins and `SKILL.md` files for Pydantic, Pydantic AI and Logfire, installed from the repository | Maintainer guidance on how to use a library well; released with the plugin repository, not with the version you pin. since-cutoff's notes are written for your lockfile. |
| Codemods: [ast-grep](https://ast-grep.github.io/) rules, OpenAI's `openai migrate` ([Grit](https://github.com/openai/openai-python/discussions/742)) | Rewrite code that already exists with hand-written syntactic rules; ast-grep's catalog has an [OpenAI SDK migration](https://ast-grep.github.io/catalog/python/#migrate-openai-sdk) (`openai.Completion.create(...)` to `client.completions.create(...)`) | For migrating code you already have, a codemod is the right tool. since-cutoff is about the code an assistant writes next: it finds the changes from the API diff instead of from rules someone wrote, and only suggests; it rewrites nothing. |
| Dependency bots: [Renovate](https://github.com/renovatebot/renovate), [Dependabot](https://github.com/dependabot/dependabot-core) | Open pull requests that update your pinned versions | The GitHub Action can run on those pull requests, list the changed APIs your code uses and the files that use them, and, with `check-notes`, fail until the notes are synced. |
| Benchmarks: [GitChameleon 2.0](https://arxiv.org/abs/2507.12367), [VersiCode](https://arxiv.org/abs/2406.07411), [CodeUpdateArena](https://arxiv.org/abs/2407.06249), [LibEvolutionEval](https://arxiv.org/abs/2412.04478) | Measure models on fixed task sets built from real version changes, or synthetic ones (CodeUpdateArena); GitChameleon 2.0 runs unit tests | They compare models in general, and some check behaviour by running tests. since-cutoff looks at one project's pinned versions, statically: a type checker sees names, parameters and deprecations, not behaviour. |

`--compare signatures` in `since-cutoff run` gives the model the new version's signature and the
first paragraph of its docstring. It is a local stand-in for a documentation lookup, not Context7.

Two smaller tools work on the same problem: [cutoff](https://github.com/sandeepsirodia/cutoff)
probes a library you maintain by running model-written programs against its current version, and
[postcut](https://github.com/justi/postcut) turns a Ruby `Gemfile.lock` into a brief of changes
since the cutoff. since-cutoff is built on [griffe](https://mkdocstrings.github.io/griffe/),
[basedpyright](https://github.com/DetachHead/basedpyright), [models.dev](https://models.dev) and [rich](https://github.com/Textualize/rich).

### Using since-cutoff with Context7

`since-cutoff scan` tells you which APIs to look up; Context7 can supply the docs. Name the
version you pin when you ask ("anthropic 1.8.0"). Context7 matches it only when the library's
owners [added that version](https://github.com/upstash/context7/blob/master/docs/howto/claiming-libraries.mdx):
on 2026-09-27, `/openai/openai-python` offered v1.68.0, v1_105_0, v2.8.1 and v2.11.0, and
`/anthropics/anthropic-sdk-python` offered none, so you may get the default branch's docs.

## Related research

- **Deprecated APIs in code completion.** Wang et al., *LLMs Meet Library Evolution: Evaluating
  Deprecated API Usage in LLM-based Code Completion* (ICSE 2025;
  [arXiv:2406.09834](https://arxiv.org/abs/2406.09834), first titled *How and Why LLMs Use
  Deprecated APIs in Code Completion? An Empirical Study*). 7 models, 145 mappings from a
  deprecated API to its replacement in 8 Python libraries, 28,125 completion prompts. Most
  completions used neither API. Of those that used one of the two (the paper's "plausible"
  completions), 25-38% used the deprecated one over the whole dataset: 70-90% when the prompt came
  from code that used the deprecated API, 9-18% when it came from up-to-date code. Two baseline
  fixes were tested on up-to-date prompts where a model had used the deprecated API. ReplaceAPI
  swaps the deprecated API's tokens for the replacement during decoding and lets the model finish
  the line: the replacement was then used in 85.2-99.6% of cases on the six open models (it needs
  control of decoding, so not GPT-3.5). InsertPrompt adds the comment
  `# {dep} is deprecated, use {rep} instead and revise the return value and arguments.` and
  regenerates: 25.7-97.2%, depending on the model, which the authors judge not yet effective or
  accurate enough. since-cutoff's notes are close to InsertPrompt, moved into the project's
  instructions file; `since-cutoff run` measures them on held-out tasks instead of assuming they
  work.
- **Documentation in context is not enough on its own.** Ashik et al., *When LLMs Lag Behind:
  Knowledge Conflicts from Evolving APIs in Code Generation*
  ([arXiv:2604.09515](https://arxiv.org/abs/2604.09515), 2026 preprint). 270 real API updates (45
  deprecated or removed, 128 modified, 97 new) from releases of 8 Python libraries after December
  2023, and 11 models from 4 families with training cutoffs before that date. Given only a
  description of the update, the models at least partly adopted it in 74.64% of answers (judged
  by GPT-5 mini), and 42.55% of those answers ran in the library version that introduced the
  update; with the API documentation as well, 92.87% adopted it and 66.36% ran. Adding
  chain-of-thought and self-reflection prompts raised the executable rate by a further 11.33%, a
  relative gain rather than percentage points. Of the answers that did not adopt the update, 42.1%
  ignored it entirely and 16.4% used the old API; of the adopting answers that still failed to run
  in the best setup, the most common update-related cause was wrong parameters (26.6% of those
  failures). This is why since-cutoff checks code against your exact version, and why
  `since-cutoff run` re-tests the model with the notes rather than assuming they are followed.
- **Benchmarks.** [GitChameleon 2.0](https://arxiv.org/abs/2507.12367): 328 Python completion
  problems, each tied to specific library versions and checked by executable unit tests;
  enterprise models reach 48-51% at baseline, retrieved documentation adds up to about 10 points
  (GPT-4.1: 48.5% to 58.5%) and self-debugging about 10-20.
  [VersiCode](https://arxiv.org/abs/2406.07411): version-specific code completion and
  version-aware code migration over more than 300 Python libraries and more than 2,000 versions
  across 9 years. [CodeUpdateArena](https://arxiv.org/abs/2407.06249): knowledge editing for 54
  functions from 7 Python packages, with synthetic, GPT-4-generated updates and 670
  program-synthesis examples; prepending the update's documentation did not let open models
  (DeepSeek, CodeLlama) use it. [LibEvolutionEval](https://arxiv.org/abs/2412.04478)
  ([NAACL 2025](https://aclanthology.org/2025.naacl-long.348/)): version-specific inline completion
  across 8 libraries; retrieved version-specific documentation and prompting help.

These studies measure many models on fixed task sets; GitChameleon 2.0 and Ashik et al. run the
generated code. since-cutoff does something narrower: for one project it lists the changes since a
comparison release, the ones your code uses first, and `run` checks one model's answers
statically. It cannot see behaviour changes behind an unchanged signature, which tests that run
the code can.

## Contributing

since-cutoff is young. The most useful help right now:

- **Run it on your project** and post what it found, including false positives, in
  [Share your results](https://github.com/MohammadHijjawi97/since-cutoff/discussions/6).
- **Pick up a [good first issue](https://github.com/MohammadHijjawi97/since-cutoff/labels/good%20first%20issue)**:
  small, self-contained tasks such as another lockfile format or a provider preset.
- **Bigger pieces** are labelled [help wanted](https://github.com/MohammadHijjawi97/since-cutoff/labels/help%20wanted),
  for example [TypeScript support](https://github.com/MohammadHijjawi97/since-cutoff/issues/1).
- **Report a bug or an odd result** in the [issues](https://github.com/MohammadHijjawi97/since-cutoff/issues).

[CONTRIBUTING.md](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/CONTRIBUTING.md)
explains the code layout and the checks; the offline test suite runs the whole pipeline with a
toy library and a scripted model, so no API key is needed. Security issues: [SECURITY.md](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/SECURITY.md).

## Citation

If you use since-cutoff in research, please cite it (see [`CITATION.cff`](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/CITATION.cff)).

## License

MIT © [Mohammad Hijjawi](https://github.com/MohammadHijjawi97)
