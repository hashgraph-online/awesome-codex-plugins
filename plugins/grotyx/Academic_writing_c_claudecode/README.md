<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.png">
    <img src="assets/logo.png" width="220" alt="ManuWright, the careful senior author">
  </picture>
</p>

<h1 align="center">ManuWright</h1>

<p align="center">
  <em>He will not let you cite a paper you have not registered.</em>
</p>

<p align="center">
  <a href="https://github.com/grotyx/Academic_writing_c_claudecode/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/grotyx/Academic_writing_c_claudecode/tests.yml?style=flat-square&color=111111&label=tests" alt="Tests"></a>
  <img src="https://img.shields.io/github/v/tag/grotyx/Academic_writing_c_claudecode?style=flat-square&color=111111&label=release" alt="Release">
  <img src="https://img.shields.io/badge/python-3.10%2B-111111?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/works%20with-5%20agents-111111?style=flat-square" alt="Works with 5 agents">
  <img src="https://img.shields.io/badge/license-CC%20BY%204.0-111111?style=flat-square" alt="CC BY 4.0">
</p>

<p align="center">
  <strong>Plan first &middot; every citation registered &middot; every number from your data &middot; gates before submission</strong><br>
  <sub>A medical-manuscript workflow for AI agents: Claude Code, Codex, Antigravity, opencode and Muse share one verification engine.</sub>
</p>

<p align="center">
  <sub><a href="README.ko.md">한국어</a> &middot; <a href="README.ja.md">日本語</a> &middot; <a href="README.zh.md">中文</a></sub>
</p>

---

You know him. The senior author in every good lab. Reads the draft with a pen in hand. Circles a sentence and asks, quietly, *"Which paper says that?"* Circles a number: *"Which table?"* Nothing leaves the lab until he signs it.

ManuWright puts him inside your AI agent.

## Before / after

You ask your agent to write the Results section before the plan is settled.

Without ManuWright, it writes fluent prose, cites a plausible paper that does not exist, and rounds a mean it never read.

With ManuWright:

```text
BLOCKED by workflow gate (Rule 8): drafts/draft_plan.md has not been approved.
Create the draft plan first, get author approval, then draft sections.
```

And once the plan is approved, every claim has to survive the checkers:

```text
$ manuwright citations drafts/03_introduction.md
GATE FAIL
citation: EVID:smith_2021
reason: citation id not found in knowledge/evidence.md

$ manuwright numbers drafts/05_results.md
GATE FAIL
number: 54.3
reason: number not found in results CSV files
```

## How it works

```text
 evidence.md   ┐
 results/*.csv ┼──▶ approved plan ──▶ draft ──▶ gates ──▶ QC ×3 ──▶ signed build
 style spec    ┘                                  ├ citations
                          ▲                       ├ numbers
                    hooks block                   └ semantic review (independent)
                    writes without it
```

| Guarantee | Enforced by |
|---|---|
| No section before an approved draft plan; no analysis code before an approved analysis plan | Agent hooks (Claude Code, Codex) and `manuwright verify` |
| Every `[EVID:id]` exists in `knowledge/evidence.md` with a verified source | `manuwright citations` |
| Every reported number exists in `results/*.csv` | `manuwright numbers` and result bindings |
| Reviews go stale when a source, plan or the engine changes | sha256 snapshots in every receipt |
| Submission needs human signoff, AI-use disclosure and a completed checklist | `manuwright verify --profile submission` |
| Prose reads like a high-impact clinical journal, not like a chatbot | Academic writing mode: style cards at every draft, prose checks after every edit (`strict` blocks) |

The engine never invents approvals or reviews. It records decisions that humans made.

## Academic writing mode

The agent writes in the register of medical journals from the first draft, not in chatbot prose. The targets were measured from 33 openly licensed original articles in JAMA Surgery, JAMA Network Open, Lancet, BMJ and Nature, published 2019 to 2022, before generative AI. Only the numbers ship (`docs/academic_style/reference_profile.json`); the papers stay off GitHub. For example, "used" appeared 345 times against "utilized" once, and delve, underscore and "plays a crucial role" never appeared.

You use it from the chat:

| Say | What happens |
|---|---|
| "write the Introduction", "rewrite the Discussion" | The agent loads that section's card (moves, phrasebank, model paragraphs, measured targets) and writes |
| "fix them" | After every edit the prose findings appear; the agent fixes them. *MUST FIX* is AI register; *consider* is a suggestion you may keep |
| "learn my style from this folder" | Measures 3 or more good papers (yours or the target journal's) and adds their style to every card |
| "learn from my edits" | Proposes rules from how you edited the drafts; only the rules you approve are enforced |
| "check for overclaiming", "recheck my references" | Wording stronger than the evidence; retracted papers and wrong DOIs |
| "academic mode strict" / "off" / "on" | `strict` blocks AI-register sentences; the default `academic` reports them; `off` stops both |

It works only inside a paper folder. Rewrites never change the facts: `manuwright style preserve` fails if a citation, number, *p* value or Table/Figure reference moved. Walkthrough: [manual, section 6](docs/manual.md#6-academic-writing-mode).

**What you teach it stays.** Say "from now on use *used*, not *utilized*", "remember: Spine wants a capital P" or "add Dr Kim as a co-author" and the agent saves it in your personal library (`~/.manuwright/library`: wording rules, notes, team profile), adding without overwriting. Every new paper starts with it, and a paper you already started pulls the new items when you open a session. Rules you approve from your own edits go there too. "Sync my library" runs `manuwright library sync --pull` (or `--push` to send a paper's rules up).

## Install

Two ways, one engine. Pick one.

**A. Template (no install).** Clone the repository and write inside it. Claude Code picks up `.claude/`; Codex and Gemini read `AGENTS.md` and `GEMINI.md`.

```sh
git clone https://github.com/grotyx/Academic_writing_c_claudecode my-paper
```

**B. Installed engine.** One CLI for all your papers, plus adapters for each agent.

```sh
uv tool install manuwright
# or: pip install manuwright  |  a pinned tag: uv tool install git+https://github.com/grotyx/Academic_writing_c_claudecode@v1.10.8
manuwright agents install --dry-run     # preview, then run without --dry-run
manuwright setup                        # picks the main model and reviewers for you; updates, Obsidian
manuwright init my-paper
manuwright target                      # inside the paper: target journal + Word style
```

| Agent | What `manuwright agents install` adds | Plan-first enforcement |
|---|---|---|
| Claude Code | plugin `manuwright@manuwright`: skills + hooks | hook blocks the write |
| Codex | plugin `manuwright@manuwright`: skills + hooks (trust once) | hook blocks `apply_patch` |
| Antigravity (`agy`) | plugin with skills | `manuwright verify` |
| opencode | skills in `~/.config/opencode/skills` | `manuwright verify` |
| Muse | user skills | `manuwright verify` |

**Update.** `manuwright update` installs the newest release and then refreshes the agent adapters (`manuwright agents update`; skip with `--no-agents`), then updates the agent rules of every registered paper without asking (`manuwright init --refresh-rules --all --auto`; only unedited AGENTS/CLAUDE/GEMINI.md copies that ManuWright wrote change, .bak kept; a file you wrote or edited is left alone, as is a paper that pins another engine version). A paper folder you open in Claude Code or Codex also updates its own rules at session start, so nothing is missed on Windows or for papers not yet registered. `manuwright check` shows in one screen whether everything is current (version, each agent's plugin, main model, OpenRouter key, auto-update, paper rules) and the command that fixes each ✗. Opt in to automatic patch updates with `manuwright config set auto-update on`: it checks once a day and never applies an update that would invalidate a paper's current review. On Windows (uv install) Windows cannot replace the running `manuwright.exe`, so `manuwright update` opens a PowerShell window that waits until ManuWright has closed, installs the new version and refreshes the agent adapters and paper rules; if no window can open, it prints the same steps as one line (`uv tool install --force ...; if ($?) { manuwright agents update; manuwright init --refresh-rules --all --auto }`) to paste into a new PowerShell window. Template users: `git pull`, or see the [migration guide](docs/migration_guide.md).

**Uninstall.** `claude plugin uninstall manuwright@manuwright`, `codex plugin remove manuwright@manuwright`, `agy plugin uninstall manuwright`, `muse skills uninstall manuwright`, then `uv tool uninstall manuwright`.

## Commands

| Command | What it does |
|---|---|
| `manuwright init [folder]` | Start a paper folder: manifest, plan templates (unapproved), evidence registry, agent rules |
| `manuwright rules [keyword]` | Print the workflow rules, or one section |
| `manuwright check` | One report: version, agent plugins, main model, key, auto-update, papers to refresh, each with its fix |
| `manuwright mode academic\|strict\|off` | Academic writing mode: style cards + prose checks after each edit; `strict` blocks writes with AI-register prose |
| `manuwright style learn <papers>` / `style card <section>` | Measure a corpus of good papers (your style, landmark, target journal) / print a section's style card |
| `manuwright bind [--write]` | Propose result bindings: each number tied to its results CSV cell; the table context and numbers found in several cells come from `review/bindings_overrides.json`, never guessed |
| `manuwright track-changes OLD.md NEW.md -o OUT.docx` | The revision as a Word tracked-changes file (`"tracked_baseline"` makes `build` write it) |
| `manuwright figure SPEC.json [--check]` | Draw a forest, bar or line figure from a results CSV, with a provenance file; `verify` fails a figure whose CSV, spec, style or image changed |
| `manuwright disclose [--check]` | Propose AI-use wording from the `ai_usage` record (declaration before the references, Methods sentences, caption notes) and check the record |
| `manuwright claim-strength drafts` | Flag cited sentences worded more strongly than the evidence's `Claim Strength` (speculative, observed, supported, strong) |
| `manuwright search audit` | Re-check every evidence.md entry against PubMed: weighted title/author/year/journal match, DOI mismatch, retractions, expressions of concern, errata |
| `manuwright blind-review packet` / `check` | Revision re-review with the response letter withheld until the verdicts are recorded (no persuasion by the letter) |
| `manuwright journal fit [journal]` / `suggest` | Before submitting: does the paper fit this journal (its PubMed record on the topic, word and reference limits, a review by that journal's editor), or which journals publish similar work; `journal list --build` makes your list of top-half journals in your field (detected from your references, or set with `--preset`/`--category`), on your computer |
| `manuwright style edits <ai> <edited>` / `--apply` | Learn rules from how you edited AI drafts; only the rules you tick reach `Style/terminology.md` |
| `manuwright library term` / `note` / `sync [--pull\|--push]` | Keep a wording rule or a lesson across papers; bring a paper and your library in step (additions only) |
| `manuwright guide [name ...]` | List the engine guides the rules cite (`docs/<name>.md`), or print them |
| `manuwright verify --project project.json --profile draft\|revision\|submission` | Run every check for that stage |
| `manuwright citations \| numbers \| abstract \| crossrefs \| lint ...` | Run one checker on one file |
| `manuwright gate` / `verify-all` | Check a phase-gate ledger against live checkers |
| `manuwright search "<query>"` | Search PubMed and print evidence entries |
| `manuwright packet` / `build` | Local review packet / gated DOCX build |
| `manuwright update`, `agents install\|update`, `config` | Releases, agent adapters, auto-update, main model and reviewer models |
| `manuwright obsidian status\|connect`, `evidence import-obsidian <citekey>` | Optional, recommended: connect the Obsidian "[Academic Paper Citation Manager](https://github.com/grotyx/rag-obsidian)" library to every agent; bring a vault reference into `evidence.md` |

In Claude Code the template also ships slash commands: `/verify`, `/search-evidence`, `/import-doi`, `/style-pass`, `/verify-claims`, `/suggest-citation`, `/cite-stance`, `/evidence-table`, `/paper-debate`, `/critical-review`, `/editor-review`.

## Your Obsidian library (optional, recommended)

Keep your references in Obsidian with **[Academic Paper Citation Manager](https://github.com/grotyx/rag-obsidian)**, a plugin by the same author ([Obsidian Community plugins](https://community.obsidian.md/plugins/academic-paper-citation-manager)): PubMed import, AI summaries, MeSH tags and `[@citekey]` citations, with your notes as the database. Its MCP server lets every agent search that library while it writes.

```sh
manuwright obsidian install          # plugin into a vault, offers MCP access (skip if installed)
manuwright obsidian connect          # register its MCP server (rag-obsidian) with each agent
manuwright evidence import-obsidian <citekey>
```

The vault is for discovery; only `knowledge/evidence.md` is citable. An imported note brings its CSL fields as the citation and the plugin's AI summary as the summary fields, is cited as `[EVID:<citekey>]`, and stays `abstract-only` until someone reads the full text. Keep Obsidian open with MCP access on while agents use it. Walkthrough: [manual, section 3b](docs/manual.md#3b-your-obsidian-library-optional-recommended).

<p align="center"><img src="docs/images/manual/43_obsidian_import_evidence.png" width="720" alt="Importing a reference from the Obsidian library into evidence.md"></p>

## The workflow

| Phase | You and the agent | Gate |
|---|---|---|
| 1 Setup | Topic, journal, study design; register references | sources verified in `evidence.md` |
| 2 Analysis | Analysis plan, scripts, results CSV, tables | plan approved before any script |
| 3 Draft plan | Key message, claim-to-citation map, outline | plan approved before any section |
| 4 Draft | Methods, Results, Introduction, Discussion, Conclusion, Abstract | citation, number, logic, constraint checks per section |
| 5 Style | Journal style from your own exemplar | measurable style metrics |
| 6 QC | At least 3 rounds; checklist (CONSORT, STROBE, PRISMA, CARE) | recorded in `review/qc_log.md` |
| 7 Finalize | DOCX manuscript, title page, tables | submission profile PASS + human signoff |
| 8 Revision | Response letter, revised sections | every change claim and every reviewer comment checked |

Full rules: [WORKFLOW.md](WORKFLOW.md). Everything that used to live in this README (features, project structure, document list): [docs/guide/overview.md](docs/guide/overview.md).

## FAQ

**Does it write the paper for me?** It helps an agent draft inside your rules. You decide the message, approve the plans, and sign off. Human and co-author review stay mandatory.

**Does anything leave my machine?** Checks run locally. Sending text to another model (external review, PubMed search) happens only when you run those commands.

**Where do my real manuscripts go?** In a private folder or repository, never in a public clone of this template. `manuwright init` creates one.

**Why "ManuWright"?** Manuscript + *wright*, an old word for a maker: playwright, shipwright. Someone who builds manuscripts carefully.

## Documentation

[User manual](docs/manual.md) &middot; [Harness guide](docs/harness_guide.md) &middot; [Workflow reference](docs/workflow_reference.md) &middot; [Verification protocol](docs/verification_protocol.md) &middot; [Writing guide](docs/writing_guide.md) &middot; [QC guide](docs/qc_guide.md) &middot; [Distribution design](docs/distribution_plan.md) &middot; [Changelog](CHANGELOG.md)

## Author

**Professor Sang-Min Park, M.D., Ph.D.**, Department of Orthopaedic Surgery, Seoul National University Bundang Hospital, Seoul National University College of Medicine. <https://sangmin.me/>

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Copyright (c) 2026 Sang-Min Park, Seoul National University Bundang Hospital. Share and adapt for any purpose with attribution. Full text: [LICENSE](LICENSE). To cite ManuWright, use [CITATION.cff](CITATION.cff) (GitHub "Cite this repository").
