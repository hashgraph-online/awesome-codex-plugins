---
# AGENT SKILLS STANDARD FIELDS (v2)
name: self-determined-project-design-protocol
description: "Structure a student's self-determined project with mentoring checkpoints, competency alignment, and reflection. Use when guiding student-led projects within a competency-based framework."
disable-model-invocation: true
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "original-frameworks/self-determined-project-design-protocol"
skill_name: "Self-Determined Project Design Protocol"
domain: "original-frameworks"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Manning — Personal project mentoring methodology (original, developed through capstone mentoring and international teaching)"
  - "Zimmerman (2000, 2002) — Self-regulated learning: forethought, performance, self-reflection phases"
  - "Bandura (1997) — Self-efficacy: the exercise of control (feasibility calibration as self-efficacy assessment)"
  - "Ericsson & Pool (2016) — Peak: secrets from the new science of expertise (knowledge/skill acquisition as deliberate practice)"
  - "Black & Wiliam (1998) — Assessment and classroom learning (milestone checkpoints as formative assessment)"
  - "Manning — LT authoring methodology and rubric logic (Domain 14 Skills 98 and 99)"
input_schema:
  required:
    - field: "student_idea"
      type: "string"
      description: "The student's initial project idea — however rough"
    - field: "student_level"
      type: "string"
      description: "Developmental band and age"
    - field: "available_time"
      type: "string"
      description: "Total duration and weekly time commitment"
  optional:
    - field: "existing_curriculum_LTs"
      type: "string"
      description: "Whether curriculum LTs exist for this domain or need to be created"
    - field: "mentor_expertise"
      type: "string"
      description: "How much the educator knows about the project domain"
    - field: "prior_experience"
      type: "string"
      description: "What the student has already done in this area"
output_schema:
  type: "object"
  fields:
    - field: "phase_1_ideation_and_feasibility"
      type: "object"
      description: "Student actions + educator actions — idea articulation, feasibility reality-check, possibility expansion if needed"
    - field: "phase_2_knowledge_gap_analysis"
      type: "object"
      description: "Parallel research by student AND educator — what's required, what the student knows, what they don't, honest readiness assessment"
    - field: "phase_3_planning"
      type: "object"
      description: "LT selection or creation, exemplar analysis, rubric development, knowledge/skill acquisition plan, timeline with milestones, resource and mentor identification, tracking system setup"
    - field: "phase_4_execution_and_monitoring"
      type: "object"
      description: "Weekly rhythm, self-monitoring protocol, milestone check-ins, adaptive replanning"
    - field: "phase_5_completion_and_defence"
      type: "object"
      description: "Final self-assessment against rubric, presentation or defence, honest impact assessment"
    - field: "tracking_system"
      type: "object"
      description: "Specification for the shared visible artefact — document, board, or spreadsheet — that both student and mentor can see at all times. Must show: the plan, the timeline, current status against milestones, and evidence of progress. Tool-agnostic but functional requirements are non-negotiable"
    - field: "educator_feasibility_calibration_guide"
      type: "object"
      description: "Specific questions to determine genuine readiness — what students should be able to explain, what to do when they're not ready"
    - field: "known_limitations"
      type: "object"
      description: "Where the protocol requires the educator to reach outside their expertise; when to bring in external mentors"
chains_well_with:
  - "learning-target-authoring-guide"
  - "coherent-rubric-logic-builder"
  - "developmental-band-system-designer"
  - "self-regulated-learning-designer"
  - "curriculum-knowledge-architecture-designer"
teacher_time: "6 minutes"
tags: ["self-determined", "project", "Manning", "mentoring", "SRL", "Zimmerman", "Bandura", "feasibility", "deliberate-practice", "tracking"]
---

# Self-Determined Project Design Protocol

## What This Skill Does

This skill encodes an original practitioner framework developed by Gareth Manning, educator, curriculum designer, and learning systems designer. Unlike skills in other domains, it is not drawn from peer-reviewed research traditions. It is grounded in serious engagement with learning science, original curriculum design work, and active classroom testing. It is included because the methodology is coherent, transferable, and genuinely useful — and because intellectual honesty requires distinguishing practitioner frameworks from research-validated approaches.

This skill guides both student and educator through the full arc of designing, planning, and executing a self-determined personal project — from initial idea through to completion, defence, and reflection. It specifies what BOTH parties need to do at each phase, how to calibrate ambition honestly, and how to build the knowledge and skill acquisition plan alongside the project itself. The output is a complete dual-perspective protocol: student-facing roadmap and educator-facing mentoring guide, phase by phase. The protocol maps directly to Zimmerman's (2000, 2002) self-regulated learning phases: forethought (Phases 1-3), performance (Phase 4), and self-reflection (Phase 5). Bandura (1997) informs the feasibility calibration: over-ambitious and under-ambitious projects both reflect miscalibrated self-efficacy, and the educator's role is to help students calibrate honestly without crushing agency. Ericsson & Pool (2016) inform the knowledge/skill acquisition plan: the skills a student needs to develop for their project constitute a deliberate practice design problem. The tracking system — a shared, visible artefact that both student and mentor can see at all times — is the structural backbone of the protocol. Without it, mentoring conversations have no shared reference point and project drift is invisible until it's too late.

## Evidence Foundation

Manning developed this protocol through personal project mentoring in multiple international school contexts, most recently through capstone mentoring at REAL School Budapest. The methodology addresses a specific problem: most "independent project" programmes give students freedom without structure — resulting in either teacher-directed projects that aren't really self-determined, or student-led projects that drift, stall, or collapse because the student lacked the self-regulation skills to manage the process. Zimmerman (2000, 2002) provides the theoretical framework for the protocol's phase structure. His self-regulated learning model describes three cyclical phases: forethought (goal-setting, strategic planning, self-efficacy assessment), performance (self-monitoring, strategy use, help-seeking), and self-reflection (self-evaluation, attribution, adaptive responses). The protocol operationalises these phases: Phases 1-3 ARE forethought, Phase 4 IS performance, Phase 5 IS self-reflection. Bandura (1997) informs the feasibility calibration — the most critical and most frequently skipped part of the protocol. Self-efficacy (the student's belief in their ability to succeed) directly predicts effort, persistence, and resilience. But self-efficacy can be miscalibrated: a student who believes they can build an app in 6 weeks with no coding experience has inflated self-efficacy that will lead to demoralising failure. Equally, a student who says "I can't do anything interesting" has deflated self-efficacy that will lead to an uninspired project. The educator's role is to calibrate honestly: probing what the student actually knows, what they need to learn, and whether the timeline is realistic. Over-ambitious equals under-ambitious in terms of harm — a student who fails a project they weren't ready for learns the wrong lesson. Ericsson & Pool (2016) inform the knowledge/skill acquisition plan. The skills a student needs for their project — coding, woodworking, research methods, writing, design — are not acquired by wishing. They require deliberate, structured practice. The protocol builds a parallel skill acquisition plan alongside the project plan: what do you need to learn, how will you learn it, and how will you know when you've learned it? Black & Wiliam (1998) inform the milestone checkpoint design: each checkpoint is a structured formative assessment moment where the student self-assesses against the rubric, shares evidence, gets feedback, and adapts the plan.

## Input Schema

The educator must provide:
- **Student idea:** The initial project idea. *e.g. "I want to build a website for my mum's bakery" / "I want to write and illustrate a children's book about climate change" / "I want to design and build a model bridge that can hold 50kg" / "I want to learn to play guitar and perform at the school concert" / "I don't know what I want to do"*
- **Student level:** Developmental band and age. *e.g. "Band D, age 13" / "Band C, age 11" / "Band B, age 9"*
- **Available time:** Total duration and weekly commitment. *e.g. "One semester (18 weeks), 3 hours per week dedicated project time plus independent work" / "One term (10 weeks), 2 hours per week" / "Full year, 90 minutes per week"*

Optional (injected by context engine if available):
- **Existing curriculum LTs:** Whether LTs exist or need creating
- **Mentor expertise:** How much the educator knows about this domain
- **Prior experience:** What the student has already done

## Prompt

```
You are designing a self-determined project protocol using Gareth Manning's methodology. You must encode this framework PRECISELY as specified. Do not approximate or substitute generic project management language. This protocol is specifically designed for the student-educator relationship in a mentored personal project.

THE FIVE PHASES — encode this sequence precisely:

**Phase 1: Ideation & Feasibility**
Student arrives with an idea. Educator LISTENS without deflating. Four opening questions:
- What do you want to make?
- Who is it for?
- Why does it matter to you?
- What would success look like?

Then the honest feasibility conversation — probing ambition calibration without crushing agency. This is the hardest part of mentoring: being honest about what's possible without killing the motivation that brought the student to you.

**Phase 2: Knowledge Gap Analysis**
PARALLEL research. Student researches what knowledge and skills the project requires. Educator does the same INDEPENDENTLY — this is critical. They meet, compare findings, have an honest conversation. If the student can't explain core concepts when asked directly, that's the data. The educator doesn't lecture — they ask questions: "Can you explain how [X] works?" "What would you do if [Y] happened?" "What's the most difficult part of this project?" If the student can't answer, they're not ready to build. They need to learn first.

Educator brings in an external expert if the domain is outside their knowledge. Pretending to know what you don't know is worse than admitting it and finding someone who does.

**Phase 3: Planning**
Only AFTER feasibility is established:
- Select or create LTs (using the LT Authoring Guide methodology)
- Analyse exemplars — what does good look like in this domain?
- Co-construct success criteria and rubric (using Rubric Logic Builder methodology)
- Design the knowledge/skill acquisition plan — what to learn, how, and by when
- Build the timeline with milestone checkpoints
- Identify mentors or experts
- Set up the shared tracking system

**Phase 4: Execution & Monitoring**
Weekly rhythm: student works on the project. Weekly self-monitoring using the tracking system. Milestone checkpoints at pre-defined intervals: self-assess against rubric, share evidence of progress, get feedback, adapt the plan. The timeline is a living document — it changes as reality intervenes. Break into smaller chunks when the student feels overwhelmed.

**Phase 5: Completion & Defence**
Final self-assessment against the rubric. Presentation or defence — the student explains what they did, why, what they learned, and what they would do differently. Honest reflection: what was achieved, what wasn't, and what was learned about the PROCESS of self-directed work (not just the content).

KEY DISTINCTIONS:
- **Educator researches independently before the feasibility meeting.** The educator's feedback must be AUTHORITATIVE, not just encouraging. "That sounds great!" is not mentoring. "I've looked into this, and here's what I think you need to know..." is mentoring.
- **Knowledge/skill acquisition plan runs IN PARALLEL with the project plan.** You learn what you need AS you build. The two plans are interleaved, not sequential.
- **LTs and rubric BEFORE execution.** Students who understand what excellence looks like BEFORE they begin produce better work than students who discover the criteria at the end.
- **The tracking system is SHARED and VISIBLE to both parties at all times.** It is not a private student document. It is the shared reference point for every mentoring conversation.
- **Over-ambitious equals under-ambitious in terms of harm.** A student who fails a project they weren't ready for learns "I'm not capable" (wrong lesson). A student who coasts through a project they could do in their sleep learns "I don't need to try" (also wrong lesson). Calibration matters.

Your task is to design the protocol for:

**Student idea:** {{student_idea}}
**Student level:** {{student_level}}
**Available time:** {{available_time}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Existing curriculum LTs:** {{existing_curriculum_LTs}} — if not provided, create LTs as part of Phase 3.
**Mentor expertise:** {{mentor_expertise}} — if not provided, assume the educator has general pedagogical expertise but may not be a domain expert.
**Prior experience:** {{prior_experience}} — if not provided, assume this is the student's first self-determined project of this scale.

Return your output in this exact format:

## Self-Determined Project Protocol: [Project Idea]

**Student idea:** [The initial idea]
**Student level:** [Band and age]
**Available time:** [Duration and weekly commitment]
**Protocol overview:** [One sentence — what both parties will do across the five phases]

### Phase 1: Ideation & Feasibility

**Student actions:**
[What the student does — articulating the idea, answering the four questions, engaging honestly with feasibility]

**Educator actions:**
[What the educator does — listening, probing, calibrating without deflating, honest feasibility assessment]

**Feasibility decision:**
[The specific questions and criteria that determine whether the project is feasible in the available time with the student's current capabilities]

### Phase 2: Knowledge Gap Analysis

**Student research:**
[What the student investigates — what knowledge and skills the project requires]

**Educator research (independent):**
[What the educator investigates independently — what they need to know to mentor this project effectively]

**Feasibility meeting:**
[How the meeting works — what each party brings, what questions to ask, what to do if the student isn't ready]

### Phase 3: Planning

[The complete planning phase — LTs, exemplars, rubric, knowledge/skill acquisition plan, timeline, mentors, tracking system]

### Phase 4: Execution & Monitoring

**Weekly rhythm:**
[What happens each week — self-monitoring, work sessions, mentor check-ins]

**Milestone checkpoints:**
[How many, when, and what happens at each one — self-assessment, evidence sharing, feedback, adaptation]

**Adaptive replanning:**
[What to do when the plan needs to change — how to adjust without abandoning the project]

### Phase 5: Completion & Defence

**Final self-assessment:**
[How the student assesses their work against the rubric]

**Presentation or defence:**
[What the student presents, to whom, and what questions they should expect]

**Honest reflection:**
[What was achieved, what wasn't, and what was learned about the process]

### Tracking System Specification

**Purpose:** A shared, visible artefact that both student and mentor can see at all times — the structural backbone of the protocol.

**Functional requirements (non-negotiable):**
[What the tracking system must contain and display — regardless of the tool used]

**Tool options:**
[Tool-agnostic recommendations — this could be a Trello board, Google Doc, spreadsheet, physical wall chart, or dedicated app]

**Update protocol:**
[When and how the tracking system is updated — whose responsibility, at what frequency]

### Educator Feasibility Calibration Guide

[Specific questions to determine genuine readiness. What students should be able to explain. What to do when they're not ready — without crushing motivation.]

### Known Limitations

[Where the protocol requires the educator to reach outside their expertise; when to bring in external mentors; what happens when the student's ambition genuinely exceeds what's achievable]

**Self-check before returning output:** Verify that (a) all five phases are present, (b) the educator researches independently in Phase 2, (c) knowledge/skill acquisition runs parallel to the project, (d) LTs and rubric are created before execution, (e) the tracking system specification is included and complete, (f) feasibility calibration is honest not deflating, and (g) over-ambitious is treated as seriously as under-ambitious.
```

## Example Output

**Scenario:** *Student idea: "I want to write and illustrate a children's book about climate change — aimed at 6-8 year olds, about 20 pages, with hand-drawn illustrations and a simple story that helps kids understand why the planet is getting warmer and what they can do" / Student level: "Band D, age 13" / Available time: "One semester (18 weeks), 3 hours per week dedicated project time plus independent work at home" / Mentor expertise: "English teacher — strong on writing and storytelling, limited knowledge of illustration techniques and climate science" / Prior experience: "The student is a strong writer (has written short stories for English class) and draws in her free time, but has never written for a young audience or combined text and illustration in a structured way"*

---

## Self-Determined Project Protocol: Children's Book on Climate Change

**Student idea:** Write and illustrate a 20-page children's book about climate change for ages 6-8
**Student level:** Band D, age 13
**Available time:** 18 weeks, 3 hours/week + independent work
**Protocol overview:** Student designs and creates a children's book while developing writing, illustration, and communication skills; educator provides structured mentoring through five phases with honest feasibility calibration and a shared tracking system

### Phase 1: Ideation & Feasibility

**Student actions:**
Answer the four questions:
- *What do you want to make?* A 20-page illustrated children's book about climate change for 6-8 year olds.
- *Who is it for?* Young children (6-8) — maybe the Year 1-2 students at our school.
- *Why does it matter to you?* I care about climate change and I think kids should learn about it early, but most climate books are boring or scary. I want to make one that's hopeful.
- *What would success look like?* A finished, bound book that I've read to a class of Year 2 students and they understood the message.

**Educator actions:**
Listen to the full idea without interrupting or deflating. Then probe:
- "Twenty pages is a real commitment. Have you ever written anything that long in a structured format? What was the longest thing you've written?"
- "Writing for 6-year-olds is very different from writing for your own age group. What do you know about how young children read and understand stories?"
- "You said 'hand-drawn illustrations.' That's at least 10-15 original illustrations. How long does a typical drawing take you? Do the maths — is that realistic in 18 weeks alongside the writing?"
- "Climate science for children — how will you make sure the science is accurate without being overwhelming? Where will you get your climate information?"

**Feasibility decision:**
The project is feasible IF: (a) the student is willing to learn about writing for young children (it's a specific skill she doesn't have yet), (b) the page count is adjusted if needed after Phase 2 research, (c) the illustration style is chosen for feasibility (simple watercolour, not detailed realism), and (d) the climate science is fact-checked by someone qualified. The student is a strong writer and draws regularly — the raw capability is there. The challenge is the integration of text and illustration for a young audience, which is a new skill.

### Phase 2: Knowledge Gap Analysis

**Student research (1.5 weeks):**
- Read 5-6 children's picture books aimed at ages 6-8. Analyse: How many words per page? How do text and illustration work together? What makes the story accessible?
- Read 2-3 existing children's books about environmental topics. What works? What's preachy or boring?
- Research climate change basics: What are the most important concepts for a 6-year-old? What can they actually understand?
- Research illustration for children's books: page layout, colour choices, character consistency across pages.

**Educator research (independent, 1 week):**
- Read 3-4 children's picture books — specifically analysing word count per page, sentence structure, and story arc for this age group.
- Research the children's book creation process: what professional children's book authors say about the development process, common mistakes, typical timelines.
- Identify a climate science resource or contact — who could fact-check the science content? (Perhaps a science teacher or a university outreach programme.)
- Identify an illustration resource — who could advise on illustration technique? (Perhaps an art teacher or a local illustrator.)

**Feasibility meeting:**
Both parties share findings. Key questions the educator asks:
- "Based on what you've read, how many words per page do you think your book should have?" (Tests whether she's learned about writing for young children — should be around 20-50 words per page.)
- "What's the single most important climate concept you want a 6-year-old to understand after reading your book?" (Tests whether she can simplify — if she lists 10 concepts, the book will be muddled.)
- "Show me the illustration style you're planning. How long did this drawing take? Now multiply by 15 pages. Does the timeline work?"

If the student can answer these questions with specificity, proceed to Phase 3. If she can't: "You need another week of research. Go read 5 more picture books, and this time, COUNT the words on each page. Then come back and tell me what you learned."

### Phase 3: Planning

**LT selection/creation:**
Two LTs for this project (using the LT Authoring Guide methodology):
- **LT1: Audience-Appropriate Communication.** "I can create a text that communicates a complex idea in language and form appropriate for a specific young audience."
- **LT2: Integrated Design.** "I can design a multi-page product where text, image, and layout work together to communicate a unified message."

**Exemplar analysis:**
Student and educator analyse 2 published children's picture books together, using the rubric criteria: What makes the text work for this age group? How do illustrations add meaning that words don't? Where do text and image contradict or reinforce each other?

**Rubric co-construction:**
Build rubrics for both LTs using the Coherent Rubric Logic Builder (Skill 99). Competent: the book communicates one clear climate concept in age-appropriate language with consistent illustrations that support the text. Extending: the book shows genuine craft — voice, pacing, and illustration choices that go beyond functional competence.

**Knowledge/skill acquisition plan:**
| Skill Needed | Current Level | Learning Plan | Timeline |
|---|---|---|---|
| Writing for young children | Novice | Study 8-10 picture books, draft practice pages, get feedback from Year 2 teacher | Weeks 3-6 |
| Climate science accuracy | Basic | Research 3 reliable sources, create a fact sheet, have it reviewed by science teacher | Weeks 3-5 |
| Illustration for narrative | Intermediate | Choose a style, practise character consistency, create a test spread | Weeks 4-7 |
| Page layout and design | Novice | Study how published books use white space, font size, and image placement | Weeks 5-8 |

**Timeline with milestones:**
- **Milestone 1 (Week 6):** Story outline and 3 sample pages (text + rough illustration) — present to educator
- **Milestone 2 (Week 10):** Complete draft text for all pages + 5 finished illustrations — present to educator and get feedback from Year 2 teacher on accessibility
- **Milestone 3 (Week 14):** Complete book (all pages, text and illustrations) — present to educator and external reviewer
- **Milestone 4 (Week 17):** Final bound book — read to Year 2 class
- **Week 18:** Defence and reflection

**Resource and mentor identification:**
- **Climate science:** Ms. Chen (science teacher) to fact-check the content
- **Illustration technique:** Mr. Okonkwo (art teacher) for one 30-minute consultation on character consistency and colour
- **Young audience testing:** Ms. Patel (Year 2 teacher) to arrange a read-aloud test in Week 12-13

**Tracking system setup:** See Tracking System Specification below.

### Phase 4: Execution & Monitoring

**Weekly rhythm:**
- **Monday (30 min):** Update tracking system — what was accomplished last week, what's planned this week, any blockers.
- **Tuesday-Thursday (2.5 hours):** Dedicated project time — writing, illustrating, or skill acquisition (as specified in the knowledge/skill plan).
- **Friday (optional):** Independent work at home if behind schedule.
- **Bi-weekly mentor meeting (20 min):** Educator reviews tracking system, asks: "Are you on track? What's blocking you? What do you need from me?" Provides feedback on work in progress.

**Milestone checkpoints:**
At each milestone:
1. Student self-assesses against both rubric LTs: "Where am I? Emerging, Developing, Competent, or Extending on each LT?"
2. Student shares EVIDENCE: the specific pages, illustrations, or drafts that demonstrate progress.
3. Educator provides feedback: specific, actionable, linked to the rubric. Not "This is great!" but "Your text is accessible (Competent on LT1) but your illustration on page 4 doesn't support the text — the image shows winter but the text is about heat waves (Developing on LT2). How could you fix that?"
4. Plan adaptation: adjust timeline if needed, add or remove tasks, reprioritise.

**Adaptive replanning:**
If the student falls behind:
- First: identify the cause. Is it skill-related (illustration takes longer than expected), motivation-related (lost interest), or life-related (other school demands)?
- If skill-related: adjust the scope (reduce from 20 pages to 15, simplify illustration style)
- If motivation-related: return to Phase 1 — "Why does this matter to you? Is this still the right project?"
- If life-related: adjust the timeline, protect the quality of the work over the quantity

### Phase 5: Completion & Defence

**Final self-assessment:**
Student completes a final self-assessment against both rubric LTs, with specific evidence cited for each level claimed. "I believe I am Competent on LT1 because my text uses 30-40 words per page, simple sentence structures, and was understood by the Year 2 class when I read it aloud."

**Presentation or defence:**
Student presents the finished book to a panel (educator + one other teacher + one student peer). The panel asks:
- "Why did you choose this topic and this audience?"
- "What was the hardest part of the project? How did you handle it?"
- "What would you do differently if you started again?"
- "Show us one page and explain WHY you made the design choices you did."

**Honest reflection:**
Written reflection addressing:
- What was achieved (a finished book, read to a real audience)
- What wasn't achieved (any planned elements that were cut or compromised)
- What was learned about the CONTENT (climate science, children's literature)
- What was learned about the PROCESS (self-regulation, time management, dealing with setbacks)
- What the student would tell another student starting a similar project

### Tracking System Specification

**Purpose:** A shared, visible artefact that both student and mentor can see at all times. This is the structural backbone of the protocol — without it, mentoring conversations lack a shared reference point, project drift is invisible, and accountability is vague.

**Functional requirements (non-negotiable regardless of tool):**

1. **The Plan:** The complete project plan, including milestones, deadlines, and the knowledge/skill acquisition plan. Visible at a glance — not buried in a document.

2. **The Timeline:** A visual representation of the 18-week schedule showing what should happen when. Must show: past (what was done), present (what's happening now), and future (what's planned). Updated weekly.

3. **Current Status Against Milestones:** For each milestone: is it upcoming, in progress, completed, or overdue? With the date of last update. At a glance, both student and mentor should be able to answer: "Are we on track?"

4. **Evidence of Progress:** A place to attach or link to work-in-progress: draft pages, illustration sketches, feedback received, rubric self-assessments. This is the EVIDENCE that the tracking system points to — not just a timeline but a portfolio of progress.

5. **Blockers and Decisions:** A running log of: what's stuck, what decisions were made and why, what help was requested. This creates a history of the project's evolution.

**Tool options (tool-agnostic — choose based on what the student and school already use):**
- **Trello or similar kanban board:** Columns for each phase. Cards for each task. Checklists within cards. Attachments for evidence. Simple, visual, low barrier.
- **Google Doc:** A single living document with sections for plan, timeline (as a table), status, evidence (embedded images), and blockers log. Low-tech, universally accessible.
- **Spreadsheet:** Timeline in one tab, task tracker in another, evidence log in a third. Good for students who think in tables.
- **Physical wall chart:** A large poster divided into the five phases, with sticky notes for tasks, a timeline drawn across the bottom, and a pocket for evidence. Best for younger students or those who need tangible visual tracking.
- **Dedicated app (if available):** Any project management tool the school uses — provided it meets all five functional requirements above.

**Update protocol:**
- **Student updates the tracking system every Monday** before the week's work begins. This is non-negotiable — it takes 5-10 minutes and is the self-monitoring habit that drives the whole protocol.
- **Educator reviews the tracking system before every mentoring meeting.** They should not need to ASK the student "What have you done?" — the tracking system should tell them.
- **At each milestone checkpoint,** the tracking system is reviewed together and the plan is adapted if needed.

### Educator Feasibility Calibration Guide

**Questions to determine genuine readiness (Phase 1-2):**

| Question | What a Ready Student Says | What an Unready Student Says | What to Do |
|---|---|---|---|
| "What's the single most important thing your reader should understand?" | One clear, specific concept | A long list of everything about climate change | "Choose ONE. The rest can wait for your next book." |
| "How many words per page in a book for 6-year-olds?" | "About 20-50, based on the books I studied" | "I don't know" or "A few hundred?" | "You haven't done your research yet. Go read 5 picture books and count." |
| "Show me a drawing in the style you plan to use. How long did it take?" | Shows a drawing, knows the time | "I haven't tried yet" | "Try one this week. Time yourself. Then we can plan realistically." |
| "What will you do if you run out of time?" | "I could reduce the page count or simplify the illustrations" | "I'll just work harder" | "Working harder isn't a plan. Let's identify what could be cut without losing the core." |

**When the student isn't ready:**
Do NOT say "This project is too hard for you." DO say: "You have a great idea and the capability to do this. You're not ready YET — here's what you need to do first: [specific research, specific skill practice, specific expert consultation]. Let's meet again in [time] when you've done that."

### Known Limitations

1. **The educator may not be a domain expert.** This protocol requires the educator to research the project domain independently (Phase 2), but a language arts teacher mentoring a coding project or a science teacher mentoring a music composition has real knowledge limitations. The protocol addresses this by requiring external expert identification — but finding the right expert takes time and may not always be possible. When in doubt, the educator should be honest: "I don't know enough about this to give you expert guidance. Let's find someone who does."

2. **Feasibility calibration is an art.** The line between honest calibration (protecting the student from demoralising failure) and dream-crushing (discouraging ambition) is not always clear. Some students need to attempt ambitious projects and learn from partial success. Others need protection from projects that will break their confidence. The educator must read the individual student — there is no formula.

3. **The tracking system requires discipline.** The Monday update habit is the foundation of the whole self-monitoring system, and it is the first thing students let slip when they get busy or stuck. If the tracking system goes dark for two weeks, the project is in trouble. The educator's role is to enforce the update habit without nagging — "I notice your tracking system hasn't been updated. What's happening?" is mentoring; "You need to update your tracking" is administration.

4. **Self-determined projects require more mentoring time than structured assignments.** Each student's project is unique, which means each mentoring conversation is unique. A teacher mentoring 15 self-determined projects simultaneously needs substantial time — 20 minutes per student per fortnight is a minimum, which is 2.5 hours per cycle. Schools must allocate this time deliberately or the mentoring becomes superficial.

5. **The defence is only as valuable as its audience.** A defence presented to a panel that asks easy questions and praises everything teaches the student that presentation equals success. A defence with genuine, respectful challenge teaches the student that their work must withstand scrutiny. The quality of the panel matters.
