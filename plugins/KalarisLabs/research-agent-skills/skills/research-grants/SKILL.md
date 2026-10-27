---
name: research-grants
description: Guides writing of competitive research grant proposals for NSF, NIH, DOE, DARPA, and Taiwan NSTC. Covers agency-specific formatting and review criteria, specific aims, project descriptions, significance and innovation narratives, broader impacts, budgets and justifications, timelines, biosketches, and the NSTC CM03 form. Use when drafting a proposal for one of these agencies. Use when writing specific aims or broader impacts statements. Use when preparing a budget justification or milestone plan. Use when responding to a solicitation, BAA, or reviewer comments in a resubmission. Use when checking a draft against page limits and submission requirements. For general manuscript writing, use a scientific writing skill instead.
license: MIT
compatibility: Works in Agent Skills-compatible hosts. Grant-writing guidance needs no network; optional figures via the scientific-schematics skill require OPENROUTER_API_KEY and outbound API access.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.3'
  category: research-writing
  maintainer: Kalaris Labs
  tags: grant writing, NIH, NSF, research proposals, funding
---

# Research Grant Writing

## Overview

Research grant writing is the process of developing competitive funding proposals for federal agencies and foundations. Master agency-specific requirements, review criteria, narrative structure, budget preparation, and compliance for NSF (National Science Foundation), NIH (National Institutes of Health), DOE (Department of Energy), DARPA (Defense Advanced Research Projects Agency), and Taiwan's NSTC (National Science and Technology Council) submissions.

**Critical Principle: Grants are persuasive documents that must simultaneously demonstrate scientific rigor, innovation, feasibility, and broader impact.** Each agency has distinct priorities, review criteria, formatting requirements, and strategic goals that must be addressed.

## When to Use This Skill

This skill should be used when:
- Writing research proposals for NSF, NIH, DOE, DARPA, or NSTC programs
- Preparing project descriptions, specific aims, or technical narratives
- Developing broader impacts or significance statements
- Creating research timelines and milestone plans
- Preparing budget justifications and personnel allocation plans
- Responding to program solicitations or funding announcements
- Addressing reviewer comments in resubmissions
- Planning multi-institutional collaborative proposals
- Writing preliminary data or feasibility sections
- Preparing biosketches, CVs, or facilities descriptions

## Visual Enhancement (Optional)

Strong proposals often include 1–3 figures (timelines, workflow diagrams, preliminary data). Figures support review but are not a substitute for clear aims and methods.

**When figures help:**
- Research methodology and workflow diagrams
- Project timeline or Gantt charts
- Conceptual framework or system architecture (technical proposals)
- Experimental design flowcharts
- Broader impacts activity diagrams
- NSTC CM03 research architecture diagrams (often expected)

**How to create figures:**
- **Preferred:** Use the **scientific-schematics** skill (`--doc-type grant`) for AI-generated diagrams from a natural-language description
- **Alternative:** Build figures in your usual tools (matplotlib, Illustrator, PowerPoint, etc.)

Run from the repository root, with `OPENROUTER_API_KEY` set:

```bash
python skills/scientific-schematics/scripts/generate_schematic.py "project timeline with Year 1-3 milestones" -o figures/timeline.png --doc-type grant
```

**Disclosure:** AI schematic generation sends your prompt to [OpenRouter](https://openrouter.ai/) (a third-party API). Do not include unpublished sensitive details unless that transmission is appropriate for your project.

---

## Agency-Specific Overview

### NSF (National Science Foundation)
**Mission**: Promote the progress of science and advance national health, prosperity, and welfare

**Key Features**:
- Follow [PAPPG 24-1](https://www.nsf.gov/policies/pappg) (effective May 20, 2024) unless a solicitation overrides it
- Intellectual Merit + Broader Impacts (equally weighted)
- 15-page project description limit (most programs; includes Results from Prior NSF Support, max 5 pages)
- Emphasis on education, diversity, and societal benefit
- Collaborative research encouraged
- Open data and open science emphasis
- Merit review process with panel + ad hoc reviewers

### NIH (National Institutes of Health)
**Mission**: Enhance health, lengthen life, and reduce illness and disability

**Key Features**:
- Specific Aims (1 page) + Research Strategy (12 pages for R01)
- Significance, Innovation, Approach as core review criteria
- Preliminary data typically required for R01s
- Emphasis on rigor, reproducibility, and clinical relevance
- Modular budgets ($250K increments) for most R01s
- Multiple resubmission opportunities

### DOE (Department of Energy)
**Mission**: Ensure America's security and prosperity through energy, environmental, and nuclear challenges

**Key Features**:
- Focus on energy, climate, computational science, basic energy sciences
- Often requires cost sharing or industry partnerships
- Emphasis on national laboratory collaboration
- Strong computational and experimental integration
- Energy innovation and commercialization pathways
- Varies by office (ARPA-E, Office of Science, EERE, etc.)

### DARPA (Defense Advanced Research Projects Agency)
**Mission**: Make pivotal investments in breakthrough technologies for national security

**Key Features**:
- High-risk, high-reward transformative research
- Focus on "DARPA-hard" problems (what if true, who cares)
- Emphasis on prototypes, demonstrations, and transition paths
- Often requires multiple phases (feasibility, development, demonstration)
- Strong project management and milestone tracking
- Teaming and collaboration often required
- Varies dramatically by program manager and BAA (Broad Agency Announcement)

### NSTC (National Science and Technology Council - Taiwan)
**Mission**: Advance scientific breakthrough, industrial application, and societal impact in Taiwan.

**Key Features**:
- **CM03 Form**: The core technical proposal format.
- **Bilingual**: Abstract required in both Chinese and English.
- **Innovation & Feasibility**: Primary review focus.
- **Preliminary Data**: Highly critical for credibility.
- **Research Architecture Diagram**: A mandatory visual element for clarity.

## Core Components of Research Proposals

Section-by-section guidance for every standard proposal component — specific aims,
significance, innovation, approach, preliminary data, timeline, budget and justification,
biosketch, facilities, data management and sharing, and broader impacts — with structure,
length targets, and worked language, is in
[references/core_components.md](references/core_components.md).

## Review Criteria, Writing Principles, and Proposal Types

- [references/review_criteria.md](references/review_criteria.md): how NIH, NSF, DOE, and
  DARPA score proposals, and what each criterion actually rewards.
- [references/writing_principles.md](references/writing_principles.md): what separates
  funded proposals from competent ones — framing, specificity, reviewer psychology, and
  readability.
- [references/proposal_types_and_resubmission.md](references/proposal_types_and_resubmission.md):
  the common proposal types and how to handle a resubmission, including responding to
  a summary statement.

## Common Mistakes to Avoid

### Conceptual Mistakes

1. **Failing to Address Review Criteria**: Not explicitly discussing significance, innovation, approach, etc.
2. **Mismatch with Agency Mission**: Proposing research that doesn't align with agency goals
3. **Unclear Significance**: Failing to articulate why the research matters
4. **Insufficient Innovation**: Incremental work presented as transformative
5. **Vague Objectives**: Goals that are not specific or measurable

### Writing Mistakes

1. **Poor Organization**: Lack of clear structure and flow
2. **Excessive Jargon**: Inaccessible to broader review panel
3. **Verbosity**: Unnecessarily complex or wordy writing
4. **Missing Context**: Assuming reviewers know your field deeply
5. **Inconsistent Terminology**: Using different terms for same concept

### Technical Mistakes

1. **Inadequate Methods**: Insufficient detail to judge feasibility
2. **Overly Ambitious**: Too much proposed for timeline/budget
3. **No Preliminary Data**: For mechanisms requiring demonstrated feasibility
4. **Poor Timeline**: Unrealistic or poorly justified schedule
5. **Misaligned Budget**: Budget doesn't support proposed activities

### Formatting Mistakes

1. **Exceeding Page Limits**: Automatic rejection
2. **Wrong Font or Margins**: Non-compliant formatting
3. **Missing Required Sections**: Incomplete application
4. **Poor Figure Quality**: Illegible or unprofessional figures
5. **Inconsistent Citations**: Formatting errors in references

### Strategic Mistakes

1. **Wrong Program or Mechanism**: Proposing to inappropriate opportunity
2. **Weak Team**: Insufficient expertise or missing key collaborators
3. **No Broader Impacts**: For NSF, failing to adequately address
4. **Ignoring Program Priorities**: Not aligning with current emphasis areas
5. **Late Submission**: Technical issues or rushed preparation

## Workflow for Grant Development

### Phase 1: Planning and Preparation (2-6 months before deadline)

**Activities**:
- Identify appropriate funding opportunities
- Review program announcements and requirements
- Consult with program officers (if appropriate)
- Assemble team and confirm collaborations
- Develop preliminary data (if needed)
- Outline research plan and specific aims
- Review successful proposals (if available)

**Outputs**:
- Selected funding opportunity
- Assembled team with defined roles
- Preliminary outline of specific aims
- Gap analysis of needed preliminary data

### Phase 2: Drafting (2-3 months before deadline)

**Activities**:
- Write specific aims or objectives (start here!)
- Develop project description/research strategy
- Create figures and data visualizations
- Draft timeline and milestones
- Prepare preliminary budget
- Write broader impacts or significance sections
- Request letters of support/collaboration

**Outputs**:
- Complete first draft of narrative sections
- Preliminary budget with justification
- Timeline and management plan
- Requested letters from collaborators

### Phase 3: Internal Review (1-2 months before deadline)

**Activities**:
- Circulate draft to co-investigators
- Seek feedback from colleagues and mentors
- Request institutional review (if required)
- Mock review session (if possible)
- Revise based on feedback
- Refine budget and budget justification

**Outputs**:
- Revised draft incorporating feedback
- Refined budget aligned with revised plan
- Identified weaknesses and mitigation strategies

### Phase 4: Finalization (2-4 weeks before deadline)

**Activities**:
- Final revisions to narrative
- Prepare all required forms and documents
- Finalize budget and budget justification
- Compile biosketches, CVs, and current & pending
- Collect letters of support
- Prepare data management plan (if required)
- Write project summary/abstract
- Proofread all materials

**Outputs**:
- Complete, polished proposal
- All required supplementary documents
- Formatted according to agency requirements

### Phase 5: Submission (1 week before deadline)

**Activities**:
- Institutional review and approval
- Upload to submission portal
- Verify all documents and formatting
- Submit 24-48 hours before deadline
- Confirm successful submission
- Receive confirmation and proposal number

**Outputs**:
- Submitted proposal
- Submission confirmation
- Archived copy of all materials

**Critical Tip**: Never wait until the deadline. Portals crash, files corrupt, and emergencies happen. Aim for 48 hours early.

## Integration with Other Skills

This skill works effectively with:
- **Scientific Schematics**: Optional AI-generated grant figures (`--doc-type grant`)
- **Scientific Writing**: For clear, compelling prose
- **Literature Review**: For comprehensive background sections
- **Peer Review**: For self-assessment before submission
- **Research Lookup**: For finding relevant citations and prior work
- **Data Visualization**: For creating effective figures

## Resources

This skill includes comprehensive reference files covering specific aspects of grant writing:

- `references/nsf_guidelines.md`: NSF-specific requirements, formatting, and strategies
- `references/nih_guidelines.md`: NIH mechanisms, review criteria, and submission requirements
- `references/doe_guidelines.md`: DOE programs, emphasis areas, and application procedures
- `references/darpa_guidelines.md`: DARPA BAAs, program offices, and proposal strategies
- `references/broader_impacts.md`: Strategies for compelling broader impacts statements
- `references/specific_aims_guide.md`: Writing effective specific aims pages
- `references/nstc_guidelines.md`: NSTC-specific guidelines and review criteria

Load these references as needed when working on specific aspects of grant writing.

## Templates and Assets

- `assets/nsf_project_summary_template.md`: NSF project summary structure
- `assets/nih_specific_aims_template.md`: NIH specific aims page template
- `assets/budget_justification_template.md`: Budget justification structure

---

**Final Note**: Grant writing is both an art and a science. Success requires not only excellent research ideas but also clear communication, strategic positioning, and meticulous attention to detail. Start early, seek feedback, and remember that even the best researchers face rejection—persistence and revision are key to funding success.

## Agent operating procedure

1. **Check the environment.** Collect the user's draft, data, figures and target venue before writing anything.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Draft one section or paragraph and confirm tone, structure and terminology with the user.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Every claim traces to the user's data or a verified source; numbers match tables and figures; citations are real (`citation-verification`).
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| A claim has no supporting data or citation | Flag it in the text (e.g. `[citation needed]`) instead of inventing support. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- The user is the author: never add results, references or claims they did not provide or approve.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `venue-templates`: Prepare journal manuscripts, conference papers, research posters, and grant documents using venue-specific formatting guidance and bundled…
- `rebuttal-and-response-to-reviewers`: Plan and write responses to peer review, including journal "response to reviewers" letters for revise-and-resubmit, conference rebuttals un…
- `systems-paper-writing`: Provides paragraph-level structural blueprints for 10-12 page systems papers targeting OSDI, SOSP, ASPLOS, NSDI, and EuroSys.
