# Education Agent Skills Library

[![Skills](https://img.shields.io/badge/skills-165-blue)](https://github.com/GarethManning/education-agent-skills)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Last Commit](https://img.shields.io/github/last-commit/GarethManning/education-agent-skills)](https://github.com/GarethManning/education-agent-skills/commits/main)

An independent open-source library of **165 education skills across 20 domains**: practical instructions that help AI agents support lesson planning, assessment, curriculum design and learning. It brings named research and clearly labelled original practitioner frameworks into reusable workflows, with limitations and educator judgement built in. Domains 1–19 support teachers and designers; Domain 20 contains **13 student-facing skills** for study interactions.

The library uses [Agent Skills](https://agentskills.io/home), the open format originally developed by Anthropic and adopted across an open ecosystem. Each skill is a folder with a named and described `SKILL.md`, instructions and optional supporting resources. Existing Claude/plugin and MCP integrations use the rich source files; a generated portable edition passes the official format validator. See [standards and verification](#agent-skills-format-and-verification) for exactly what was checked and [skill quality](docs/SKILL_QUALITY.md) for the educational review approach. Format compatibility is not certification of teaching effectiveness.

**22 October 2026 — v3.1.0:** The library now has a portable edition checked against the official Agent Skills reference tool, 37 targeted educational revisions and eight guides with reorganized optional examples. Skill IDs and interfaces stay stable. [Read the update and its limits](docs/releases/v3.1.0.md).

The library-operated public MCP service was retired with this release; public signup is no longer offered. Use the [portable download](https://github.com/GarethManning/education-agent-skills/releases/download/v3.1.0/education-agent-skills-portable-v3.1.0.zip), source plugins, manual prompts or local/self-hosted MCP below. Existing remote-only clients need a supported local route or an endpoint they operate; migration is not automatic.

---

## Get Started

Start with the [v3.1.0 GitHub release](https://github.com/GarethManning/education-agent-skills/releases/tag/v3.1.0), choose a local integration for Claude, Codex or Hermes, or copy the portable edition into another compatible client. Client versions and activation behaviour vary; the [verification receipt](docs/audits/agent-skills-build-verification-2026-10-22.md) records the tested limits.

Local skill files need no library-operated service. MCP users can [run locally over stdio or operate their own hosted endpoint](mcp-server/README.md).

### Claude

**CoWork** — the repository URL for plugin import is:

```
https://github.com/GarethManning/education-agent-skills
```

**Claude Code** — for 2.1.275+ use the command recommended by the tested 2.1.307 validator:

```text
/plugin install education-agent-skills --marketplace GarethManning/education-agent-skills
```

Claude 2.1.307 passed local manifest validation with advisory warnings; installation and session activation were not tested. For older clients without this syntax, use manual prompt copying below or follow that client's local-plugin instructions; repository-URL CLI installation is not established by this check.

**Claude Desktop (local MCP)** — follow the [local stdio setup](mcp-server/README.md#run-locally-stdio). For a client that only accepts remote MCP, operate your own authenticated endpoint using the [self-hosting guide](mcp-server/README.md#self-hosted-http). The former public connector and signup are no longer supported; its credentials do not automatically transfer to your endpoint.

### OpenAI Codex

Codex does **not** need the hosted MCP server. Recommended local setup:

```bash
git clone https://github.com/GarethManning/education-agent-skills.git
cd education-agent-skills
codex plugin marketplace add "$PWD"
codex plugin add education-agent-skills@education-agent-skills
codex plugin list --marketplace education-agent-skills --json
```

The manifests list all 20 domain directories. Registration and installation are separate steps. Codex CLI 0.163.0-alpha.11.1 passed isolated registration, installation and listing with 165 source skills and their resources; actual model activation and desktop refresh were not tested. Start a new session after installation; see the full guide for refresh and cache updates.

For one or two individual skills, copy them into your global Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -r skills/<domain>/<skill-name> ~/.codex/skills/
```

Example:

```bash
cp -r skills/memory-learning-science/spaced-practice-scheduler ~/.codex/skills/
```

Full Codex guide: [docs/CODEX.md](docs/CODEX.md).

### Hermes Agent

Hermes users should keep this repository as the canonical source, then install only the skills they actually need locally.

```bash
hermes skills tap add GarethManning/education-agent-skills
hermes skills install \
  GarethManning/education-agent-skills/skills/original-frameworks/learning-target-authoring-guide \
  --category education --yes
```

Recommended starting point: install selected skills or a small starter pack rather than all 165 skills. That keeps your local Hermes index useful instead of noisy.

Hermes v0.18.0 (2026.7.1) listed all 165 portable skills and read selected main files, metadata and a moved example in an isolated local profile. Hub installation, updates and model invocation were not tested in that check.

If you want intelligent skill discovery and recommendation rather than local/offline installs, run local/self-hosted MCP and use its `find_skills` and `suggest_skills` tools. The MCP route and the Hermes tap serve different adopter types; a separate Hermes plugin is not currently planned.

Full Hermes guide: [docs/HERMES.md](docs/HERMES.md).

### Any Agent Skills-compatible tool

Download the [portable ZIP](https://github.com/GarethManning/education-agent-skills/releases/download/v3.1.0/education-agent-skills-portable-v3.1.0.zip) and extract it: `agent-skills/` contains 165 skill folders, accompanied by an installation note. For clients requiring strict standard frontmatter, copy from `agent-skills/<skill-name>/`. Maintainers can instead generate the same profile at `dist/agent-skills/` using the [isolated Python setup](docs/AGENT_SKILLS.md#generate-the-portable-edition). Copy the complete selected folder into your client's skills directory, preserving `references/`, `agents/` and other included files. Using the copied skills needs no Python or Node build. Check the client's discovery path and invocation controls; generic clients may ignore vendor policy files.

### Manual (no setup)

1. Open any skill file in the repository (under `skills/`)
2. Copy the prompt block
3. Paste it into any AI and fill in the fields for your class or context

---

## Feedback & Contributions

I'd love to hear your thoughts. If you have suggestions, find bugs, or want to contribute:

- Email: gareth.manning@gmail.com
- X: https://x.com/worldteacherman
- LinkedIn: https://www.linkedin.com/in/gareth-manning-a404b387/
- Open a Pull Request or Issue on GitHub

---

**I'm an educator — [start here](#try-it-now)**
No setup required. Use the plugin, a local skill install, or manual copy-paste and start teaching.

**I'm a developer or AI builder — [start here](#architecture)**
YAML schemas, typed inputs and outputs, chaining metadata, [local/self-hosted MCP](#mcp-server).

---

## Who This Is For

- **Classroom teachers** who want evidence-based lesson and assessment design without hours of research
- **University lecturers and professors** who received little or no teacher training and want practical, research-grounded support for their teaching
- **Curriculum designers and heads of learning** building programmes, units, and assessments
- **School leaders in innovative and alternative education contexts** — international schools, Montessori, project-based, democratic and nature-based schools
- **Innovators reimagining education** — people building new school models, alternative programmes, and next-generation learning environments. Evidence-based constraints don't limit creative redesign of education; they deepen it.
- **EdTech developers and AI builders** who need a structured, programmatically accessible education knowledge layer
- **Education researchers** interested in how evidence translates into AI-mediated practice

---

## Why This Exists

AI is arriving in education fast. Whether it improves learning outcomes or simply scales mediocre practice depends almost entirely on what it is built on.

Most AI education tools are built on convention, habit, and assumption — on what educators have always done, rather than on what the research says actually works. Learning styles. Rigid lesson structures. Wellbeing programmes disconnected from learning theory. As AI expands in education, so does the risk of scaling ineffective practice.

This library exists to build something different: a credible, rigorous foundation for AI in education. One that is anchored in named research, honest about its limitations, and designed especially for the educators working at the frontier — building the next generation of schools, not optimising existing ones.

The potential is real. Personalised, evidence-grounded learning support at a scale that was never previously possible. But only if what is powering it is the actual evidence.

The benefit is not only personalised learning. It is teaching quality and workload. An educator who would otherwise spend hours researching, designing, and second-guessing gets structured, evidence-grounded support in minutes — which means more time for the parts of teaching that only a human can do.

That is one use case. The same library can power school-wide curriculum audits, personalised professional development pathways for teachers, or orchestrated end-of-term assessment reviews. The skills are the foundation. The architecture below describes the layers that make this possible.

---

## Try It Now

### With a runtime install (recommended)

Install the skills in Claude, Codex, or Hermes, then tell your agent what you need in plain language. The relevant skills can be selected automatically or searched locally.

**Example:** Say *"I'm planning a Year 9 science unit on cells — 6 weeks, 3 lessons a week."*

An agent could combine the **Backwards Design Unit Planner**, the **Spaced Practice Scheduler**, and the **Retrieval Practice Generator** to draft a lesson plan with spaced retrieval and formative assessment activities for educator review. This is an illustrative workflow, not a measured multi-agent run or a 90-second performance guarantee.

### Without the plugin (manual)

No API key. No technical setup. No dependencies.

1. Open any skill file in the repository (under `skills/`)
2. Copy the prompt block
3. Paste it into any AI and fill in the fields for your class or context

**Example:** Open `skills/memory-learning-science/spaced-practice-scheduler/SKILL.md` and provide:

- Topics: Cell structure, Cell transport, Cell division, Enzymes, Biological molecules
- Timeline: 8-week term, starting 3 February
- Lessons per week: 3

Claude returns a complete week-by-week schedule showing when to teach new content and when to revisit previous topics at expanding intervals — with specific retrieval activities for each review slot. Expanding intervals are a practical scheduling heuristic informed by spacing research, including Cepeda et al. (2006), rather than that meta-analysis's exact optimum for this class. Review timing should respond to the retention goal and learner evidence; the skill also offers guidance when review reveals gaps.

---

## What Makes This Different

**Evidence is the filter — including knowing what to exclude.**
Research-grounded skills cite named authors, studies and findings; original practitioner frameworks distinguish their own methods from the research they draw on. Frameworks that lack empirical support — including learning styles, VAK, and other widely-circulated but poorly-evidenced approaches — are not included. The library documents exactly what was excluded and why in [EXCLUSIONS.md](docs/EXCLUSIONS.md). For any school or faculty trying to separate evidence from convention, that document is worth reading on its own.

**Evidence strength is rated transparently.**

| Rating | What it means |
|--------|--------------|
| **Strong** | Multiple meta-analyses or systematic reviews with consistent findings |
| **Moderate** | Solid experimental evidence with some contextual variation |
| **Emerging** | Promising research base with limited replication or practitioner translation |
| **Original** | Practitioner framework; clearly labelled, not claimed as research-backed |

Original frameworks are grouped in Domain 15 and labelled honestly. Existing metadata also records practitioner and legacy evidence labels; these have not been silently mapped to new ratings. The prompts themselves have not been empirically validated as AI interventions. The [quality guide](docs/SKILL_QUALITY.md) explains the review criteria and remaining research limits.

**Built by an educator with 20 years of international school experience.**
The pedagogical judgements embedded in every prompt, every output structure, and every known-limitations section reflect real classroom and curriculum design practice — not a reading of the literature.

**Designed for orchestration from day one.**
YAML schema headers, typed input and output fields, chaining metadata, and composable outputs are built into every skill. This is not a prompt collection with metadata bolted on. It is a skill library engineered for programmatic use.

---

## The 20 Domains

> **Note on Domain 20:** Domains 1–19 are teacher and designer-facing — they generate plans, rubrics, scaffolds, and assessments. Domain 20 is different: these skills run live during a student's study session, shaping how AI responds to a learner in real time. The governing principle is the same across all 20 domains — evidence-grounded — but the user, the output, and the invocation pattern are all different. See [Domain 20 skills](skills/student-learning/) for details.

| # | Domain | Skills | Focus |
|---|--------|--------|-------|
| 1 | **Memory & Learning Science** | 8 | Retrieval practice, spacing, interleaving, cognitive load, dual coding, elaborative interrogation, feedback |
| 2 | **Self-Regulated Learning & Metacognition** | 5 | Self-regulation scaffolds, metacognitive prompts, goal-setting, study strategy selection, error analysis |
| 3 | **Explicit & Direct Instruction** | 5 | Gradual release sequences, checking for understanding, lesson openings, think-alouds, practice design |
| 4 | **Questioning, Discussion & Dialogue** | 5 | Socratic questioning, discussion protocols, dialogic teaching moves, hinge questions |
| 5 | **Literacy, Writing & Critical Thinking** | 7 | Argument structure, disciplinary writing, reading comprehension, source evaluation, text complexity, media literacy, critical thinking |
| 6 | **EAL/D & Language Development** | 5 | Language demand analysis, vocabulary tiering, scaffolded task modification, sentence frames, sheltered instruction |
| 7 | **Curriculum Design & Assessment** | 13 | Backwards design, competency unpacking, rubric generation, assessment validity, formative assessment, differentiation, gap analysis, learning progressions, PBL, threshold concept translation |
| 8 | **Wellbeing, Motivation & Student Agency** | 12 | Motivation diagnostics, self-efficacy, wellbeing-learning connections, agency scaffolds, belonging, and related practices |
| 9 | **Professional Learning & Teacher Development** | 10 | Lesson observation, reflective practice, PD session design, data interpretation, and related practices |
| 10 | **Global & Cross-Cultural Pedagogies** | 9 | Variation theory, CPA sequences, phenomenon-based learning, culturally responsive teaching, Ubuntu, place-based inquiry, Reggio documentation, emergent projects, cross-cultural validity |
| 11 | **Environmental & Experiential Learning** | 6 | Outdoor learning, biophilic design, ecological inquiry, experiential learning cycles, interdisciplinary connections, service learning |
| 12 | **AI Learning Science** | 14 | Adaptive hints, erroneous examples, digital worked examples, spacing algorithms, AI feedback, tutoring dialogue, learning analytics, collaborative learning, cognitive tutoring, self-explanation, metacognitive monitoring, productive failure, worked example transitions, formative assessment loops |
| 13 | **AI Literacy** | 7 | AI output auditing, hallucination fact-checking, prompt literacy, expertise interrogation, learning boundary mapping, AI Socratic dialogue, disciplinary AI reliability |
| 14 | **Montessori & Alternative Evidence-Based Approaches** | 4 | Three-part lessons, prepared environment design, mixed-age learning, uninterrupted work cycles |
| 15 | **Original Frameworks** | 17 | SEEDS regenerative inquiry, H3Uni systems methods (scoping, Three Horizons, dilemma navigation, multi-perspective decision wheel), developmental band systems, learning target authoring, rubric logic, self-determined project design, dispositional assessment, single-point rubrics; composite orchestrators (assessment design, inclusive design, place-based curriculum, regenerative project design, compassionate systems awareness) |
| 16 | **Curriculum Alignment** | 4 | Coverage audit, KUD chart authoring, developmental band translation, scope and sequence |
| 17 | **Historical Thinking** | 10 | Sourcing, close reading, contextualisation, corroboration, document-based lesson design, document set curation, source adaptation, strategy modelling, assessment design, central question evaluation |
| 18 | **Systems Thinking** | 8 | Systems awareness iceberg, aspirational iceberg, hexagon complexity mapper, leverage and response design, mental model mapper, agency circles for systems action, ladder of inference, systems wellbeing impact |
| 19 | **Inclusive Design** | 3 | UDL lesson auditing, options design across engagement/representation/action, proactive barrier anticipation before delivery |
| 20 | **Student-Facing Learning Skills** *(new)* | 13 | Retrieve-first gate, explain-first interrogator, progressive hint ladder, confidence calibration check, stuck & error diagnosis coach, AI claim checker, transfer bridge, teach-back evaluator, productive failure protocol, SRL session wrapper, unassisted evidence checkpoint, weekly agency review, fading manager |

---

## Agent Skills format and verification

Two views serve different clients:

- **Canonical source:** `skills/<domain>/<skill-name>/` retains typed education schemas, evidence metadata and vendor options for the existing plugins and MCP adapter. Its extended frontmatter is not claimed to pass the strict official validator.
- **Portable edition:** `dist/agent-skills/<skill-name>/` uses standard frontmatter, preserves the source body, and stores complete original metadata in `references/education.json`. Complete folders include the licence and local resources/policies.

The [22 October 2026 local verification](docs/audits/agent-skills-build-verification-2026-10-22.md) records **165/165 portable skills passing `skills-ref` 0.1.0** and all 165 included by its prompt generator, pinned to upstream commit `69ef37e9424c0a7ea9dd2293b559e43ec8176379`. This is point-in-time compatibility with the [official specification](https://agentskills.io/specification), not foundation certification, a specification version called “1.0” or “v2”, or proof of model adherence or learner outcomes. No hosted update is implied by these local checks.

For developers: [format, export and version details](docs/AGENT_SKILLS.md). For educators and contributors: [quality criteria and limits](docs/SKILL_QUALITY.md).

---

## Architecture

This repository implements the skill library and MCP adapter. The Context Engine (Layer 2) and Orchestrator (Layer 3) are architectural proposals, not implemented services here. For the design, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

### For developers: the YAML schema

Every skill opens with a machine-readable YAML header including skill ID, domain, evidence strength, evidence sources, typed input/output schemas, chaining metadata, and tags. See any skill file under `skills/` for the full format, or [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the schema reference.

### MCP Server

The MCP source supports local stdio and self-hosted Streamable HTTP. The library-operated public endpoint is retiring with v3.1.0; no public access signup is offered. See [migration options](docs/HOSTED_MCP_ACCESS.md).

For local MCP, build from the source checkout and configure your client to launch it over stdio. No Vercel, access token or email-provider configuration is required. Clients restricted to remote connectors need an endpoint they operate and configure with their own origin and authentication. [Setup instructions](mcp-server/README.md) cover both routes.

The server exposes:
- **157 tools** (153 model-invocable skills + 4 discovery tools: `list_skills`, `find_skills`, `suggest_skills`, `get_skill_details`)
- **165 prompts** (all skills, including the 12 marked `disable-model-invocation: true`, remain available for explicit prompt use)

Source code, local setup, and development instructions: [`mcp-server/`](mcp-server/)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for inclusion criteria. The standard is high intentionally — every skill must be grounded in named evidence, honestly rated, and practically useful. The library's value depends on its rigour.

### Workflow for adding or revising a skill

Edit the canonical skill and its resources, then regenerate `registry.json` and `mcp-server/src/skills.json`. Generate and validate the portable edition separately; generated distribution folders stay ignored. The [contributor guide](CONTRIBUTING.md#validation-before-a-pull-request) gives dependency setup, exact checks and files to include. Updating a clone does not necessarily refresh an installed plugin cache or copied skill; follow the client update instructions. A rebuilt local MCP snapshot is not a hosted release.

---

## Credit

Built by [Gareth Manning](https://substack.com/@garethmanning) — educator, curriculum designer, and learning systems designer. 20 years of international education experience across 27 countries.

## Licence

The educational skills, documentation, examples, and curriculum materials in this repository are licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Open. Forkable. Share alike. See the [LICENSE](LICENSE) file for the repository-level notice and full legal terms.
