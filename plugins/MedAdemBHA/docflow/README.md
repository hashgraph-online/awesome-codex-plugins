<p align="center">
  <a href="https://github.com/MedAdemBHA/docflow">
    <img src="assets/banner.png" alt="docflow banner" width="100%">
  </a>
</p>

# docflow

[![CI](https://github.com/MedAdemBHA/docflow/actions/workflows/ci.yml/badge.svg)](https://github.com/MedAdemBHA/docflow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/MedAdemBHA/docflow?style=flat&logo=github&label=stars)](https://github.com/MedAdemBHA/docflow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/MedAdemBHA/docflow?style=flat&logo=github&label=forks)](https://github.com/MedAdemBHA/docflow/network/members)
[![Last commit](https://img.shields.io/github/last-commit/MedAdemBHA/docflow?style=flat)](https://github.com/MedAdemBHA/docflow/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/MedAdemBHA/docflow?style=flat)](https://github.com/MedAdemBHA/docflow/issues)

<p align="center">
  <a href="#why-docflow">Why DocFlow</a> ·
  <a href="#install-and-run">Install</a> ·
  <a href="#live-demo">Demo</a> ·
  <a href="#token-and-context-efficiency">Context proof</a> ·
  <a href="examples/basic-repo/">Example repo</a> ·
  <a href="#trust-and-safety">Security</a>
</p>

**DocFlow gives AI coding agents durable project memory.** It organizes what the product does, how it works, why decisions were made, what is planned, and what shipped—then routes the agent to the smallest relevant document.

Plain Markdown. Small Bash helpers. No database, hosted service, or source-code rewrite.

> **Status:** early MVP. Claude Code plugin setup works today. Codex works through repository guidance and local plugin development; a public Codex directory listing is not published yet.

## Why DocFlow

| Without DocFlow | With DocFlow |
|---|---|
| Every new session rediscovers the documentation layout | The agent starts from one compact `path → purpose` map |
| Product behavior, implementation, and decisions are mixed together | WHAT, HOW, and WHY have stable homes |
| Existing docs may need a risky manual migration | `doctor` chooses init, adopt, or repair; adoption preserves existing docs |
| Recent shipped work depends on chat history or memory | An append-only monthly changelog carries outcomes into later sessions |
| Broken links and stale indexes are found by accident | Validation checks links, headings, map freshness, and required structure |
| Large documentation sets may be read broadly | The agent opens one routed document first; measured initial docs context stayed below 1% in two established repositories |

### What changes in your repository

```text
your-repo/
├── AGENTS.md                 # agent start and routing rules
├── GEMINI.md                 # points Gemini to the same rules
├── .cursorrules              # points Cursor to the same rules
├── docflow.json              # docs root + validation profile
├── docs/
│   ├── README.md             # human documentation hub
│   ├── INDEX.md              # compact map agents read first
│   ├── product-spec/         # WHAT the product does
│   ├── specs/                # HOW it is implemented
│   ├── decisions/            # WHY choices were made
│   ├── plans/                # planned and in-progress work
│   ├── reviews/              # audits, quality, and known bugs
│   └── changelog/            # shipped outcomes by month
└── scripts/                  # doctor, repair, map, links, validation
```

DocFlow does **not** move existing documentation during adoption, edit application source code, call a remote service, or silently fix user-authored content.

## Install And Run

### Claude Code — plugin setup

Run these inside Claude Code:

```text
/plugin marketplace add https://github.com/MedAdemBHA/docflow
/plugin install docflow
/reload-plugins
```

Then open the target repository:

```text
/docflow:doctor
```

Run the one next command it recommends. Type `/docflow:` to browse commands, or ask naturally: “is DocFlow ready here?”, “where is authentication documented?”, or “add this release to the changelog.”

### Codex, Gemini, Cursor, or any agent — repository setup

This is the verified portable path today:

```bash
git clone https://github.com/MedAdemBHA/docflow.git
cd docflow

# Read-only diagnosis first
bash scripts/docflow-doctor.sh --target /path/to/your-repo

# Empty/new documentation
bash scripts/scaffold.sh --target /path/to/your-repo --docs-root docs --project "My App"

# OR: preserve and adopt existing documentation
bash scripts/docflow-adopt.sh --target /path/to/your-repo --docs-root docs --project "My App"
```

Open the target repository in your agent. Codex reads `AGENTS.md`; Gemini and Cursor are pointed to the same rules. Confirm readiness with:

```bash
bash /path/to/docflow/scripts/docflow-check.sh --target /path/to/your-repo
```

### Codex plugin status

The repository includes a valid [.codex-plugin/plugin.json](.codex-plugin/plugin.json), but DocFlow is not yet published in the public plugin directory. For local plugin development, add the source through a personal/local marketplace, install it from the Codex `/plugins` browser, and start a new session. See the [official OpenAI plugin workflow](https://developers.openai.com/codex/build-plugins).

Until the public listing ships, use the repository setup above instead of copying an unverified `codex plugin add` command.

### First command: doctor

| Repository state | Recommendation | What happens |
|---|---|---|
| No meaningful docs | `init` | Creates the full documentation system |
| Existing project docs | `adopt` | Adds routing and helpers without rewriting existing docs |
| Existing DocFlow repo needs refresh | `repair` | Regenerates the map and updates recognized managed helpers |
| DocFlow is healthy | none | Reports `Ready`; normal work can begin |

### Core commands

| Need | Claude command | Script fallback |
|---|---|---|
| Choose the safe setup path | `/docflow:doctor` | `scripts/docflow-doctor.sh` |
| Get one readiness answer | `/docflow:check` | `scripts/docflow-check.sh` |
| Create a new docs system | `/docflow:init` | `scripts/scaffold.sh` |
| Preserve and adopt existing docs | `/docflow:adopt` | `scripts/docflow-adopt.sh` |
| Refresh generated helpers | `/docflow:repair` | `scripts/docflow-repair.sh` |
| Validate before completion | `/docflow:validate` | `scripts/docflow-validate.sh` |
| Find the right document | `/docflow:router` | Read `docs/INDEX.md` |
| Record shipped work | `/docflow:changelog` | Append the current month |

Full command and skill reference: [docs/references/commands.md](docs/references/commands.md).

## Token And Context Efficiency

DocFlow does not compress the content of project documentation. It reduces context use by loading a small routing layer first, then opening full documents only when the task requires them.

[![DocFlow uses 99%+ less initial documentation context in a measured repository](assets/social/docflow-context-optimization-v2.png)](assets/social/docflow-context-optimization-v2.png)

The default Claude `SessionStart` payload contains:

1. Up to 30 non-empty lines from `docs/INDEX.md` (`path → purpose`).
2. Up to 20 non-empty lines from the newest real monthly changelog.
3. Within that changelog budget, the document header, `Summary`, and newest detailed entry—not the full month.

The agent then opens the exact product spec, technical spec, ADR, plan, review, or reference needed for the current task. `AGENTS.md` uses the same route-first workflow for Codex, Gemini, Cursor, and other repo-aware agents, although automatic `SessionStart` injection is Claude-specific.

### Measured on two established repositories

Measurements taken on 2026-08-13 with `wc -w`, using the default hook limits:

| Repository | All Markdown under `docs/` | Automatic hook payload | Context avoided initially |
|---|---:|---:|---:|
| Repository A | 127,424 words | 605 words | 99.53% |
| Repository B | 129,865 words | 481 words | 99.63% |

These are word counts, not tokenizer-specific token counts. Actual tokens depend on the model tokenizer, Markdown, code, and file paths. The comparison is still useful because it measures the exact text boundary DocFlow controls: full documentation versus the bounded automatic payload.

### What the saving does—and does not—mean

- The hook avoids injecting the full documentation corpus at session start.
- `docs/README.md` and task-specific documents may be read afterward, so total task context will be higher than the hook payload.
- A broad audit can legitimately open many documents; DocFlow optimizes ordinary targeted work, not tasks that require the whole corpus.
- Savings depend on agents following `INDEX.md` and `AGENTS.md` instead of scanning every documentation file.
- Limits can be tuned with `DOCFLOW_INDEX_LINES` and `DOCFLOW_LOG_LINES`; smaller values save more context but expose less navigation/history.

Reproduce the measurement:

```bash
repo=/path/to/repo
find "$repo/docs" -type f -name '*.md' -print0 | xargs -0 wc -w | tail -n 1
CLAUDE_PROJECT_DIR="$repo" bash /path/to/docflow/hooks/docflow-context.sh | wc -w
```

See [Context efficiency](docs/references/context-efficiency.md) for the measurement contract, formula, and interpretation rules.

## Live Demo

The committed [example repository](examples/basic-repo/) is a complete, validation-clean DocFlow setup—not a screenshot or pseudocode.

```bash
# From the DocFlow repository root
bash examples/basic-repo/scripts/docflow-check.sh --target examples/basic-repo
CLAUDE_PROJECT_DIR="$PWD/examples/basic-repo" bash hooks/docflow-context.sh
```

Readiness output:

```text
DocFlow Check
- status: Ready
- docs root: docs (yes)
- validation: profile=strict errors=0 warnings=0
- next: No action needed.
```

Follow one feature across the documentation lifecycle:

| Question | Durable answer |
|---|---|
| What user value does it provide? | [Product overview](examples/basic-repo/docs/product-spec/00-overview.md) |
| How does it work? | [Technical spec](<examples/basic-repo/docs/specs/(jun-26)-context-hook.md>) |
| Why is it designed that way? | [ADR 0001](examples/basic-repo/docs/decisions/0001-session-context-hook.md) |
| What shipped? | [June changelog](<examples/basic-repo/docs/changelog/(jun-26).md>) |
| What comes next? | [Roadmap](examples/basic-repo/docs/plans/upcoming/README.md) |
| What is known to be wrong? | [Open bugs](examples/basic-repo/docs/reviews/bugs/open.md) |

Browse the [human docs hub](examples/basic-repo/docs/README.md), [agent route map](examples/basic-repo/docs/INDEX.md), or [agent instructions](examples/basic-repo/AGENTS.md).

## Documentation Model

| Folder | Answers | Example naming |
|---|---|---|
| `product-spec/` | What does the product do? | `00-overview.md` |
| `specs/` | How is it built? | `(aug-26)-topic.md` |
| `decisions/` | Why was this choice made? | `0001-title.md` |
| `references/` | What rules or conventions apply? | `topic.md` |
| `plans/` | What is planned or in progress? | `(aug-26)-feature.md` |
| `reviews/` | What is risky, broken, or audited? | `(aug-26)-audit.md` |
| `changelog/` | What shipped? | `(aug-26).md` |

Full naming rules: [templates/NAMING.md](templates/NAMING.md).

## Validation Profiles

| Profile | Intended for | Behavior |
|---|---|---|
| `strict` | New DocFlow scaffolds | Enforces native naming and required document structure |
| `adopted` | Repositories with established docs | Blocks objective breakage while reporting convention differences as warnings |

Both profiles block broken local links, stale generated indexes, and Markdown documents without an H1. Adoption preserves existing folders and section vocabulary.

## Trust And Safety

docflow asks users to install an AI-agent plugin and run Bash. That deserves explicit proof.

- Read [SECURITY.md](SECURITY.md) before installing.
- CI runs `shellcheck` on scripts and hooks.
- CI runs [scripts/test-scaffold.sh](scripts/test-scaffold.sh), covering idempotency, special-character project names, JSON validity, link checks, and hook behavior.
- The Claude `SessionStart` hook is read-only and prints truncated docs context only.

Run checks locally:

```bash
bash scripts/test-scaffold.sh
for t in tests/*.sh; do bash "$t"; done
shellcheck scripts/*.sh hooks/*.sh tests/*.sh
```

## Repository Layout

```text
docflow/
├── .claude-plugin/          # Claude plugin manifest
├── .codex-plugin/           # Codex plugin manifest
├── .github/workflows/       # CI
├── commands/                # Claude slash commands
├── examples/basic-repo/     # Filled example output
├── hooks/                   # SessionStart context hook
├── repo-templates/          # AGENTS.md, GEMINI.md, .cursorrules
├── scripts/                 # doctor, adopt, repair, scaffold, map, generators, tests
├── skills/                  # doctor/check/init/adopt/repair/validate/router/author/changelog
└── templates/               # generic docs skeletons
```

## Agent Support

| Agent | Support level | How it works |
|-------|---------------|--------------|
| Claude Code | Primary | Slash commands, skills, and read-only `SessionStart` context hook |
| Codex | Repository guidance + local manifest | Scaffolded `AGENTS.md` works now; public plugin-directory install is pending |
| Gemini / Cursor | Repo guidance | Scaffolded `GEMINI.md` and `.cursorrules` point back to `AGENTS.md` |

The portable product is the docs tree and workflow. The plugin runtime is agent-specific.

## Typical Workflow

1. Run doctor to inspect the repo.
2. Run init for empty docs, adopt for existing docs, or repair for existing docflow.
3. Fill `docs/README.md` and `product-spec/00-overview.md`.
4. Write ADRs, specs, plans, and reviews using the category templates.
5. Append shipped work to the current monthly changelog.
6. Run repair after adding or renaming docs, or when managed helpers have an update.

## Share DocFlow

[![How DocFlow works: diagnose, organize, load less, and validate](assets/social/docflow-feature-overview.png)](assets/social/docflow-feature-overview.png)

Choose the [clean 1200×630 context card](assets/social/docflow-context-optimization-v2.png), [detailed context explainer](assets/social/docflow-context-optimization.png), or [feature overview](assets/social/docflow-feature-overview.png), then copy a tailored caption for [X, LinkedIn, Reddit, or Quora](assets/social/captions.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

This repo dogfoods its own docs system. Browse the knowledge base at [docs/README.md](docs/README.md) — start with [docs/INDEX.md](docs/INDEX.md) for the full `path → purpose` map.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Star History

<a href="https://www.star-history.com/#MedAdemBHA/docflow&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=MedAdemBHA/docflow&amp;type=Date&amp;theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=MedAdemBHA/docflow&amp;type=Date" />
    <img alt="DocFlow star history chart" src="https://api.star-history.com/svg?repos=MedAdemBHA/docflow&amp;type=Date" width="800" />
  </picture>
</a>

## License

MIT - see [LICENSE](LICENSE).
