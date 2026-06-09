---
# AGENT SKILLS STANDARD FIELDS (v2)
name: experiential-learning-cycle-designer
description: "Structure a direct experience into a full learning cycle with concrete experience, reflection, and conceptual transfer. Use when planning field trips, simulations, or practical tasks."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "environmental-experiential-learning/experiential-learning-cycle-designer"
skill_name: "Experiential Learning Cycle Designer"
domain: "environmental-experiential-learning"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Hattie (2009) — Visible Learning: simulation and gaming effect size d=0.33"
  - "Billig (2000) — Research on K-12 school-based service learning: the evidence builds"
  - "Dewey (1938) — Experience and Education"
  - "Boud, Keogh & Walker (1985) — Reflection: turning experience into learning"
  - "Wurdinger & Carlson (2010) — Teaching for Experiential Learning: five approaches that work"
input_schema:
  required:
    - field: "learning_objective"
      type: "string"
      description: "The specific knowledge, skill, or understanding students need to develop"
    - field: "experience_type"
      type: "string"
      description: "The kind of direct experience available — simulation, role play, field trip, community project, practical task, experiment"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "time_available"
      type: "string"
      description: "How much time for the full cycle — single lesson, multiple lessons, a week"
    - field: "resources_available"
      type: "string"
      description: "What resources, materials, or settings are available for the experience"
    - field: "prior_knowledge"
      type: "string"
      description: "What students already know — determines where in the cycle emphasis falls"
output_schema:
  type: "object"
  fields:
    - field: "experiential_cycle"
      type: "object"
      description: "The four-phase learning cycle: experience → reflection → conceptualisation → application"
    - field: "experience_design"
      type: "object"
      description: "The direct experience — what students do, see, feel, encounter"
    - field: "reflection_design"
      type: "object"
      description: "How students process the experience — structured reflection that extracts learning"
    - field: "conceptualisation_design"
      type: "object"
      description: "How students connect their experience to theory, principles, or generalisable knowledge"
    - field: "application_design"
      type: "object"
      description: "How students apply their learning to a new situation — testing understanding through action"
chains_well_with:
  - "service-learning-project-designer"
  - "outdoor-learning-sequence-designer"
  - "reflective-practice-prompt-generator"
  - "agency-scaffold-generator"
teacher_time: "4 minutes"
tags: ["experiential-learning", "simulation", "service-learning", "Dewey", "reflection", "direct-experience"]
---

# Experiential Learning Cycle Designer

## What This Skill Does

Designs a four-phase experiential learning cycle that moves students from direct experience, through structured reflection, to conceptual understanding, and then to application in a new context. The cycle draws on Dewey's (1938) foundational principle that education is the reconstruction of experience — learning occurs not from experience itself but from REFLECTING on experience and connecting it to broader understanding. The skill designs each phase deliberately: the experience must be genuinely engaging and educationally relevant (not just "fun"), the reflection must be structured (not just "how did that feel?"), the conceptualisation must connect experience to transferable principles, and the application must test understanding in a new situation. The output includes the complete four-phase cycle, with detailed design for each phase and the transitions between them. AI is specifically valuable here because designing effective experiential learning requires balancing engagement (the experience must be compelling) with rigour (it must produce genuine learning, not just enjoyable activity).

## Evidence Foundation

Dewey (1938) established the foundational principle: experience alone does not educate. "Mis-educative" experiences — those that produce no learning, reinforce misconceptions, or arrest further growth — are as common as educative ones. The difference is whether the experience is connected to reflection, conceptualisation, and future application. Hattie (2009) reported an effect size of d=0.33 for simulation and gaming as educational strategies — a moderate positive effect that suggests simulations work when well-designed but are not a silver bullet. The effect is strongest when simulations include structured debriefing (reflection) and explicit connection to learning objectives (conceptualisation). Billig (2000) reviewed research on service learning, finding moderate positive effects on academic achievement, civic responsibility, and personal development — but ONLY when the service experience was connected to curriculum content through structured reflection. Service without reflection produced community benefit but not learning. Boud, Keogh & Walker (1985) developed a detailed model of reflective learning from experience, arguing that reflection involves: returning to the experience (what happened?), attending to feelings (what did I feel?), and re-evaluating the experience (what does it mean?). Without this structured process, experiences remain as anecdotes rather than becoming learning. Wurdinger & Carlson (2010) documented five experiential approaches that produce learning: active learning, problem-based learning, project-based learning, service learning, and place-based learning — all of which share the common structure of experience followed by reflection followed by conceptualisation followed by application.

## Input Schema

The teacher must provide:
- **Learning objective:** What students need to learn. *e.g. "Understanding supply and demand — Year 10 Economics" / "Empathy and perspective-taking — Year 8 PSHE" / "The water cycle — Year 5 Science" / "How Parliament works — Year 9 Citizenship"*
- **Experience type:** What kind of experience is available. *e.g. "Simulation — we can run a classroom marketplace where students buy and sell" / "Role play — students can take on roles in a mock Parliament" / "Field trip — we're visiting a water treatment plant next week" / "Community project — students are planning a fundraising event for a local charity"*

Optional (injected by context engine if available):
- **Student level:** Year group
- **Subject area:** The curriculum subject
- **Time available:** Duration for the full cycle
- **Resources available:** What's available
- **Prior knowledge:** What students already know

## Prompt

```
You are an expert in experiential learning design, with deep knowledge of Dewey's (1938) philosophy of experience and education, Hattie's (2009) evidence on simulation and gaming, Billig's (2000) research on service learning, Boud, Keogh & Walker's (1985) model of reflective learning, and Wurdinger & Carlson's (2010) five experiential approaches. You understand that experiential learning is NOT "learning by doing" in the vague sense — it is a rigorous four-phase cycle where each phase serves a specific pedagogical function, and the learning happens in the REFLECTION and CONCEPTUALISATION, not in the experience itself.

CRITICAL PRINCIPLES:
- **Experience without reflection is just activity.** Dewey was explicit: not all experience is educative. A simulation that students enjoy but don't reflect on produces entertainment, not learning. A field trip without structured follow-up produces memories, not understanding. The REFLECTION PHASE is where learning happens — design it with as much care as the experience itself.
- **Reflection must be structured, not generic.** "How did that go?" is not reflection. "What happened when you raised the price? How did the buyers respond? Why do you think that happened? What principle does this illustrate?" is structured reflection that extracts learning from experience.
- **Conceptualisation connects the specific to the general.** The experience is specific (THIS simulation, THIS field trip). The learning must be general (the principle of supply and demand, the process of water purification). Conceptualisation explicitly bridges: "In our simulation, X happened. In the real economy, the same principle applies — here's how."
- **Application tests transfer.** If students can only explain what happened in the simulation but cannot apply the principle to a new situation, they learned the simulation, not the concept. The application phase provides a new context where students must use their learning.
- **Design the experience for learning, not just engagement.** A marketplace simulation where students have fun but the supply-demand dynamics are invisible has failed. The experience must be designed so that the target concept is EMBEDDED in the experience — students encounter it through doing, even if they don't yet have the language for it.

Your task is to design an experiential learning cycle for:

**Learning objective:** {{learning_objective}}
**Experience type:** {{experience_type}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, infer from the learning objective.
**Subject area:** {{subject_area}} — if not provided, infer from the learning objective.
**Time available:** {{time_available}} — if not provided, design for a 2-lesson sequence (one for experience, one for reflection and conceptualisation, with application as homework or a third lesson).
**Resources available:** {{resources_available}} — if not provided, design with minimal resources.
**Prior knowledge:** {{prior_knowledge}} — if not provided, design the experience to introduce the concept rather than reinforce it.

Return your output in this exact format:

## Experiential Learning Cycle: [Learning Objective]

**Learning objective:** [What students will understand]
**Experience:** [The type of direct experience]
**Key concept embedded in experience:** [The specific principle or understanding that the experience makes tangible]

### Phase 1 — Experience (Concrete Experience)

**The experience:** [What students do — detailed, step-by-step]
**What makes this experience educative:** [How the learning objective is embedded in the activity — what students encounter through doing]
**Teacher role during experience:** [What the teacher does — facilitates, observes, takes notes for the reflection phase]

### Phase 2 — Reflection (Reflective Observation)

**Structured reflection questions:** [Specific questions that extract learning from the experience — not "how did it go?" but targeted questions about what happened and why]
**Reflection format:** [How reflection is structured — whole-class discussion, written journal, paired dialogue, recorded observations]
**Key moments to revisit:** [Specific moments from the experience that the teacher draws attention to — "Remember when X happened? Why do you think that occurred?"]

### Phase 3 — Conceptualisation (Abstract Conceptualisation)

**From experience to principle:** [How the teacher helps students move from "what happened in our activity" to "what this tells us about [the concept]"]
**Theory/principle introduced:** [The formal knowledge that explains what students experienced]
**Connection made explicit:** [How the teacher links the experience directly to the theory — "In our simulation, you experienced X. The economic term for this is Y. It happens in real life when Z."]

### Phase 4 — Application (Active Experimentation)

**New context:** [A different situation where students apply the principle they've learned]
**Application task:** [What students do to test their understanding in this new context]
**How to know it worked:** [Evidence that students can transfer the learning beyond the original experience]

### Transitions Between Phases

[How to move smoothly from each phase to the next — the "glue" that makes the cycle coherent]

**Self-check before returning output:** Verify that (a) the experience genuinely embeds the learning objective, (b) the reflection is structured with specific questions, (c) the conceptualisation explicitly connects experience to transferable principle, (d) the application tests transfer to a new context, and (e) each phase serves a distinct pedagogical function.
```

## Example Output

**Scenario:** *Learning objective: "Understanding supply and demand — Year 10 Economics. Students need to understand: when supply is limited and demand is high, prices rise; when supply exceeds demand, prices fall; and that this mechanism operates through the independent decisions of buyers and sellers, not through central planning." / Experience type: "Simulation — classroom marketplace where students buy and sell goods" / Time available: "2 lessons (50 minutes each)" / Prior knowledge: "Students have not yet studied supply and demand formally — this is their introduction to the concept"*

---

## Experiential Learning Cycle: Supply and Demand

**Learning objective:** Understanding the supply-demand price mechanism — how prices emerge from the independent decisions of buyers and sellers
**Experience:** Classroom marketplace simulation
**Key concept embedded in experience:** When many buyers want a scarce good, the price rises. When goods are plentiful and buyers are few, the price falls. This happens without anyone deciding "the price should be X" — it emerges from interaction.

### Phase 1 — Experience (Lesson 1: 40 minutes)

**The experience:**

*Setup (10 minutes):*
Divide the class into Buyers (15) and Sellers (15). Each Seller receives 5 cards representing "goods" (coloured cards — nothing elaborate). Each Buyer receives a "budget" of classroom currency (paper tokens — 10 tokens each).

**Round 1 — Scarcity:** Each Seller has only 2 goods to sell. Each Buyer wants to buy 3 goods. (Demand exceeds supply.) Sellers set their own prices. Buyers negotiate individually with Sellers. Trading is open — everyone moves around the room, negotiating simultaneously. Allow 5 minutes. At the end, record all transaction prices on the board.

**Round 2 — Surplus:** Each Seller now has 8 goods to sell. Each Buyer still wants only 3 goods. (Supply exceeds demand.) Same rules — Sellers set prices, open trading. 5 minutes. Record all transaction prices.

**Round 3 — Market shock:** Mid-way through the round, the teacher announces: "Breaking news — the government has announced that these goods are now essential for the upcoming exam. Everyone needs at least 5." (Demand spike.) Observe what happens to prices. 5 minutes. Record prices.

*What makes this experience educative:*
- In Round 1, students EXPERIENCE price rises — Sellers discover they can charge high prices because Buyers are competing for scarce goods. The price mechanism is not explained; it's encountered.
- In Round 2, students EXPERIENCE price drops — Sellers discover they must lower prices because Buyers have many options. Sellers who refuse to drop prices don't sell.
- In Round 3, students EXPERIENCE a demand shock — prices that were low suddenly spike when demand increases. The dynamics are visible and felt.

**Teacher role during experience:** Do NOT explain what's happening. Circulate, observe, and take notes: which Sellers raised prices? Which Buyers walked away? What happened to prices when supply increased? These observations fuel the reflection. If students complain about "unfair" prices, note this — it's pedagogically valuable.

### Phase 2 — Reflection (Lesson 1: 10 minutes + Lesson 2: 15 minutes)

**End of Lesson 1 — Quick capture (10 minutes):**
Before the experience fades, capture immediate reflections:
- "What happened to prices in Round 1? Were they high or low? Why?"
- "What happened in Round 2? Why did prices change?"
- "When I announced the demand shock in Round 3, what did Sellers do? Why?"
- "Did anyone decide what the 'correct' price should be, or did it just... happen?"

Record key observations on the board. Don't explain yet — just gather.

**Beginning of Lesson 2 — Structured reflection (15 minutes):**
Display the transaction price data from all three rounds on a graph (price on Y-axis, round on X-axis). Students see the pattern: prices high in Round 1, low in Round 2, spiking in Round 3.

Structured reflection questions:
1. "In Round 1, why were Sellers able to charge high prices? What was their power?" (They had something Buyers wanted and couldn't get elsewhere — scarcity.)
2. "In Round 2, why did prices fall even though no one TOLD Sellers to lower their prices?" (Buyers had options. A Seller charging too much got no customers. Competition forced prices down.)
3. "Did any Buyers feel frustrated in Round 1? Did any Sellers feel frustrated in Round 2? Why?" (This surfaces the emotional dimension — the experience of market power and market vulnerability.)
4. "Who decided the prices? Was there a central authority?" (No one decided. Prices emerged from thousands of individual negotiations. This is the key insight.)
5. "In Round 3, the same goods suddenly became more valuable. Did the goods themselves change? What changed?" (The goods didn't change — the DEMAND changed. Value is not inherent in the object; it depends on how much people want it.)

### Phase 3 — Conceptualisation (Lesson 2: 20 minutes)

**From experience to principle:**
"What you just experienced has a name in economics. Let me introduce the language for what you already KNOW."

The teacher introduces:
- **Supply:** The quantity of a good that Sellers are willing to sell at a given price. In Round 1, supply was LOW (2 per Seller). In Round 2, supply was HIGH (8 per Seller).
- **Demand:** The quantity of a good that Buyers want to purchase at a given price. In Round 1 and 2, demand was moderate. In Round 3, demand SPIKED.
- **Price mechanism:** Prices adjust to balance supply and demand. No one decides — it EMERGES from the interaction of buyers and sellers.
- **Supply curve and demand curve:** The teacher sketches the classic diagram. "Remember Round 1? That's here on the graph — low supply, high demand, price is here. Round 2? Here — high supply, same demand, price drops. Round 3? Here — demand curve shifts right, price jumps."

**Connection made explicit:** "In our simulation, you charged high prices when your goods were scarce. In the real economy, the same principle explains why concert tickets cost more when the band is popular, why house prices rise when many people want to live in an area, and why petrol prices spike when oil supply is disrupted. The mechanism is the same — you've already experienced it."

### Phase 4 — Application (Lesson 2: 15 minutes)

**New context:** Students apply supply-demand analysis to a real-world scenario they have NOT experienced:

"Read this news article: 'House prices in [local area] rise by 15% as new tech company opens headquarters.' Using what you learned from the marketplace simulation, explain: Why did house prices rise? Draw a supply-demand diagram. What would happen to house prices if the tech company then built 500 new homes for its workers?"

**Application task:** Students write a paragraph explanation using economic terminology (supply, demand, price mechanism, scarcity, surplus) and draw a labelled supply-demand diagram. They must connect the real-world scenario to the principle they experienced in the simulation.

**How to know it worked:** Students who can explain the house price scenario using supply-demand analysis have transferred their learning from the simulation to a new context. Students who can only describe what happened in the simulation but cannot apply the principle to the house price scenario have learned the activity, not the concept — they need more practice with the conceptualisation and application phases.

### Transitions Between Phases

**Experience → Reflection:** The transition is the price data. Recording transaction prices on the board creates a SHARED DATA SET that everyone can see. This data is the raw material for reflection: "Look at the data. What pattern do you see?"

**Reflection → Conceptualisation:** The transition is the question: "What you noticed has a name in economics." Students have already articulated the insight in their own words ("prices went up because everyone wanted them"). The teacher now introduces the formal vocabulary that names what they already understand.

**Conceptualisation → Application:** The transition is the challenge: "Can you use this principle to explain something you HAVEN'T experienced?" This tests whether the learning has moved from specific (our simulation) to general (the principle of supply and demand).

---

## Known Limitations

1. **Kolb's (1984) experiential learning cycle, while widely cited, has significant theoretical and empirical limitations.** This skill draws on the four-phase cycle structure (experience → reflection → conceptualisation → application) but does NOT claim this as Kolb's model specifically. Kolb's theory has been criticised for: (a) weak empirical validation — the cycle is intuitively appealing but has not been rigorously tested, (b) cultural bias — the cycle assumes a Western, individualistic model of learning where personal experience is the starting point, (c) the "learning styles" component (Kolb's LSI) has been repeatedly debunked (Coffield et al., 2004), and (d) the cycle implies a fixed sequence when in practice learners may enter at any point. This skill uses the four-phase structure as a practical planning framework, grounded in Dewey (1938) and Boud et al. (1985) rather than Kolb specifically.

2. **Simulations simplify reality.** The classroom marketplace is a simulation of supply and demand, not the real thing. Real markets involve information asymmetry, externalities, government regulation, monopoly power, behavioural biases, and historical context that a classroom simulation cannot replicate. The simulation teaches the BASIC mechanism — but students should be told explicitly: "The real economy is more complex than our simulation. What we've learned is the foundation — the principle that supply and demand affect prices. In the coming weeks, we'll add the complications."

3. **The effect size for simulation-based learning is moderate (Hattie, d=0.33).** This is a positive effect but not a large one, and it depends heavily on the quality of the debriefing. Simulations without structured reflection consistently produce weaker learning outcomes than simulations WITH structured reflection. The reflection phase is not optional — it is where the learning happens. An engaging simulation followed by "OK, that was fun, now open your textbooks" wastes the experiential opportunity.
