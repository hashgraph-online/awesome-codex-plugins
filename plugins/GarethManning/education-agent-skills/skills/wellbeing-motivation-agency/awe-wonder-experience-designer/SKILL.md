---
# AGENT SKILLS STANDARD FIELDS (v2)
name: awe-wonder-experience-designer
description: "Design a moment of awe or wonder that hooks curiosity and deepens emotional engagement with content. Use when opening units, introducing surprising material, or reigniting student interest."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "wellbeing-motivation-agency/awe-wonder-experience-designer"
skill_name: "Awe & Wonder Experience Designer"
domain: "wellbeing-motivation-agency"
version: "1.0"
evidence_strength: "emerging"
evidence_sources:
  - "Keltner & Haidt (2003) — Approaching awe, a moral, spiritual, and aesthetic emotion"
  - "Keltner (2023) — Awe: the new science of everyday wonder and how it can transform your life"
  - "Valdesolo & Graham (2014) — Awe, uncertainty, and agency detection"
  - "Shiota, Keltner & Mossman (2007) — The nature of awe: elicitors, appraisals, and effects on self-concept"
  - "Gottlieb, Keltner & Lombrozo (2018) — Awe as a scientific emotion"
input_schema:
  required:
    - field: "lesson_content"
      type: "string"
      description: "The subject content and learning objectives for the lesson"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "awe_trigger"
      type: "string"
      description: "A specific element the teacher wants to build the awe moment around"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: class interests, engagement patterns, prior knowledge"
    - field: "available_resources"
      type: "string"
      description: "Technology, space, materials available"
    - field: "lesson_duration"
      type: "string"
      description: "Length of the lesson"
output_schema:
  type: "object"
  fields:
    - field: "awe_moment_design"
      type: "object"
      description: "The designed awe experience — what students encounter, how it is presented, where it sits in the lesson"
    - field: "vastness_element"
      type: "string"
      description: "What creates the sense of vastness — physical, temporal, conceptual, or social"
    - field: "accommodation_bridge"
      type: "string"
      description: "How the awe moment connects to the learning — the 'need to know' that awe creates"
    - field: "teaching_sequence"
      type: "object"
      description: "How to sequence the lesson so the awe moment drives inquiry rather than just entertainment"
chains_well_with:
  - "perma-based-lesson-designer"
  - "motivation-diagnostic-task-redesign"
  - "lesson-opening-designer"
  - "critical-thinking-task-designer"
teacher_time: "3 minutes"
tags: ["awe", "wonder", "curiosity", "Keltner", "engagement", "positive-emotion"]
---

# Awe & Wonder Experience Designer

## What This Skill Does

Designs a moment of awe or wonder within a lesson — an experience that stops students in their tracks, creates a sense of vastness (something bigger, more complex, or more beautiful than expected), and triggers the "need for accommodation" (the drive to update one's mental model to make sense of something that doesn't fit). The critical principle is that awe is not a decorative add-on — it is a cognitive event that opens students to new information, reduces fixed thinking, and creates the motivation to learn. The output includes the awe moment design, an analysis of what creates the sense of vastness, a bridge connecting the awe moment to the learning objective (so wonder leads to inquiry, not just entertainment), and a teaching sequence that uses the awe moment to drive deeper engagement with the content. AI is specifically valuable here because designing awe moments requires both subject expertise (knowing what IS genuinely astonishing about the content) and psychological knowledge (knowing how to present it for maximum impact) — and because teachers, familiar with their content, may have lost the capacity to see what is awe-inspiring about material they've taught dozens of times.

## Evidence Foundation

Keltner & Haidt (2003) defined awe as an emotion with two core features: perceived vastness (the stimulus is larger, more complex, or more powerful than the observer's current frame of reference) and a need for accommodation (the observer's existing mental model cannot account for what they're experiencing, creating a drive to update it). Keltner (2023) expanded this to identify eight categories of awe elicitors: moral beauty, collective effervescence, nature, music, visual design, spirituality, life and death, and epiphany (sudden understanding). Shiota, Keltner & Mossman (2007) showed that awe reduces the self — the "small self" experience — which decreases self-focus and increases openness to new information. In educational contexts, this means awe can break students out of fixed patterns ("I already know this," "This is boring," "I can't do this") by making them feel part of something larger. Gottlieb, Keltner & Lombrozo (2018) demonstrated that awe functions as a "scientific emotion" — it motivates explanation-seeking, increases curiosity, and promotes deeper processing. Valdesolo & Graham (2014) found that awe increases tolerance for uncertainty — a crucial disposition for learning, which requires being comfortable with not-yet-knowing.

## Input Schema

The teacher must provide:
- **Lesson content:** What the lesson is about. *e.g. "Year 7 Science: the scale of the universe — understanding the relative sizes and distances of objects in the solar system" / "Year 10 History: the trenches of WW1 — understanding conditions and experiences of soldiers" / "Year 8 Maths: probability — understanding that seemingly random events follow predictable patterns at scale"*
- **Student level:** Year group. *e.g. "Year 7"*

Optional (injected by context engine if available):
- **Subject area:** The curriculum subject
- **Awe trigger:** A specific element to build around
- **Student profiles:** Class interests, engagement patterns
- **Available resources:** Technology, space, materials
- **Lesson duration:** Length of lesson

## Prompt

```
You are an expert in the psychology of awe and its application to education, with deep knowledge of Keltner & Haidt's (2003) model of awe, Keltner's (2023) eight categories of awe elicitors, Gottlieb, Keltner & Lombrozo's (2018) research on awe as a scientific emotion, and the cognitive effects of awe (reduced self-focus, increased openness, tolerance for uncertainty, motivation to learn).

IMPORTANT: Awe is not the same as "cool" or "interesting." Awe requires VASTNESS — something that exceeds the student's current frame of reference — and a NEED FOR ACCOMMODATION — the student's existing understanding cannot account for what they're experiencing. A flashy video might be interesting; the realisation that the observable universe contains more stars than grains of sand on every beach on Earth is awe-inducing because it breaks the student's sense of scale.

IMPORTANT: Awe must serve learning, not replace it. A lesson that starts with an amazing video and then reverts to a worksheet has used awe as entertainment, not as a learning driver. The awe moment should create a NEED TO KNOW that the rest of the lesson satisfies. Wonder without learning is spectacle; learning without wonder is drudgery; awe that drives inquiry is education at its best.

Your task is to design an awe moment for:

**Lesson content:** {{lesson_content}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Subject area:** {{subject_area}} — if not provided, infer from the content.
**Awe trigger:** {{awe_trigger}} — if not provided, identify the most awe-inducing element of the content.
**Student profiles:** {{student_profiles}} — if not provided, design for a typical class.
**Available resources:** {{available_resources}} — if not provided, assume a standard classroom with a projector and internet access.
**Lesson duration:** {{lesson_duration}} — if not provided, assume 50–60 minutes.

Apply these principles:

1. **Identify the genuine source of awe in the content (Keltner & Haidt, 2003):**
   - Every subject contains something genuinely vast, complex, or beautiful — but familiarity can blind us to it.
   - Science: the scale of the universe, the complexity of a cell, the age of the Earth.
   - History: the scale of human suffering, the courage of individuals, the chain of consequences from a single event.
   - Mathematics: the emergence of patterns from chaos, the infinite, the unreasonable effectiveness of mathematics.
   - English: the power of a single sentence to change how you see the world.
   - Art: the capacity of humans to create beauty from nothing.

2. **Design for vastness (Shiota et al., 2007):**
   - Physical vastness: scale, size, distance, number.
   - Temporal vastness: deep time, long chains of cause and effect.
   - Conceptual vastness: the realisation that something is far more complex or interconnected than imagined.
   - Social vastness: collective human achievement, sacrifice, or creativity.

3. **Create the need for accommodation (Keltner & Haidt, 2003):**
   - The awe moment should leave students thinking: "I didn't know that was possible" or "I can't quite fit this into what I already knew."
   - This dissonance IS the learning opportunity — the rest of the lesson should help students build a new, more accurate mental model.

4. **Bridge awe to inquiry (Gottlieb et al., 2018):**
   - After the awe moment, channel the wonder into specific questions: "How is that possible?" / "Why does that happen?" / "What would we need to understand to explain this?"
   - The lesson content becomes the ANSWER to the questions that awe provokes.

5. **Protect the moment:**
   - Don't over-explain before the reveal. Don't tell students what they're about to see is "amazing" — let them feel it themselves.
   - Use silence after the moment. Let the vastness land. Don't rush to the next activity.
   - Genuine awe changes the emotional state of the room — respect that shift.

Return your output in this exact format:

## Awe Moment Design: [Lesson Topic]

**Content:** [What students learn]
**For:** [Student level]

### The Awe Moment

[Detailed description of the moment — what students experience, how it's presented, what makes it awe-inducing]

### Vastness Element

[What creates the sense of vastness and which category of awe it uses]

### Accommodation Bridge

[How the awe moment creates a "need to know" that the lesson content satisfies]

### Teaching Sequence

[How the awe moment fits into the lesson — what comes before, the moment itself, and what comes after]

### Protecting the Moment

[How to present the awe moment without diluting it — timing, silence, teacher language]

**Self-check before returning output:** Verify that (a) the awe moment involves genuine vastness, not just "something interesting," (b) the moment connects directly to the learning objective, (c) the bridge from awe to inquiry is explicit, (d) the moment is protected with appropriate pacing and silence, and (e) the lesson uses awe to drive learning, not as decoration.
```

## Example Output

**Scenario:** *Lesson content: "Year 7 Science: the scale of the solar system — understanding the relative sizes of planets and distances between them" / Student level: "Year 7" / Available resources: "School field available, standard classroom, projector"*

---

## Awe Moment Design: The Scale of the Solar System

**Content:** Relative sizes and distances in the solar system
**For:** Year 7 Science

### The Awe Moment

Take the class to the school field. Place a football (22cm diameter) at one end. Tell students: "This football is the Sun. I want you to guess — if the Sun is this football, how big is the Earth? And how far away is it?"

Take guesses. Students will typically guess the Earth is a marble and "over there" (pointing 5–10 metres away).

Then reveal: the Earth, at this scale, is a peppercorn — 2mm across. Hold it up. Let them see how small it is against the football. (Silence. Don't explain yet. Let them feel the scale difference.)

Then: "And how far away?" Walk. Keep walking. The Earth is 24 metres from the Sun at this scale. Students watch you walk — and walk — and walk. When you reach the point and hold up the peppercorn, the Sun-football is distant. The Earth is tiny. The distance is vast.

Now: "Jupiter?" Jupiter is a conker — much bigger than the peppercorn, but still small against the football. And it's 126 metres away. Walk. The football-Sun is barely visible from Jupiter's position.

Finally: "The nearest star — Proxima Centauri? At this scale, it would be another football. It would be in..." (pause) "...Madrid." (Or your nearest equivalent — approximately 6,500 kilometres at this scale.)

Silence. Let the vastness land.

### Vastness Element

**Physical vastness — scale.** The awe comes from the visceral, bodily experience of walking the distance. Reading "the Earth is 150 million km from the Sun" is a fact. Walking 24 metres while holding a peppercorn and looking back at a distant football is an EXPERIENCE. The scale exceeds what the human brain can intuitively grasp — which is exactly Keltner's definition of vastness. The nearest star being in Madrid (at this scale) produces the accommodation response: "I genuinely cannot comprehend how big space is." That's awe.

### Accommodation Bridge

The awe moment creates specific questions:
- "If the Earth is that small and that far away, how do we even know what's out there?"
- "Why do the planets orbit the Sun if they're that far apart?"
- "How long would it take to travel between them?"
- "If the nearest star is that far away, are we alone?"

The rest of the lesson uses these questions to teach the curriculum content: relative sizes (quantitative data), orbital mechanics (why gravity works at these distances), and the structure of the solar system. The awe moment makes the CONTENT feel necessary — students want to understand what they've just experienced.

### Teaching Sequence

**Phase 1 — The Awe Moment (15 minutes):**
On the field. Football → peppercorn → walking the distances. No explanation, no data, no textbook. Just the experience and the silence that follows.

**Phase 2 — Channelling the Wonder (5 minutes):**
Back in the classroom. "What questions do you have after that?" Collect questions on the board. Group them. Students will have asked most of the questions you were planning to teach anyway — but now they WANT the answers.

**Phase 3 — Building Understanding (25 minutes):**
Use the questions to structure the learning: relative sizes (with data table — converting the field model to real measurements), distances (introducing astronomical units and light-years), and the structure of the solar system. Every piece of data is connected back to the field experience: "Remember how far you had to walk to reach Jupiter? That's 778 million kilometres."

**Phase 4 — Reflection (5 minutes):**
"Write one sentence that captures what surprised you most today. Then write one question you still want answered." Collect. Use the questions to plan the next lesson.

### Protecting the Moment

1. **Don't pre-announce the scale.** Don't say "We're going to do something amazing on the field today." Just go to the field, place the football, and start. The surprise IS the awe.

2. **Use silence after each reveal.** When you hold up the peppercorn: silence. When you reach the 24-metre mark: silence. When you say "Madrid": silence. Let the vastness register in the body before engaging the intellect. The temptation is to immediately start explaining — resist it for 10 seconds.

3. **Don't trivialise with humour.** Awe is a serious emotion. Students may laugh nervously (this is a normal response to something overwhelming). Don't match the laughter with a joke. A calm, quiet "I know. It's hard to take in, isn't it?" validates the emotion without deflating it.

4. **Let students express their reaction.** Some will say "Wow." Some will say "That's insane." Some will be quiet. All are appropriate responses to genuine awe. Don't police the emotional response — channel it into questions.

---

## Known Limitations

1. **Awe is subjective.** What produces awe in one student may be merely interesting to another. The scale model works for most students because it involves physical vastness — but students who have already encountered this demonstration may not experience the same awe. The teacher must know their students and select awe triggers that match the group's prior experience.

2. **Awe moments are rare by nature.** If every lesson starts with an "awe moment," the effect diminishes rapidly. Awe should be used strategically — perhaps once per unit or topic — at points where the content genuinely warrants it. Overuse turns awe into spectacle.

3. **The evidence base for awe in education is emerging, not established.** Keltner's research is robust in psychology, but its application to classroom learning has limited controlled studies. The principles are sound (awe increases openness, curiosity, and tolerance for uncertainty — all valuable for learning), but the specific claim that "awe improves academic outcomes" requires more research. This skill is based on well-established emotion science applied to educational contexts, not on direct educational RCTs.
