---
# AGENT SKILLS STANDARD FIELDS (v2)
name: ai-facilitated-collaborative-learning-designer
description: "Design AI-supported collaborative tasks that structure group interaction and address participation problems. Use when students struggle to collaborate effectively on group tasks."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "ai-learning-science/ai-facilitated-collaborative-learning-designer"
skill_name: "AI-Facilitated Collaborative Learning Designer"
domain: "ai-learning-science"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Roschelle & Teasley (1995) — The construction of shared knowledge in collaborative problem solving"
  - "Dillenbourg (1999) — What do you mean by collaborative learning? (CSCL framework)"
  - "Järvelä & Hadwin (2013) — New frontiers: regulating learning in CSCL (socially shared regulation of learning)"
  - "Slavin (1995) — Cooperative learning: theory, research, and practice (meta-analysis)"
  - "Kirschner et al. (2018) — From cognitive load theory to collaborative cognitive load theory"
input_schema:
  required:
    - field: "collaborative_task"
      type: "string"
      description: "The specific learning task that students will work on together — what they need to produce or solve as a group"
    - field: "collaboration_challenge"
      type: "string"
      description: "The specific collaboration problem to address — what goes wrong when students work together on this task"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group and proficiency level"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "group_size"
      type: "string"
      description: "How many students per group"
    - field: "ai_capabilities"
      type: "string"
      description: "What AI tools are available — chatbot, collaborative workspace, real-time monitoring, or other"
    - field: "time_available"
      type: "string"
      description: "How long students have for the collaborative task"
output_schema:
  type: "object"
  fields:
    - field: "collaboration_design"
      type: "object"
      description: "The structure of the collaborative task — roles, phases, and the specific points where AI facilitates"
    - field: "ai_facilitation_moves"
      type: "array"
      description: "The specific things the AI does during collaboration — prompts, monitoring, scaffolding, and interventions"
    - field: "regulation_scaffolds"
      type: "object"
      description: "How the AI supports socially shared regulation — planning, monitoring, and reflecting on the group process"
    - field: "equity_mechanisms"
      type: "object"
      description: "How the design ensures all group members participate meaningfully — preventing free-riding and dominance"
chains_well_with:
  - "intelligent-tutoring-dialogue-designer"
  - "ai-feedback-design-principles"
  - "metacognitive-monitoring-ai-contexts"
teacher_time: "5 minutes"
tags: ["collaboration", "CSCL", "Dillenbourg", "Järvelä", "cooperative-learning", "Slavin", "group-work", "AI-facilitation", "regulation"]
---

# AI-Facilitated Collaborative Learning Designer

## What This Skill Does

Designs a collaborative learning task with specific AI facilitation points — the places where an AI system supports the group process without replacing it. This skill addresses the fundamental challenge of collaborative learning: it CAN be one of the most powerful learning approaches (Slavin's 1995 meta-analysis found effect sizes of 0.26-0.32 for well-structured cooperative learning) but it frequently degenerates into one student doing all the work while others watch, or into parallel individual work with a shared document. Dillenbourg (1999) established that genuine collaboration requires joint problem-solving with shared understanding, not just task division. Järvelä & Hadwin (2013) showed that effective collaboration requires socially shared regulation of learning (SSRL) — the group's ability to collectively plan, monitor, and adjust their approach. AI is specifically valuable here because it can do what teachers cannot: observe multiple groups simultaneously, detect collaboration breakdown in real time, and intervene precisely when needed. A teacher circulating among 8 groups catches problems minutes or hours late; an AI monitoring group interactions can prompt in real time. The output includes the complete collaboration design (task structure, roles, phases), AI facilitation moves (when and how the AI intervenes), regulation scaffolds (supporting the group's self-regulation), and equity mechanisms (ensuring all members participate).

## Evidence Foundation

Dillenbourg (1999) established the foundational framework for computer-supported collaborative learning (CSCL), distinguishing between cooperation (dividing a task into subtasks that individuals complete separately) and collaboration (jointly constructing shared understanding of a problem). He argued that genuine collaboration requires: (a) a shared goal, (b) mutual engagement with each other's ideas, and (c) joint construction of knowledge that no individual could produce alone. Technology can support collaboration by structuring interaction, making thinking visible, and providing shared representations — but it can also undermine collaboration by making task division too easy. Roschelle & Teasley (1995) defined collaboration as "a coordinated, synchronous activity that is the result of a continued attempt to construct and maintain a shared conception of a problem." They showed that effective collaboration involves specific conversational patterns: proposals, elaborations, challenges, and repairs of shared understanding. When these patterns break down, collaboration degenerates into parallel work. Järvelä & Hadwin (2013) developed the concept of socially shared regulation of learning (SSRL) — the idea that effective collaborative groups don't just share the cognitive work, they also share the REGULATORY work: planning what to do, monitoring progress, evaluating whether their approach is working, and adjusting when it isn't. They found that SSRL is the strongest predictor of collaborative learning success, and that it can be scaffolded by technology — prompts that ask the group to plan, check progress, and reflect. Slavin (1995) conducted a comprehensive review of cooperative learning research, finding consistent positive effects (d = 0.26-0.32) when two conditions were met: (a) group goals (the group is assessed as a group, not individually) and (b) individual accountability (each member's contribution is visible and assessed). Without these conditions, cooperative learning often produces free-riding and social loafing. Kirschner et al. (2018) extended cognitive load theory to collaborative contexts, arguing that group work distributes cognitive load across members — but only when the task is too complex for any individual. For simple tasks, the transaction costs of collaboration (coordinating, communicating, managing different perspectives) outweigh the benefits. Collaboration should be reserved for tasks that genuinely require multiple minds.

## Input Schema

The teacher must provide:
- **Collaborative task:** What students will work on together. *e.g. "Year 10 science: design an experiment to test whether temperature affects the rate of a chemical reaction. Each group must produce a method, risk assessment, predicted results, and explanation of the underlying chemistry" / "Year 8 English: collaboratively write a newspaper front page covering the events of Romeo and Juliet as if they happened today" / "Year 12 economics: analyse a real-world case study of market failure and produce a policy brief recommending government intervention"*
- **Collaboration challenge:** What goes wrong when students collaborate on this. *e.g. "One student does all the writing while the others watch. The 'discussion' phase lasts 30 seconds before they start dividing up the task" / "Groups default to the loudest student's idea without considering alternatives. Quieter students disengage" / "Students split the work up ('you do the method, I'll do the risk assessment') and never build shared understanding — the final product is four separate pieces stuck together"*

Optional (injected by context engine if available):
- **Student level:** Year group and proficiency
- **Subject area:** The curriculum subject
- **Group size:** How many students per group
- **AI capabilities:** What AI tools are available
- **Time available:** Duration of the collaborative task

## Prompt

```
You are an expert in collaborative learning design and AI-facilitated CSCL (computer-supported collaborative learning), with deep knowledge of Dillenbourg's (1999) collaboration framework, Roschelle & Teasley's (1995) research on shared knowledge construction, Järvelä & Hadwin's (2013) socially shared regulation of learning (SSRL), Slavin's (1995) meta-analysis of cooperative learning, and Kirschner et al.'s (2018) collaborative cognitive load theory. You understand that collaboration is one of the most powerful — and most frequently misused — learning strategies. You know that the difference between productive collaboration and time-wasting group work depends entirely on the DESIGN, not on the students.

CRITICAL PRINCIPLES:
- **Collaboration requires a task that is genuinely too complex for one person.** Kirschner et al. (2018): if one student can do the task alone, collaboration adds transaction costs without cognitive benefit. The task must require multiple perspectives, skills, or knowledge bases that no individual possesses. If the task could be done individually, don't make it collaborative.
- **Structure the interaction, not just the task.** Dillenbourg (1999): giving students a task and saying "work together" is not collaborative learning design. The interaction must be structured: who speaks when, what they discuss at each phase, how they make decisions, and how they build on each other's ideas. AI can enforce this structure without the teacher being present.
- **Individual accountability prevents free-riding.** Slavin (1995): every group member must have a visible, assessable contribution. If a student can sit passively and still get the grade, they will. Design roles, individual deliverables, or accountability mechanisms that make every student's contribution visible.
- **AI should facilitate, not participate.** The AI's role is to support the GROUP PROCESS — prompting planning, flagging imbalanced participation, asking regulation questions ("How is your approach going? Do you need to adjust?"). The AI should NOT contribute ideas, solve problems for the group, or become a group member. If students are talking to the AI instead of to each other, the design has failed.
- **Socially shared regulation is the highest-value target.** Järvelä & Hadwin (2013): the groups that learn the most are the ones that collectively regulate their process — planning, monitoring, and adjusting. AI scaffolds for regulation (planning prompts, progress checks, reflection prompts) are more valuable than AI scaffolds for content.

Your task is to design an AI-facilitated collaborative learning experience:

**Collaborative task:** {{collaborative_task}}
**Collaboration challenge:** {{collaboration_challenge}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for a general secondary school context.
**Subject area:** {{subject_area}} — if not provided, infer from the task.
**Group size:** {{group_size}} — if not provided, design for groups of 3-4.
**AI capabilities:** {{ai_capabilities}} — if not provided, design for a text-based AI that can monitor group work and send prompts to the group.
**Time available:** {{time_available}} — if not provided, design for a 50-minute lesson.

Return your output in this exact format:

## AI-Facilitated Collaboration Design: [Task Name]

**Task:** [What students will produce together]
**Collaboration challenge addressed:** [The specific problem this design solves]
**AI role:** [One-sentence summary of what the AI does and what it does NOT do]

### Task Complexity Check

[Verify that this task genuinely requires collaboration. If it doesn't, redesign it so it does.]

### Collaboration Structure

[The complete design: phases, roles, interaction rules, and deliverables. Include timing.]

**Phase 1: [Name]** (X minutes)
[What happens, what each role does, what the AI does]

**Phase 2: [Name]** (X minutes)
[What happens, what each role does, what the AI does]

### AI Facilitation Moves

[The specific moves the AI makes during collaboration — when, what, and why]

| Trigger | AI Move | Purpose | Example |
|---|---|---|---|
| [When] | [What the AI does] | [Why] | [Exact text] |

### Regulation Scaffolds

[How the AI supports socially shared regulation — planning, monitoring, and reflection prompts]

### Equity Mechanisms

[How the design ensures balanced participation — roles, accountability, and AI monitoring]

### What the AI Does NOT Do

[Explicit boundaries on AI involvement — what the AI should never do in this context]

**Self-check before returning output:** Verify that (a) the task genuinely requires collaboration, (b) interaction is structured not just assigned, (c) individual accountability is built in, (d) the AI facilitates the process rather than participating in it, and (e) regulation scaffolds are included.
```

## Example Output

**Scenario:** *Collaborative task: "Year 10 science: design an experiment to test whether temperature affects the rate of a chemical reaction (hydrochloric acid and sodium thiosulfate). Each group must produce a method, risk assessment, predicted results graph, and explanation of the underlying chemistry (collision theory)" / Collaboration challenge: "Groups always divide the work: one student writes the method, one does the risk assessment, one draws the graph, one does the theory. They never discuss, never build shared understanding, and the final report is four separate pieces stuck together. The student who wrote the method often doesn't understand the theory, and the student who wrote the theory couldn't replicate the method" / Group size: "4" / Student level: "Year 10, triple science" / AI capabilities: "Text-based AI chatbot that can message the group at set intervals or in response to triggers" / Time available: "60 minutes"*

---

## AI-Facilitated Collaboration Design: Experiment Design — Temperature and Reaction Rate

**Task:** Design a complete experiment to test whether temperature affects the rate of the hydrochloric acid / sodium thiosulfate reaction
**Collaboration challenge addressed:** Task-splitting without shared understanding — students divide and conquer rather than collaborating, producing fragmented work
**AI role:** The AI monitors group process and sends regulation prompts at key moments. It NEVER contributes scientific ideas, writes any part of the report, or answers chemistry questions.

### Task Complexity Check

The original task CAN be divided into independent subtasks (method, risk assessment, graph, theory) — which is exactly why students split it up. To make collaboration necessary, the task must be REDESIGNED so that each component depends on the others:

**Redesigned task:** Instead of producing four separate sections, the group must produce ONE integrated document where every decision in the method is explicitly justified by the theory, every risk is linked to a specific step in the method, and the predicted results graph is derived from the theory (with the group explaining the shape of the curve). This interdependence means students CANNOT split the work — the student writing the method needs the theory student, and vice versa.

**Additional constraint:** Each group member must be able to explain ANY section of the report, not just "their" section. The teacher will randomly select one member at the end to present and answer questions about the entire report.

### Collaboration Structure

**Phase 1: Individual Thinking (5 minutes)**
Each student independently writes down: (a) what they already know about collision theory, (b) one thing they're unsure about, and (c) their prediction — will higher temperature increase or decrease the reaction rate, and why? This activates prior knowledge and gives every student something to contribute to the discussion. NO TALKING during this phase.

*AI move:* At the end of 5 minutes, the AI sends: "Time's up for individual thinking. Before you start discussing, each person shares ONE thing they wrote down. Go round the group — everyone speaks before anyone speaks twice."

**Phase 2: Shared Understanding Building (15 minutes)**
The group discusses collision theory and how temperature affects reaction rate. They must reach AGREEMENT on: (a) why higher temperature increases the rate (particles move faster → more frequent AND more energetic collisions → more particles exceed activation energy), and (b) what the predicted results graph should look like (curved line showing rate increasing with temperature — not linear, because of the activation energy distribution). No writing yet — this is DISCUSSION only.

*AI move:* At minute 10, the AI sends a regulation check: "Quick check: can everyone in the group explain WHY higher temperature increases reaction rate? Not just 'particles move faster' — WHY does faster movement lead to a faster reaction? If anyone is unsure, this is the time to ask. You need this understanding for the next phase."

**Phase 3: Integrated Design (25 minutes)**
The group writes the integrated report. To prevent task-splitting, use a ROTATING AUTHOR structure:
- Minutes 1-8: Person A writes, others contribute verbally. Focus: method (but every step must be justified by the theory — "We heat to 40°C because…").
- Minutes 9-16: Person B writes, others contribute. Focus: predicted results and theory explanation (linking the graph shape to collision theory).
- Minutes 17-25: Person C writes, others contribute. Focus: risk assessment and variables (linking risks to specific method steps, explaining controlled variables).
- Person D is the "quality checker" throughout — their job is to ensure every section connects to every other section.

Roles rotate, but the KEY design feature is that the person writing must incorporate the group's verbal input, not work alone. The other three are actively contributing ideas, not watching.

*AI moves:* See AI Facilitation Moves table below.

**Phase 4: Presentation Preparation (10 minutes)**
The AI randomly selects one group member to present the report and answer the teacher's questions. The group has 10 minutes to ensure the selected person can explain EVERYTHING — not just "their" section.

*AI move:* At the start of Phase 4, the AI sends: "For the presentation, [randomly selected name] will explain and answer questions on the ENTIRE report. Group: you have 10 minutes to make sure [name] can explain the method, the theory, the predicted results, and the risk assessment. Quiz them. Find the gaps."

**Phase 5: Presentation (5 minutes per group)**
Selected member presents. Teacher asks questions. This is the individual accountability mechanism — every member must understand the whole report because any of them could be selected.

### AI Facilitation Moves

| Trigger | AI Move | Purpose | Example |
|---|---|---|---|
| End of Phase 1 (5 min) | Round-robin prompt | Ensure all voices are heard before discussion begins | "Each person shares ONE thing from their individual notes. Go clockwise. Everyone speaks once before anyone speaks twice." |
| Phase 2, minute 10 | Comprehension check | Verify shared understanding before writing begins | "Can everyone explain WHY higher temperature increases rate? Not just 'what happens' but 'why it happens.' Check with each other." |
| Phase 3, minute 5 | Integration prompt | Prevent method from being written without theory connection | "I notice you're writing method steps. For each step, add: 'We chose this because...' linking it to your theory understanding." |
| Phase 3, one student not contributing for 3+ min | Participation prompt | Prevent disengagement | "[Name], what do you think about [the current section being written]? The group needs your input here." |
| Phase 3, minute 20 | Progress check | Ensure the group is on track to finish | "You have 5 minutes left for writing. Quick check: have you connected the method to the theory, and the predicted graph to the collision model? What's still missing?" |
| Start of Phase 4 | Random selection + preparation prompt | Create individual accountability | "[Name] has been selected to present. Group: 10 minutes to make sure they can explain everything." |

### Regulation Scaffolds

**Planning (start of Phase 2):** The AI sends: "Before you dive in — take 60 seconds as a group to agree: what does a GOOD experiment design look like for this task? What will make yours better than average? Write down your group's success criteria."

**Monitoring (mid-Phase 3):** The AI sends: "Halfway through writing. Look back at the success criteria you set. Are you meeting them? If not, what do you need to adjust?"

**Reflection (end of Phase 3, before presentation prep):** The AI sends: "Before you prepare for the presentation — one quick reflection as a group: what was the hardest part of working together on this? What would you do differently next time?" This builds metacognitive awareness of the collaboration process itself.

### Equity Mechanisms

1. **Individual thinking before group discussion (Phase 1).** Every student arrives at the discussion with their own ideas. This prevents the loudest student from dominating from the start — everyone has something prepared.

2. **Round-robin sharing (start of Phase 2).** The AI enforces "everyone speaks once before anyone speaks twice." This ensures quiet students contribute before dominant students take over.

3. **Rotating author structure (Phase 3).** No single student can write the entire report. The rotation forces different people to hold the pen, reducing the "one person does everything" problem.

4. **Quality checker role.** Person D's explicit job is to ensure integration — but also to notice if anyone has stopped contributing and to pull them back in.

5. **Random presentation selection (Phase 4).** Because any member could be selected, the group is incentivised to ensure everyone understands everything. The free-rider who "did nothing" becomes a liability the group will actively address.

6. **AI participation monitoring.** The AI detects extended silence from individual students and prompts the group to include them. This catches disengagement that the teacher would miss.

### What the AI Does NOT Do

- **The AI does NOT answer chemistry questions.** If a student asks the AI "What is collision theory?" the AI should respond: "That's a great question for your group. Ask them — and if nobody knows, flag it for your teacher."
- **The AI does NOT write any part of the report.** It does not generate text, suggest method steps, or draw predicted graphs.
- **The AI does NOT evaluate the quality of the science.** It doesn't say "your method is good" or "your theory explanation is incomplete." Quality evaluation is the teacher's role.
- **The AI does NOT resolve disagreements.** If the group disagrees about the predicted graph shape, the AI should say: "You have a disagreement. Good — that means someone is thinking deeply. Can each person explain their reasoning? Then decide as a group." The AI facilitates the PROCESS of disagreement resolution, not the CONTENT.

---

## Known Limitations

1. **AI-facilitated collaboration depends on reliable AI monitoring.** The facilitation moves above assume the AI can detect participation imbalances, silence, and off-task behaviour. Current AI systems have variable capabilities here — text-based monitoring is feasible, but detecting disengagement in a face-to-face group working on paper is much harder. The design may need to be adapted for the specific AI system available.

2. **The evidence for AI-specific facilitation of collaboration is still emerging.** Dillenbourg (1999), Slavin (1995), and Järvelä & Hadwin (2013) established the principles of effective collaboration, but the specific application of AI to facilitate these principles is a newer field with fewer controlled studies. The AI facilitation moves above are principled extrapolations from established research, not empirically validated AI interventions.

3. **Collaborative cognitive load can be high.** Kirschner et al. (2018) note that coordination costs (communicating, negotiating, managing different perspectives) consume cognitive resources. For students who are already struggling with the content, the additional load of structured collaboration may be overwhelming. The teacher should monitor whether the collaboration structure is helping or hindering learning.

4. **Cultural norms affect collaboration.** Dillenbourg's (1999) framework was developed primarily in Western educational contexts. In some cultural contexts, direct disagreement, challenging peers' ideas, or speaking before someone of higher perceived status may be uncomfortable or inappropriate. The AI facilitation prompts may need cultural adaptation.
