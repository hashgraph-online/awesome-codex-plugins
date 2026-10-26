# Third-party notices

The Foundry's own code, commands, tests and docs are MIT-licensed (see `LICENSE`).
Parts of `01_Context_Vault/` are adapted from
open-source projects. Each upstream licence text is reproduced verbatim in
[`licenses/`](./licenses/). Files may have been modified from upstream
(renamed, trimmed, re-voiced); upstream copyright remains with the original authors.

| Upstream | Licence | Copyright holder | Used in this repo |
|---|---|---|---|
| [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | MIT | AgentLand Contributors | 52 agent personas in `01_Context_Vault/Agents/` (design, engineering, marketing, product, project-management, specialized, support, testing, strategy) |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | MIT | Affaan Mustafa | 5 agents in `Agents/specialized/lead-intelligence/` and `Agents/specialized/learning/`; `Protocols/Self_Evaluation/` |
| [blader/humanizer](https://github.com/blader/humanizer) | MIT | Siqi Chen | `Protocols/humanizer-main/` |
| [mattpocock/skills](https://github.com/mattpocock/skills) | MIT | Matt Pocock | `Protocols/grill-me/` |
| [nidhinjs/prompt-master](https://github.com/nidhinjs/prompt-master) | MIT | Nidhin Joseph Nelson | `Intelligence/Prompt_Master/` |
| [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) | MIT | Cathryn Lavery | `Skills/diagram-design/` (its icon sets are credited inside `references/primitive-icons.md`: Tabler MIT, Simple Icons CC0, Devicon MIT, log-z/logos MIT) |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Apache-2.0 | see upstream | `Protocols/caveman/` (Apache-2.0 section 4: licence text included; files may carry modifications) |

## Original or locally adapted (covered by the root MIT licence)

`Agents/marketing/marketing-linkedin-strategist.md`, `Agents/specialized/data-analytics-reporter.md`,
`Agents/specialized/diagram-architect.md`, `Agents/strategy/digital_twin_strategist.md`,
`Methodology/`, `Protocols/` (other than the rows above), `Intelligence/` (other than Prompt Master),
and all of `core/engine/`.

## Modifications to bundled files

Two example snippets had credential-shaped placeholder passwords (`'secure_password'`, `'password123'`)
that secret scanners flag. They now read `process.env.TEST_USER_PASSWORD`:
`Agents/testing/testing-api-tester.md` and `Agents/testing/testing-performance-benchmarker.md`.
No other upstream text was changed for this.

## How this was determined

Upstream was identified by matching file names and frontmatter against each
project's published tree, then confirming each repository's licence through the
GitHub API. Matching by name is strong evidence, not a byte-for-byte audit:
if you are an upstream author and a file here is misattributed or you want it
removed, open an issue and it will be fixed promptly.

A previously bundled `karpathy_rules.md` derived from an unlicensed upstream
and was removed rather than redistributed.
