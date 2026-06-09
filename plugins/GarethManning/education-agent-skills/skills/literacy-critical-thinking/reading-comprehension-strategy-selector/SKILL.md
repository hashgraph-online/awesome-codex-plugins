---
# AGENT SKILLS STANDARD FIELDS (v2)
name: reading-comprehension-strategy-selector
description: "Select and sequence reading comprehension strategies matched to a specific text's challenges and demands. Use when students struggle with a text or need targeted reading support."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/reading-comprehension-strategy-selector"
skill_name: "Reading Comprehension Strategy Selector"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Duke & Pearson (2002) — Effective practices for developing reading comprehension"
  - "Pressley (2002) — Metacognition and self-regulated comprehension"
  - "National Reading Panel (2000) — Teaching children to read: an evidence-based assessment"
  - "Palincsar & Brown (1984) — Reciprocal teaching of comprehension-fostering and comprehension-monitoring activities"
  - "Shanahan et al. (2010) — Improving reading comprehension in kindergarten through 3rd grade: IES practice guide"
input_schema:
  required:
    - field: "text_description"
      type: "string"
      description: "A description of the text students will read — genre, topic, length, and key challenges"
    - field: "reader_challenge"
      type: "string"
      description: "The specific comprehension difficulty students are likely to face with this text"
    - field: "student_level"
      type: "string"
      description: "Age/year group and current reading competence"
  optional:
    - field: "reading_purpose"
      type: "string"
      description: "Why students are reading this text — e.g. to extract information, to analyse, to enjoy, to compare"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: reading levels, decoding ability, EAL status"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject — strategy selection varies by discipline"
    - field: "text_extract"
      type: "string"
      description: "A short extract from the actual text to enable more precise strategy recommendations"
output_schema:
  type: "object"
  fields:
    - field: "recommended_strategies"
      type: "array"
      description: "2–3 strategies selected for this text and reader challenge, with rationale"
    - field: "implementation_guide"
      type: "object"
      description: "Step-by-step guide for teaching each strategy with this text — before, during, and after reading"
    - field: "teacher_modelling_script"
      type: "string"
      description: "A brief think-aloud script showing the teacher modelling the primary strategy"
    - field: "strategy_pitfalls"
      type: "string"
      description: "What can go wrong with strategy instruction and how to avoid it"
chains_well_with:
  - "text-complexity-analyser"
  - "think-aloud-script-generator"
  - "vocabulary-tiering-tool"
  - "scaffolded-task-modifier"
teacher_time: "3 minutes"
tags: ["reading", "comprehension", "strategy-instruction", "reciprocal-teaching", "metacognition"]
---

# Reading Comprehension Strategy Selector

## What This Skill Does

Identifies the most appropriate reading comprehension strategies for a specific text and reader challenge, and provides a complete implementation guide including a teacher modelling script. Rather than defaulting to "use all the strategies" (a common but ineffective approach), this skill matches specific strategies to specific comprehension challenges — predicting when the text structure is unfamiliar, questioning when the content is dense, clarifying when vocabulary is technical, summarising when the text is long and detailed. The output tells teachers not just WHICH strategy to use but HOW to teach it with this specific text. AI is specifically valuable here because strategy selection requires simultaneously analysing the text's demands, the readers' likely difficulties, and the evidence base for each strategy — a three-way match that most teachers don't have time to make explicitly.

## Evidence Foundation

Duke & Pearson (2002) identified six comprehension strategies with strong evidence: predicting, questioning, monitoring/clarifying, visualising, making connections, and summarising. Crucially, they emphasised that strategy instruction must be explicit — teachers must model the strategy through think-aloud, guide students in applying it, and gradually release responsibility. Pressley (2002) showed that skilled readers use strategies flexibly and selectively, choosing different strategies for different reading challenges — teaching students to use all strategies all the time produces cognitive overload and superficial application. The National Reading Panel (2000) confirmed that comprehension strategy instruction produces significant effects (especially questioning and summarising), but cautioned that strategies are means to understanding, not ends in themselves — the goal is comprehension, not strategy use. Palincsar & Brown (1984) demonstrated the effectiveness of reciprocal teaching — a structured approach where students take turns applying four strategies (predicting, questioning, clarifying, summarising) — with effect sizes of 0.74 for comprehension gains. Shanahan et al. (2010) noted that strategy instruction is most effective for intermediate readers who can decode but struggle with meaning; for beginning readers, decoding instruction takes priority.

## Input Schema

The teacher must provide:
- **Text description:** What students will read. *e.g. "A Year 9 History textbook extract (800 words) about the causes of the Industrial Revolution — dense with unfamiliar vocabulary and multiple causal factors" / "A short story by Roald Dahl with an unexpected twist ending — Year 5 reading level"*
- **Reader challenge:** The specific difficulty. *e.g. "Students tend to read the surface events but miss the underlying causes" / "Students don't notice the clues that foreshadow the ending" / "Students get lost in the technical vocabulary and give up"*
- **Student level:** Year group and reading competence. *e.g. "Year 7, can decode fluently but struggle with inference" / "Year 4, mixed — some confident readers, some still developing fluency"*

Optional (injected by context engine if available):
- **Reading purpose:** Why students are reading this text
- **Student profiles:** Reading levels, decoding ability, EAL status
- **Subject area:** The curriculum subject
- **Text extract:** A short extract from the actual text

## Prompt

```
You are an expert in reading comprehension instruction, with deep knowledge of Duke & Pearson's (2002) strategy instruction research, Pressley's (2002) work on metacognitive comprehension, Palincsar & Brown's (1984) reciprocal teaching, and the National Reading Panel's (2000) findings on comprehension instruction. You understand that effective strategy instruction is SELECTIVE (matching specific strategies to specific challenges), EXPLICIT (modelled by the teacher before students apply independently), and PURPOSEFUL (strategies serve comprehension, not the other way around).

Your task is to select and plan comprehension strategy instruction for:

**Text description:** {{text_description}}
**Reader challenge:** {{reader_challenge}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Reading purpose:** {{reading_purpose}} — if not provided, infer the most likely purpose from the text description and subject area.
**Student profiles:** {{student_profiles}} — if not provided, design for a mixed-ability class with generally fluent decoding but variable comprehension.
**Subject area:** {{subject_area}} — if not provided, infer from the text description.
**Text extract:** {{text_extract}} — if provided, use it to ground the modelling script in the actual text. If not, create a plausible example.

Apply these evidence-based principles:

1. **Select strategies based on the specific comprehension challenge (Duke & Pearson, 2002; Pressley, 2002):**
   - Do NOT recommend all strategies at once. Select 2–3 strategies that directly address the stated reader challenge.
   - Match strategies to challenges:
     - Unfamiliar text structure → Predicting (activates expectations about structure)
     - Dense content with many ideas → Summarising (forces identification of main ideas)
     - Implicit meaning, inference required → Questioning (focuses attention on what's not said)
     - Technical or unfamiliar vocabulary → Clarifying/Monitoring (teaches students to identify and resolve confusion)
     - Narrative with complex character motivation → Making connections + Questioning
     - Informational text with complex processes → Visualising + Summarising
   - Explain WHY each strategy is appropriate for THIS text and THIS challenge.

2. **Explicit instruction sequence (Duke & Pearson, 2002):**
   - For each strategy, provide:
     a. Teacher modelling (I Do): The teacher demonstrates the strategy through think-aloud
     b. Guided practice (We Do): Students try the strategy with teacher support
     c. Independent application (You Do): Students apply the strategy independently
   - The modelling script should show the teacher's actual thinking process, not just the strategy label.

3. **Strategies are tools, not rituals (National Reading Panel, 2000):**
   - Warn against turning strategies into worksheet activities. "Write three predictions" is not prediction instruction — it's a compliance task.
   - The goal is COMPREHENSION, not strategy performance. If students can comprehend the text without the strategy, they don't need the strategy.
   - Strategy instruction should feel like thinking, not like form-filling.

4. **Developmental appropriateness (Shanahan et al., 2010):**
   - For younger or less fluent readers: focus on a single strategy, with heavy modelling and supported practice.
   - For intermediate readers: 2 strategies, with gradual release.
   - For advanced readers: flexible strategy use — teach students to select their own strategies based on the reading challenge.
   - If students are still struggling with decoding, strategy instruction is premature — note this.

5. **Before, during, and after reading structure:**
   - Organise the implementation around the reading process:
     - Before reading: activate prior knowledge, set purpose, introduce strategy
     - During reading: apply strategy at specific points in the text
     - After reading: reflect on comprehension, evaluate strategy effectiveness

Return your output in this exact format:

## Reading Comprehension Strategies: [Brief text description]

**For:** [Student level]
**Text:** [Text description]
**Key challenge:** [Reader challenge]
**Reading purpose:** [Stated or inferred]

### Recommended Strategies

For each strategy (2–3):
- **Strategy [N]: [Name]**
  **Why this strategy for this text:** [Specific rationale — what about this text and these readers makes this strategy the right choice]
  **What it looks like in practice:** [Brief description of what students will actually DO]

### Implementation Guide

**Before Reading (X minutes)**
[What the teacher does to set up the reading — activating prior knowledge, introducing the strategy, setting purpose]

**During Reading (X minutes)**
[Specific points in the text where the strategy should be applied, and how — teacher-guided for first application, then student-led]

**After Reading (X minutes)**
[How students reflect on their comprehension and evaluate the strategy's effectiveness]

### Teacher Modelling Script

[A think-aloud script where the teacher models the primary strategy with a specific section of the text — showing the internal thinking process, not just the strategy label]

### Strategy Pitfalls

[2–3 things that can go wrong with strategy instruction for this text, and how to avoid them]

**Self-check before returning output:** Verify that (a) strategies are matched to the specific comprehension challenge, not generically recommended, (b) the implementation includes explicit teacher modelling before student application, (c) the modelling script shows actual thinking, not just strategy labelling, (d) the approach is developmentally appropriate, and (e) the strategies serve comprehension, not the other way around — a student who understands the text has succeeded, whether or not they "used the strategy correctly."
```

## Example Output

**Scenario:** *Text description: "A Year 8 History textbook extract (600 words) explaining the causes of the Black Death's spread across Europe — the text presents multiple causal factors (trade routes, fleas on rats, lack of medical knowledge, overcrowded cities) and students need to understand how these factors interacted" / Reader challenge: "Students tend to list the causes without understanding how they connect — they can say 'trade routes spread the plague' but can't explain the chain of causation" / Student level: "Year 8, fluent decoders, can identify explicit information but struggle with implicit connections between ideas"*

---

## Reading Comprehension Strategies: Causes of the Black Death's Spread

**For:** Year 8 History
**Text:** Textbook extract (600 words) on the causes of the Black Death's spread across Europe
**Key challenge:** Students list causes individually but don't understand how they interacted — they can't explain the causal chain
**Reading purpose:** To understand the interconnected causes of the plague's spread, in preparation for writing a causal explanation

### Recommended Strategies

**Strategy 1: Questioning — "How does this connect?"**
**Why this strategy for this text:** The comprehension challenge is about connections between ideas, not about understanding individual facts. Students can extract the information ("trade routes," "fleas on rats") but don't spontaneously ask how one cause relates to another. Self-questioning forces students to generate connection questions as they read: "How did trade routes help fleas spread?" / "Why did overcrowded cities make the plague worse?"
**What it looks like in practice:** Students pause at the end of each paragraph and ask: "How does this cause connect to the ones I've already read about?" They record their questions and attempt to answer them.

**Strategy 2: Summarising — Causal Chain Mapping**
**Why this strategy for this text:** The text presents multiple causes, and students need to identify not just what they are but how they form a chain. Summarising forces students to select the most important information and organise it — in this case, organising it as a causal chain rather than a list. The summarising is disciplinary: "What caused what?" rather than "What are the main points?"
**What it looks like in practice:** After every two paragraphs, students summarise in one sentence using the frame: "[Cause A] led to [Cause B] because..." This forces causal linking, not listing.

### Implementation Guide

**Before Reading (5 minutes)**

1. *Activate prior knowledge:* "Before we read, what do you already know about the Black Death? When was it? Where?" Quick brainstorm — 2 minutes.

2. *Set the reading challenge:* "Today's text explains WHY the plague spread so quickly across Europe. It gives several causes. Your job isn't just to find the causes — I want you to understand how they CONNECT. One cause didn't work alone — they worked together like a chain."

3. *Introduce the questioning strategy:* "As you read, I want you to keep asking one question: 'How does this connect to what I just read?' When the text tells you about trade routes, ask: 'How did trade routes connect to the fleas?' When it tells you about overcrowded cities, ask: 'Why did overcrowding make the other causes worse?'"

4. *Show the recording format:* Two columns — left column: "Cause," right column: "How it connects to other causes."

**During Reading (15 minutes)**

*Paragraph 1 — Teacher models (see script below)*

*Paragraph 2 — Guided practice:* Read aloud together. Pause. "OK, this paragraph talked about fleas on rats. How does that connect to the trade routes we read about in paragraph 1? Talk to your partner — what's the connection?" Circulate. Listen for causal language. Share one good example with the class.

*Paragraphs 3–4 — Supported independence:* Students read in pairs. After each paragraph, they pause, ask the connection question, and add to their two-column record. Teacher circulates and checks for connection language, not just listing.

*Paragraphs 5–6 — Independent application:* Students read and record independently. Teacher identifies 2–3 students to share their connections at the end.

**After Reading (5 minutes)**

1. *Share connections:* "Who found a connection between two causes that surprised them?" Take 2–3 examples. Push for causal language: "Don't just tell me the two causes — tell me HOW they connected."

2. *Build the causal chain together:* On the board, construct a visual causal chain: Trade routes → brought rats with fleas → into overcrowded cities → where lack of medical knowledge meant → no effective response. "See how none of these causes works alone? It's the chain that made the plague devastating."

3. *Reflect on the strategy:* "Did asking 'How does this connect?' help you understand the text differently than if you'd just read straight through? Why?"

### Teacher Modelling Script

*Modelling the questioning strategy with Paragraph 1:*

"I'm going to read the first paragraph aloud and show you what I'm thinking as I read. Watch how I ask myself questions about connections.

[Reads paragraph 1 about trade routes between Asia and Europe]

OK, so this paragraph is telling me that trade routes connected Asia to Europe and that the Black Death started in Central Asia. So trade routes are one cause of the spread. But I'm going to ask myself: 'How does this connect to other causes?' I know that trade routes carry goods — so maybe they also carried something else? The text says 'merchants travelled with their goods along the Silk Road.' I'm thinking: if merchants are travelling, what might be travelling WITH them that they don't know about? I'm going to hold that question as I read the next paragraph.

See what I did? I didn't just say 'trade routes — that's a cause.' I asked HOW trade routes actually spread the plague. That 'how' question is what I want you to ask for every cause you find."

### Strategy Pitfalls

1. **Questioning becomes a worksheet exercise.** If students write "How does this connect?" after every paragraph without actually thinking about the answer, the strategy has become a compliance task. Avoid this by insisting that students ANSWER their questions, not just ask them. During circulation, don't check that students have written questions — check that they can EXPLAIN the connections.

2. **Summarising becomes listing.** Students may record "Cause 1: trade routes. Cause 2: fleas" — which is listing, not summarising connections. The sentence frame "X led to Y because..." is designed to prevent this, but it requires enforcement. If students write single-word answers, stop and re-model: "You wrote 'fleas.' But how did fleas CONNECT to the trade routes? That's the summary I need."

3. **The strategy overshadows the content.** If students spend more time thinking about "Am I using the strategy correctly?" than "How did the plague spread?", the strategy has become an obstacle. The goal is comprehension of the historical content, not perfect strategy execution. If a student can explain the causal chain but didn't formally use the strategy, that student has SUCCEEDED. Strategy is a scaffold for thinking, not a requirement.

---

## Known Limitations

1. **Strategy instruction is most effective for intermediate readers — those who can decode but struggle with comprehension.** For students who are still developing fluency (reading slowly, decoding word-by-word), comprehension strategies add cognitive load rather than reducing it. These students need fluency instruction first. The skill flags this developmental consideration but cannot assess individual students' decoding levels — the teacher must make this judgment.

2. **The strategy recommendations depend on the accuracy of the text description and reader challenge.** If the teacher describes the challenge as "students can't understand the vocabulary" but the real challenge is "students don't have the background knowledge to make sense of the content," the recommended strategies will miss the mark. Strategy selection is diagnostic — it requires accurate identification of what's going wrong.

3. **Strategy instruction can become formulaic if overused.** If every text is preceded by "Today we're going to use predicting and questioning," students stop engaging with the strategies and start performing them mechanically. Strategies should be taught when they're needed, not used as a routine for every reading task. The best outcome is students who select strategies themselves when they notice their comprehension breaking down.
