# Education Agent Skills Library

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-1.0-blue)](https://agentskills.io)
[![Skills](https://img.shields.io/badge/skills-165-blue)](https://github.com/GarethManning/education-agent-skills)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Last Commit](https://img.shields.io/github/last-commit/GarethManning/education-agent-skills)](https://github.com/GarethManning/education-agent-skills/commits/main)

An open-source library of 165 evidence-based pedagogical skills across 20 domains — works in Claude Code, Claude.ai (via MCP), OpenAI Codex, and Hermes Agent, and is engineered for AI agent orchestration. Domains 1–19 are teacher and designer-facing. Domain 20 is the first student-facing domain: live AI interaction patterns that shape how AI responds to learners during study sessions.

> [!IMPORTANT]
> **Hosted MCP access now requires an auth token.**
>
> The library is still free and open source, and local/plugin/manual use remains the recommended free path. The hosted MCP server is still available for people who specifically need a remote MCP endpoint, but anonymous access is now blocked so the service stays sustainable.
>
> **Need hosted MCP?** [Request an access token](https://docs.google.com/forms/d/e/1FAIpQLSdW1EdcmtjSPPq68Hx-bdth5hO2KNyjhAwEV9Ld0EwWL1Gr8Q/viewform) or [jump to hosted MCP setup](#mcp-server).

---

## Get Started

Works with Claude, Codex, Hermes Agent, and any tool that supports the Agent Skills standard.

For sustainable free use, install or copy the skills locally from GitHub where possible. The hosted MCP server is a convenience endpoint for remote clients, not a requirement for using the library.

### Claude

**CoWork (easiest)** — go to **Customize → (+) Add Plugin** and paste:

```
https://github.com/GarethManning/education-agent-skills
```

**Claude Code CLI** — install from the repo URL:

```bash
claude plugin install https://github.com/GarethManning/education-agent-skills
```

**Claude.ai / Claude Desktop (hosted MCP)** — use only if your workflow specifically needs a remote MCP connector. Hosted access requires a token:

```text
https://mcp-server-sigma-sooty.vercel.app/mcp
```

Request a token here: [Hosted MCP access signup](https://docs.google.com/forms/d/e/1FAIpQLSdW1EdcmtjSPPq68Hx-bdth5hO2KNyjhAwEV9Ld0EwWL1Gr8Q/viewform). Free local and manual options remain available. See [Hosted MCP access](docs/HOSTED_MCP_ACCESS.md).

### OpenAI Codex

Codex does **not** need the hosted MCP server. Recommended local setup:

```bash
git clone https://github.com/GarethManning/education-agent-skills.git
cd education-agent-skills
codex plugin marketplace add "$PWD"
```

The repository includes a Codex plugin manifest at `.codex-plugin/plugin.json` pointing to `./skills/`, plus a local marketplace helper at `.agents/plugins/marketplace.json`. After installing/enabling the local plugin, restart Codex.

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

If you want intelligent skill discovery and recommendation rather than local/offline installs, use the hosted MCP server's `find_skills` and `suggest_skills` tools. The MCP route and the Hermes tap serve different adopter types; a separate Hermes plugin is not currently planned.

Full Hermes guide: [docs/HERMES.md](docs/HERMES.md).

### Any Agent Skills-compatible tool

Copy skill folders from `skills/` into your agent's skills directory. Each skill is a folder containing `SKILL.md` with name/description frontmatter — no dependencies, no build step.

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
YAML schemas, typed inputs and outputs, chaining metadata, [live MCP server](#mcp-server).

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

Claude runs the **Backwards Design Unit Planner**, the **Spaced Practice Scheduler**, and the **Retrieval Practice Generator** in parallel. In under 90 seconds you get a complete lesson-by-lesson plan with spaced retrieval built in, evidence-grounded sequencing, and ready-to-use formative assessment activities — all calibrated to the timeline and topic list you provided.

### Without the plugin (manual)

No API key. No technical setup. No dependencies.

1. Open any skill file in the repository (under `skills/`)
2. Copy the prompt block
3. Paste it into any AI and fill in the fields for your class or context

**Example:** Open `skills/memory-learning-science/spaced-practice-scheduler/SKILL.md` and provide:

- Topics: Cell structure, Cell transport, Cell division, Enzymes, Biological molecules
- Timeline: 8-week term, starting 3 February
- Lessons per week: 3

Claude returns a complete week-by-week schedule showing when to teach new content and when to revisit previous topics at expanding intervals — with specific retrieval activities for each review slot. The schedule follows Cepeda et al.'s (2006) meta-analysis on optimal spacing intervals, includes interleaving across topics, and comes with practical guidance on what to do when review reveals gaps.

---

## What Makes This Different

**Evidence is the filter — including knowing what to exclude.**
Every skill is grounded in named research: specific authors, specific studies, specific findings. Frameworks that lack empirical support — including learning styles, VAK, and other widely-circulated but poorly-evidenced approaches — are not included. The library documents exactly what was excluded and why in [EXCLUSIONS.md](docs/EXCLUSIONS.md). For any school or faculty trying to separate evidence from convention, that document is worth reading on its own.

**Evidence strength is rated transparently.**

| Rating | What it means |
|--------|--------------|
| **Strong** | Multiple meta-analyses or systematic reviews with consistent findings |
| **Moderate** | Solid experimental evidence with some contextual variation |
| **Emerging** | Promising research base with limited replication or practitioner translation |
| **Original** | Practitioner framework; clearly labelled, not claimed as research-backed |

Where original frameworks are included (Domain 14), they are labelled honestly. One important limitation: the skills encode research-grounded prompts, but the prompts themselves have not been empirically validated as AI interventions. That work is ongoing.

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

## Architecture

This library is Layer 1 of a three-layer system. For the full design — including the Context Engine (Layer 2) and Orchestrator (Layer 3) — see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

### For developers: the YAML schema

Every skill opens with a machine-readable YAML header including skill ID, domain, evidence strength, evidence sources, typed input/output schemas, chaining metadata, and tags. See any skill file under `skills/` for the full format, or [ARCHITECTURE.md](docs/ARCHITECTURE.md) for the schema reference.

### MCP Server

The skill library is available as a live MCP server for clients that specifically need remote discovery or programmatic access.

**Production URL:** `https://mcp-server-sigma-sooty.vercel.app/mcp`

Important: the hosted MCP server is a convenience endpoint, not the only way to use the library. If you can install the skills locally, prefer the free local options in [Get Started](#get-started).

Hosted MCP access now requires a unique auth token. Request one here: [Hosted MCP access signup](https://docs.google.com/forms/d/e/1FAIpQLSdW1EdcmtjSPPq68Hx-bdth5hO2KNyjhAwEV9Ld0EwWL1Gr8Q/viewform). Gareth's Agent normally emails the MCP URL, token, and short setup instructions within a few minutes. See [Hosted MCP access](docs/HOSTED_MCP_ACCESS.md) for details.

Connect from Claude.ai by adding the URL under **Integrations > MCP Servers**. Connect from Claude Desktop:

```json
{
  "mcpServers": {
    "education-skills": {
      "type": "streamable-http",
      "url": "https://mcp-server-sigma-sooty.vercel.app/mcp",
      "headers": {
        "Authorization": "Bearer <paste access token here>"
      }
    }
  }
}
```

The server exposes:
- **169 tools** (165 skills + 4 discovery tools: `list_skills`, `find_skills`, `suggest_skills`, `get_skill_details`)
- **165 prompts** (for clients that surface MCP prompts)

Source code, local setup, and development instructions: [`mcp-server/`](mcp-server/)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for inclusion criteria. The standard is high intentionally — every skill must be grounded in named evidence, honestly rated, and practically useful. The library's value depends on its rigour.

### Workflow for adding or revising a skill

After creating or editing a `SKILL.md`, run these steps before committing:

```bash
# 1. Regenerate the registry
python3 scripts/generate-registry.py

# 2. Rebuild the MCP server bundle — required after every skill addition or revision
cd mcp-server && npm run bundle-skills && cd ..

# 3. Stage both generated files alongside the skill
git add skills/<domain>/<skill-name>/SKILL.md registry.json mcp-server/src/skills.json
```

**Why the bundle step matters:** the MCP server running on Vercel does not read `SKILL.md` files at deploy time. It serves a pre-built snapshot at `mcp-server/src/skills.json`. If you add or revise a skill without rebuilding the bundle and committing the result, the change will not appear in the live server — even after a Vercel redeploy. CI will catch this and fail the build.

---

## Credit

Built by [Gareth Manning](https://substack.com/@garethmanning) — educator, curriculum designer, and learning systems designer. 20 years of international education experience across 27 countries.

## Licence

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Open. Forkable. Share alike.
