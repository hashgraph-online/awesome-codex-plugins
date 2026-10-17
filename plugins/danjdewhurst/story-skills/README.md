<a id="readme-top"></a>

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/hero-dark.svg">
  <img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/hero-light.svg" alt="Story Skills" width="560">
</picture>

<p><b>Plan, track, and draft fiction in markdown,<br>with a continuity checker that catches mistakes before readers do.</b></p>

<p>
  <a href="https://www.npmjs.com/package/story-skills"><img src="https://img.shields.io/npm/v/story-skills?style=flat-square&color=7c3aed&label=npm" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/story-skills"><img src="https://img.shields.io/npm/dm/story-skills?style=flat-square&color=7c3aed&label=downloads" alt="npm downloads a month"></a>
  <a href="https://github.com/danjdewhurst/story-skills/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/danjdewhurst/story-skills/ci.yml?branch=main&style=flat-square&label=CI" alt="CI status"></a>
  <a href="docs/getting-started.md#install-the-story-cli"><img src="https://img.shields.io/node/v/story-skills?style=flat-square&color=7c3aed" alt="Node version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-7c3aed?style=flat-square" alt="MIT license"></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/danjdewhurst/story-skills"><img src="https://img.shields.io/ossf-scorecard/github.com/danjdewhurst/story-skills?style=flat-square&label=OpenSSF%20Scorecard" alt="OpenSSF Scorecard"></a>
  <a href="https://github.com/danjdewhurst/story-skills/stargazers"><img src="https://img.shields.io/github/stars/danjdewhurst/story-skills?style=flat-square&color=7c3aed" alt="GitHub stars"></a>
</p>

<p>
  <a href="#quick-start"><b>Quick start</b></a>
  &nbsp;·&nbsp;
  <a href="#the-continuity-engine"><b>Continuity engine</b></a>
  &nbsp;·&nbsp;
  <a href="#skills"><b>Skills</b></a>
  &nbsp;·&nbsp;
  <a href="#companion-cli"><b>CLI</b></a>
  &nbsp;·&nbsp;
  <a href="#examples"><b>Examples</b></a>
  &nbsp;·&nbsp;
  <a href="docs/README.md"><b>Docs</b></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/danjdewhurst/story-skills/blob/main/CONTRIBUTING.md"><b>Contributing</b></a>
</p>

<br>

<img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/demo.gif" alt="story continuity flags a character who died in chapter 2 but appears in chapter 4, a payoff that lands before its setup, and a question resolved before it is asked" width="900">

</div>

<br>

Story Skills gives agents a shared project format for fiction: the story bible, characters, worldbuilding, plot arcs, scenes, continuity state, promises and payoffs, and chapter drafts. Everything is plain markdown with YAML frontmatter, packaged as Agent Skills and as Codex and Claude Code plugins.

The companion `story` CLI treats the story bible as a checkable contract. Its continuity engine finds dead characters who reappear, payoffs that land before their setup, and stale story state, before a reader does. Read [why it works this way](https://ddewhurst.com/blog/story-skills-continuity-compiler-for-ai-fiction/).

<table>
  <tr>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-markdown.svg" width="40" height="40" alt=""></p>
      <p><b>Plain markdown</b><br>
      Every character, place, scene, and chapter is a markdown file with YAML frontmatter. Diff it, branch it, and open it in any editor.</p>
    </td>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-skills.svg" width="40" height="40" alt=""></p>
      <p><b>24 skills, premise to print</b><br>
      From testing a spark of an idea to the query letter and the print interior, in Claude Code, Codex, or any agent that reads <code>SKILL.md</code>.</p>
    </td>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-continuity.svg" width="40" height="40" alt=""></p>
      <p><b>A continuity compiler</b><br>
      Deaths, promises, open questions, and object and knowledge state live in frontmatter, so contradictions show up like type errors.</p>
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-languages.svg" width="40" height="40" alt=""></p>
      <p><b>Any language</b><br>
      Write in any language and script. Builds set right-to-left scripts and vertical Chinese, Japanese, and Korean text.</p>
    </td>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-builds.svg" width="40" height="40" alt=""></p>
      <p><b>Builds for every reader</b><br>
      EPUB, DOCX, a Shunn manuscript, a print interior, an HTML review copy, a screenplay, and Twine and ink, all from one project.</p>
    </td>
    <td width="33%" valign="top">
      <p><img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/icon-pull-requests.svg" width="40" height="40" alt=""></p>
      <p><b>A book by pull request</b><br>
      GitHub Actions templates draft the next chapter on a schedule and fail a pull request that breaks continuity.</p>
    </td>
  </tr>
</table>

## Quick start

> **Writing in claude.ai without a terminal?** [Writers: start here](docs/writers-start-here.md) shows how to upload a skill as a zip.

**Claude Code.** Type these inside a Claude Code session, not a shell:

```shell
/plugin marketplace add danjdewhurst/story-skills
/plugin install story-skills@story-skills
```

**Codex**

```shell
codex plugin marketplace add danjdewhurst/story-skills
codex plugin add story-skills@story-skills
```

**Any other agent that supports `SKILL.md`** can use the Agent Skills CLI:

```shell
npx skills add danjdewhurst/story-skills   # or: bunx skills add danjdewhurst/story-skills
```

Then ask your agent to **"Start a new story"**.

- [Install the skills](docs/getting-started.md#install-the-skills) covers the other agents, including GitHub Copilot, Cursor, Windsurf, Gemini CLI, and OpenCode.
- [Let your agent install it](docs/getting-started.md#let-your-agent-install-it) has a prompt that installs the skills for you.
- New to Story Skills? [Getting started](docs/getting-started.md) walks through a first session. The [documentation index](docs/README.md) links every guide.

## The continuity engine

Language models are weak at long-range consistency, and prompting does not fix that. Story Skills makes it deterministic. Character deaths, promises and payoffs, open questions, scene casts, and object and knowledge state live in frontmatter. `story continuity` reports contradictions the way a compiler reports type errors.

[`examples/the-unraveled-thread/`](examples/the-unraveled-thread/) is a deliberately broken mystery. Every file is well formed, so it passes `story validate` and `story links`, but the story does not hold together:

<!-- replay exit=1 -->
```text
$ story continuity examples/the-unraveled-thread
Continuity check failed: 4 errors, 3 warnings, 0 dismissed
error: chapters/chapter-04.md lists edran-vale, who died in chapter-02; move posthumous appearances to mentions
error: continuity/promises/the-broken-compass.md pays off in chapter-02 before it is planted in chapter-03
error: continuity/questions/who-burned-the-mill.md resolves in chapter-02 before it is introduced in chapter-03
error: continuity/state.md knowledge-state[0] references missing chapter chapter-05
warning: chapters/chapter-03.md POV character nessa-thorn is not listed in characters [pov-not-in-cast]
warning: continuity/promises/the-sealed-letter.md was planted in chapter-01, 3 chapters ago, and has no payoff yet [promise-unpaid]
warning: continuity/state.md object-state[0] status active conflicts with worldbuilding/artifacts/vales-compass.md status destroyed [state-status-conflict]
```

Each finding names its file and reproduces exactly, and CI asserts this output on every commit. Intentional flashbacks and posthumous appearances stay legal through the chapter `mentions` field. Findings listed in `continuity/exemptions.md` are reported as dismissed. `story doctor` and `story next` turn the same checks into repair actions.

## Skills

Most books move through the skills roughly in this order. `research`, `scene-craft`, `voice-style`, `verse-craft`, and `editorial-review` are used whenever they are needed rather than at one fixed point. `story-maintenance` runs underneath all of them, and `series-continuity` starts the next book. The [Skills catalogue](docs/skills.md) has the full details and how the skills hand work to each other.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/skills-dark.svg">
    <img src="https://raw.githubusercontent.com/danjdewhurst/story-skills/main/assets/readme/skills-light.svg" alt="The skills in five stages: set up, plan, draft, revise, and send it out. series-continuity loops back to start the next book, and story-maintenance runs the CLI checks under every stage." width="100%">
  </picture>
</p>

The table lists the skills in the same order, with what each one does and a request that starts it.

| Skill | Try saying |
|-------|------------|
| **premise-workshop**<br>Tests a spark as a premise, then hands off to `story init` | *"Is there a novel in this idea?"* |
| **story-init**<br>Scaffolds the story bible, folders, and registries | *"Start a new story"* |
| **character-management**<br>Builds character profiles, relationships, and arcs | *"Create a character"* |
| **worldbuilding**<br>Builds locations, systems, factions, and invented terms | *"Design a magic system"* |
| **plot-structure**<br>Plans arcs with three-act, hero's journey, Save the Cat, and other structures | *"Create a plot arc"* |
| **theme-craft**<br>Finds the controlling idea, the moral argument, and the motifs | *"What's my story really about?"* |
| **genre-craft**<br>Checks genre conventions, such as mystery fair play, romance beats, and horror | *"Plan a fair-play mystery"* |
| **research**<br>Checks the real-world facts a story relies on, with sources and confidence | *"Fact-check the sailing in chapter 4"* |
| **chapter-writing**<br>Drafts chapters from an outline and the story context | *"Write the next chapter"* |
| **discovery-drafting**<br>Drafts from a story kernel, then reconciles the bible after each chapter | *"I want to discovery-write"* |
| **scene-craft**<br>Checks scene structure, dialogue, POV, and chapter openings | *"Does this chapter breathe?"* |
| **voice-style**<br>Keeps the style sheet: spellings, dialogue punctuation, and character voices | *"Set up a style sheet for this book"* |
| **verse-craft**<br>Writes and scans verse, with stresses and rhyme schemes shown | *"Does this limerick scan?"* |
| **interactive-fiction**<br>Plans branching books: choice graphs, endings, and Twine and ink builds | *"Plan where the branches rejoin"* |
| **revision-continuity**<br>Revises drafts and audits continuity and character state | *"Continuity-check chapter 3"* |
| **line-editing**<br>Edits lines with a reason for each change, and checks that character voices differ | *"Line edit chapter 3. Everyone sounds the same."* |
| **reader-panel**<br>Runs simulated persona reads before human readers see a chapter | *"Give me a simulated beta read of chapters 1 to 5"* |
| **feedback-triage**<br>Turns alpha and beta reader feedback into a revision plan | *"Triage the beta feedback"* |
| **editorial-review**<br>Handles sensitivity reads, permissions, the AI-use statement, and editor rounds | *"I'm quoting a song lyric as my epigraph. What do I need?"* |
| **submission**<br>Checks submission readiness and drafts the query letter, synopsis, and comp titles | *"Help me query agents"* |
| **publishing**<br>Self-publishing production: retailer metadata, ISBNs, EPUB and print interiors, and pricing | *"Get my book ready for KDP and IngramSpark in 6x9"* |
| **adaptation**<br>Carries the story into audiobook, screenplay, picture-book, comics, and translated editions | *"Make a narration script so I can audition narrators"* |
| **series-continuity**<br>Starts sequels and prequels, and checks shared canon across books | *"Start a prequel to The Last Ember"* |
| **story-maintenance**<br>Runs the deterministic CLI checks: validation, continuity, reports, and exports | *"Validate my story project"* |

**line-editing** owns the prose pass. For general writing checks as well, add [**better-writing**](https://github.com/forjd/better-writing) with `npx skills add forjd/better-writing`.

## Companion CLI

The optional `story` CLI handles deterministic project maintenance, and the skills handle the creative work. The CLI needs Node 18 or newer and has no runtime dependencies:

```shell
npx story-skills --help
npm install -g story-skills   # then: story --help (Windows too)
```

Without Node, install the standalone binary with Homebrew on macOS or Linux. Releases after 0.17.0 also attach a binary for macOS, Linux, and Windows to the [releases page](https://github.com/danjdewhurst/story-skills/releases):

```shell
brew install danjdewhurst/tap/story-skills   # then: story --help
```

Check a downloaded archive against the release's checksums file before you run it. [Getting started](docs/getting-started.md#install-the-story-cli) covers every install route, the checksum steps, and running the CLI from a clone.

These are the commands writers use most:

| Command | Purpose |
|---------|---------|
| `story init "The Last Ember"` | Scaffold a story project |
| `story import draft.md --title "The Lost Coast"` | Split an existing manuscript into a project and list its recurring names |
| `story add character "Sera Voss"` | Create a file for a character, place, scene, promise, clue, or other entity |
| `story rename character sera-voss "Sera Vale"` | Rename an entity and update its references in frontmatter and links |
| `story check [path] --strict` | Run validation, link checks, and continuity in one scan; `--strict` also fails on warnings |
| `story list chapters --where status=draft` | List the entities whose frontmatter matches a filter |
| `story wordcount [path] --write` | Count chapter words and update the chapter registry |
| `story next [path]` | Recommend the next writing or maintenance action |
| `story knowledge sera-voss --at chapter-03` | Show what a character knew at a chapter |
| `story context chapter-03 --budget 6000` | Pack the drafting context for a chapter into a token budget |
| `story prose [path]` | Lint prose for filter words, adverbs, and style-sheet spellings |
| `story progress [path] --log` | Report words against targets and the deadline |
| `story export [path] --out dist/manuscript.md` | Combine front matter, chapters, and back matter into one manuscript |
| `story build [path] --format epub` | Build an EPUB with the cover, publishing metadata, and accessibility metadata |
| `story build [path] --format html` | Build a review copy whose paragraphs carry anchors such as `ch03-p12` |

Other build formats are `markdown`, `docx`, `shunn`, `print` (a paged HTML interior for Paged.js, WeasyPrint, or Prince, or a PDF with `--pdf`), `narration`, `codex`, `metadata`, `fountain`, `twee`, and `ink`. The [CLI reference](docs/cli-reference.md) lists every command and option.

The CLI only maintains the project. Agents write story content to markdown files and never create project-local build or generator scripts.

## Import an existing manuscript

Most writers start with a draft, not a blank page. `story import` builds a project from one:

```shell
story import draft.md --title "The Lost Coast" --genre mystery
story import brouillon.md --title "La Côte perdue" --language fr
```

It splits the manuscript on chapter headings, or imports a folder of chapter files, and builds the full project with word counts and registries. [Import, export, and builds](docs/manuscripts.md#import-an-existing-manuscript) covers the options, including `--force`.

## How it works

Every story element is a markdown file with YAML frontmatter. The skills cross-reference those files to keep the project consistent.

- **`story.md`** is the bible that every skill reads. Its `schema-version: 2` field lets the CLI reject incompatible formats.
- Entity files use **kebab-case identifiers**, such as `sera-voss` or `chapter-01`. The CLI takes the id from the name, and transliterates Cyrillic and Greek names. A name in a script with no transliteration, such as `李明`, needs an id from `story add --id`. Names themselves can use any script.
- **`_index.md`** files are the registries for each domain.
- Relationships are **bidirectional**.
- Scene records and continuity state keep character knowledge, object ownership, and setups and payoffs in files, so they carry over between sessions.

<details>
<summary><b>The project layout that <code>story-init</code> creates</b></summary>

```
my-story/
├── story.md                  # Story bible: title, genre, themes, POV, tense
├── style-sheet.md            # Voice, house spellings, and watch words
├── characters/
│   └── _index.md             # Character registry
├── worldbuilding/
│   ├── _index.md             # World overview
│   ├── locations/
│   ├── systems/
│   ├── factions/
│   └── artifacts/
├── plot/
│   ├── _index.md             # Arc overview
│   ├── arcs/
│   └── timeline.md
├── scenes/
│   └── _index.md             # Machine-readable scene registry
├── continuity/
│   ├── state.md              # Character, object, and knowledge state
│   ├── questions/
│   │   └── _index.md
│   ├── promises/
│   │   └── _index.md
│   └── clues/
│       └── _index.md
├── glossary/
│   ├── _index.md
│   └── terms/
└── chapters/
    └── _index.md             # Chapter registry
```

</details>

Some files appear only when needed: `matter/` for front and back matter, `research/` for research notes, `progress.md` for the session log, and `continuity/exemptions.md` for dismissed findings. The [Project format reference](docs/project-format.md) and [`schemas/story.schema.json`](schemas/story.schema.json) define the contract.

## Examples

Complete books made with Story Skills:

- [**The Cormorant Tide**](https://github.com/danjdewhurst/the-cormorant-tide)
- [**Pippa and the Borrowed Star**](https://github.com/danjdewhurst/christmas-childrens-story), a children's Christmas story

Example projects in this repository:

<table>
<tr>
<td width="50%" valign="top">

**[the-last-ember](examples/the-last-ember/)**<br>
A fantasy with a magic system, a plot arc with foreshadowing, and a drafted chapter

</td>
<td width="50%" valign="top">

**[the-fall-of-the-citadel](examples/the-fall-of-the-citadel/)**<br>
A prequel to The Last Ember, linked with `series`. Run `story series examples/the-last-ember` for the chronology

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[harbor-of-second-light](examples/harbor-of-second-light/)**<br>
A near-future mystery with memory technology and populated continuity state

</td>
<td width="50%" valign="top">

**[the-gull-rock-light](examples/the-gull-rock-light/)**<br>
A short branching story, built to Twine and ink

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[bo-and-the-missing-moon](examples/bo-and-the-missing-moon/)**<br>
A 32-page picture book with spread briefs

</td>
<td width="50%" valign="top">

**[the-left-luggage-office](examples/the-left-luggage-office/)**<br>
A weekly serial with episode questions and cliffhangers

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[salt-and-lantern](examples/salt-and-lantern/)**<br>
An anthology of three stories by different writers

</td>
<td width="50%" valign="top">

**[the-unraveled-thread](examples/the-unraveled-thread/)**<br>
A deliberately broken project that shows the continuity findings

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[quatre-heures-dix-sept](examples/quatre-heures-dix-sept/)**<br>
A short story in French

</td>
<td width="50%" valign="top">

**[kirimi-eki-no-wasuremono](examples/kirimi-eki-no-wasuremono/)**<br>
A short story in Japanese, set in vertical columns

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[laysat-lil-bay](examples/laysat-lil-bay/)**<br>
A short story in Arabic, built right to left

</td>
<td width="50%" valign="top"></td>
</tr>
</table>

[Writing in other languages](docs/languages.md) covers what works in each language and script.

## Write a book with pull requests

A story project with deterministic checks is one an agent can advance unattended. The [`templates/github/`](templates/github/) workflows turn a story repository into a self-drafting book:

- [`story-checks.yml`](templates/github/story-checks.yml) runs `story check` and `story report --actionable` on every push to `main` and every pull request, so a chapter PR with a continuity contradiction fails its checks. Mark the `story-checks` job as a required status check to block the merge.
- [`draft-next-chapter.yml`](templates/github/draft-next-chapter.yml) runs [Claude Code](https://github.com/anthropics/claude-code-action) on a schedule. It drafts the next chapter within word, turn, and spend budgets, then opens a pull request for review. The agent cannot push.
- [`review-copy.yml`](templates/github/review-copy.yml) publishes an HTML review copy to GitHub Pages, and [`manuscript-note.yml`](templates/github/ISSUE_TEMPLATE/manuscript-note.yml) gives readers an issue form for notes on exact paragraphs.

Copy the workflows into `.github/workflows/`, add an `ANTHROPIC_API_KEY` secret for the drafting workflow, and set **Settings > Pages > Source** to GitHub Actions for the review copy. GitHub Pages sites are public unless your plan supports private Pages. For a private manuscript, see [keeping the manuscript private](docs/automation.md#keeping-the-manuscript-private). [Automation and CI](docs/automation.md) covers the rest, including the note form's label.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](https://github.com/danjdewhurst/story-skills/blob/main/CONTRIBUTING.md) and the [Code of Conduct](https://github.com/danjdewhurst/story-skills/blob/main/CODE_OF_CONDUCT.md). User-visible changes are listed in the [changelog](CHANGELOG.md). The [development guide](docs/development.md) covers the repository layout, the CLI, tests, and releases.

```shell
bun install
bun run test
bun run check:metadata
```

The `evals/` harness regression-tests the writing skills against seeded briefs and known traps. See [`evals/README.md`](https://github.com/danjdewhurst/story-skills/blob/main/evals/README.md).

<a href="https://star-history.com/#danjdewhurst/story-skills&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=danjdewhurst/story-skills&type=Date&theme=dark">
    <img src="https://api.star-history.com/svg?repos=danjdewhurst/story-skills&type=Date" alt="Star history of danjdewhurst/story-skills" width="600">
  </picture>
</a>

## License

Story Skills is released under the [MIT License](LICENSE).

<div align="center">
<br>
<sub><a href="#readme-top">Back to top</a></sub>
</div>
