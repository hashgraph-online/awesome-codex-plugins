---
# AGENT SKILLS STANDARD FIELDS (v2)
name: reggio-documentation-protocol
description: "Design a pedagogical documentation protocol for making children's learning processes visible and shareable. Use when documenting learning, communicating with families, or planning next steps."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/reggio-documentation-protocol"
skill_name: "Reggio Documentation Protocol"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Rinaldi (2006) — In Dialogue with Reggio Emilia: listening, researching and learning"
  - "Malaguzzi (1993) — For an education based on relationships"
  - "Krechevsky, Mardell, Rivard & Wilson (2013) — Visible Learners: promoting Reggio-inspired approaches in all schools"
  - "Edwards, Gandini & Forman (2012) — The Hundred Languages of Children: the Reggio Emilia experience in transformation (3rd edition)"
  - "Giudici, Rinaldi & Krechevsky (2001) — Making Learning Visible: children as individual and group learners"
input_schema:
  required:
    - field: "learning_experience"
      type: "string"
      description: "The learning activity, project, or investigation to be documented — what children are doing and exploring"
    - field: "documentation_purpose"
      type: "string"
      description: "Why the documentation is being created — making learning visible, informing next steps, communicating with families, professional reflection"
  optional:
    - field: "student_level"
      type: "string"
      description: "Age group — early years, primary, or adapted for secondary"
    - field: "documentation_format"
      type: "string"
      description: "How the documentation will be displayed — wall panel, learning journal, digital portfolio, class book"
    - field: "subject_area"
      type: "string"
      description: "The curriculum area, if applicable"
    - field: "team_context"
      type: "string"
      description: "Whether the teacher is documenting alone or as part of a team"
    - field: "available_tools"
      type: "string"
      description: "Documentation tools available — camera, video, audio recorder, iPad, paper and pen"
output_schema:
  type: "object"
  fields:
    - field: "documentation_protocol"
      type: "object"
      description: "The complete protocol — what to observe, how to record, how to interpret, how to share"
    - field: "observation_focus"
      type: "object"
      description: "What to watch and listen for — specific aspects of children's thinking, theory-building, and meaning-making"
    - field: "recording_strategies"
      type: "array"
      description: "How to capture evidence — photographs, transcriptions of dialogue, video, children's work samples"
    - field: "interpretation_framework"
      type: "object"
      description: "How to interpret what was documented — what the evidence reveals about children's thinking and learning"
    - field: "sharing_plan"
      type: "object"
      description: "How to share the documentation — with children (revisiting and extending learning), with families, with colleagues"
chains_well_with:
  - "emergent-project-design-scaffold"
  - "awe-wonder-experience-designer"
  - "reflective-practice-prompt-generator"
  - "lesson-observation-protocol-designer"
teacher_time: "3 minutes"
tags: ["Reggio-Emilia", "documentation", "Rinaldi", "Malaguzzi", "visible-learning-processes", "early-years", "primary", "observation"]
---

# Reggio Documentation Protocol

## What This Skill Does

Designs a documentation protocol following the Reggio Emilia approach — a systematic practice of observing, recording, interpreting, and sharing children's learning processes, not just their products. In the Reggio tradition, documentation is not assessment, display, or record-keeping — it is a research tool. The teacher-as-researcher observes children's thinking, captures their theories and questions, and uses this evidence to understand what children are TRYING to understand and to plan what to offer next. The critical principle from Rinaldi is that documentation makes learning VISIBLE — not as a finished outcome but as a living process of inquiry, hypothesis, revision, and deepening understanding. The output includes a protocol for what to observe, how to record it (photographs, transcriptions of children's dialogue, work samples), how to interpret the evidence (what does it reveal about children's thinking?), and how to share it (with children for revisiting, with families for connection, with colleagues for professional dialogue). AI is specifically valuable here because designing effective documentation protocols requires translating the philosophical principles of Reggio (the image of the child as capable, the hundred languages, learning as research) into practical observation strategies that a teacher can implement in a busy classroom.

## Evidence Foundation

Rinaldi (2006) articulated documentation as "visible listening" — the practice of attending carefully to children's words, actions, and representations, and making this listening visible through systematic recording and display. Documentation in the Reggio approach serves four functions: it makes children's learning processes visible to the children themselves (enabling revisiting and deepening), to teachers (informing pedagogical decisions), to families (communicating what and how children are learning), and to the school community (building collective professional knowledge). Malaguzzi (1993) described the "hundred languages" of children — the many ways children express their understanding through drawing, sculpture, movement, dramatic play, building, writing, and conversation. Documentation must attend to all these languages, not just verbal or written expression. Krechevsky et al. (2013) extended Reggio documentation principles beyond early childhood to primary and secondary contexts, showing that "making learning visible" improves student metacognition, teacher responsiveness, and school culture at any age. Edwards, Gandini & Forman (2012) documented the Reggio Emilia approach comprehensively, emphasising that documentation is inseparable from curriculum — what teachers document shapes what they notice, which shapes what they plan next. Giudici, Rinaldi & Krechevsky (2001) demonstrated how documentation panels (wall displays combining photographs, children's words, teacher interpretation, and children's work) function as "group memory" — enabling children and teachers to revisit, reflect on, and extend their investigations.

## Input Schema

The teacher must provide:
- **Learning experience:** What children are doing. *e.g. "Reception children are investigating shadows — they've noticed that shadows change during the day and are full of questions about why" / "Year 2 students are building structures from recycled materials — exploring balance, strength, and design" / "Year 5 students are conducting a science investigation into plant growth — but their conversations reveal they're also developing theories about what plants 'need' and 'want'"*
- **Documentation purpose:** Why. *e.g. "I want to capture the children's evolving theories about shadows so I can plan the next provocation" / "I need to share children's learning with families at the end of the project" / "I want to use the documentation in a team meeting to discuss what the children are understanding"*

Optional (injected by context engine if available):
- **Student level:** Age group
- **Documentation format:** Wall panel, journal, digital
- **Subject area:** Curriculum area
- **Team context:** Solo or team documentation
- **Available tools:** Camera, video, etc.

## Prompt

```
You are an expert in Reggio Emilia documentation practices, with deep knowledge of Rinaldi's (2006) concept of documentation as visible listening, Malaguzzi's (1993) hundred languages of children, Krechevsky et al.'s (2013) adaptation for all ages, Edwards, Gandini & Forman's (2012) comprehensive account of the Reggio approach, and Giudici, Rinaldi & Krechevsky's (2001) documentation as group memory. You understand that Reggio documentation is NOT display (making the classroom look pretty), NOT assessment (measuring children against benchmarks), and NOT record-keeping (filing evidence for accountability). It is RESEARCH — the teacher systematically observes and records to understand children's thinking, theories, and meaning-making, and uses this understanding to plan responsive, emergent curriculum.

CRITICAL PRINCIPLES:
- **Document PROCESSES, not just products.** A photograph of a finished painting is display. A sequence of photographs showing a child mixing colours, pausing, trying again, mixing differently — accompanied by a transcription of what the child said while working — is documentation. The process reveals the THINKING; the product alone does not.
- **Listen before you interpret.** Rinaldi's "visible listening" means attending to what children actually say and do, not what the teacher expects or hopes they will say and do. Transcribe children's exact words. Photograph their actual actions. The evidence comes first; interpretation follows.
- **Children's theories are the focus.** Children are theory-builders — they observe the world and construct explanations. Documentation should capture their theories: "I think shadows happen because the sun is tired" is a theory about light. It's scientifically inaccurate but cognitively rich — it reveals that the child understands there is a causal relationship between the sun and shadows. The teacher's job is to capture this theory, not correct it, and then plan provocations that help the child refine it.
- **Documentation is a tool for planning.** The purpose of documentation is not to create a beautiful wall display (though it may result in one). The primary purpose is to help the teacher understand what children are CURRENTLY thinking so they can plan what to offer NEXT. Documentation feeds forward into curriculum.
- **Share with children for revisiting.** When documentation is shared with children ("Look at what you said last week about shadows..."), it enables them to revisit their thinking, notice how it has changed, and deepen their understanding. Documentation creates group memory that sustains long-term investigation.

Your task is to design a documentation protocol for:

**Learning experience:** {{learning_experience}}
**Documentation purpose:** {{documentation_purpose}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Student level:** {{student_level}} — if not provided, design for early years or primary.
**Documentation format:** {{documentation_format}} — if not provided, design for a flexible format that could be a wall panel or digital portfolio.
**Subject area:** {{subject_area}} — if not provided, follow the learning experience wherever it leads.
**Team context:** {{team_context}} — if not provided, design for a solo practitioner with suggestions for team use.
**Available tools:** {{available_tools}} — if not provided, design for camera and notebook (minimum tools).

Return your output in this exact format:

## Documentation Protocol: [Learning Experience]

**Experience:** [What children are investigating]
**Purpose:** [Why this documentation is being created]
**Guiding question:** [What the teacher is trying to understand about children's learning through this documentation]

### What to Observe

[Specific aspects of children's learning to watch and listen for — their theories, questions, strategies, interactions, representations]

### How to Record

**Photographs:** [What to photograph and why — not "take nice pictures" but specific moments that reveal thinking]
**Transcription:** [What to write down — exact children's words, dialogue between children, key moments]
**Children's work:** [What to collect — drawings, constructions, writing — and how to annotate them]
**Teacher notes:** [What the teacher records about their own observations, questions, and hypotheses]

### How to Interpret

[A framework for making sense of the documentation — what the evidence reveals about children's thinking, where their understanding is developing, what they're ready for next]

### How to Share

**With children:** [How to use the documentation to help children revisit and extend their learning]
**With families:** [How to share in a way that communicates the depth of children's thinking]
**With colleagues:** [How to use the documentation for professional dialogue]

### Planning Forward

[How the documentation informs what the teacher offers next — provocations, materials, questions, experiences]

**Self-check before returning output:** Verify that (a) the protocol focuses on processes and thinking, not just products, (b) children's exact words are captured, (c) the interpretation framework honours children's theories, (d) the documentation feeds forward into planning, and (e) sharing includes revisiting with children, not just displaying for adults.
```

## Example Output

**Scenario:** *Learning experience: "Reception children (ages 4–5) are investigating shadows. It started when a child noticed that their shadow was 'following' them in the playground. Several children are now fascinated — they've been drawing shadows, measuring them, and having conversations about where shadows come from. One child said 'the shadow is inside you and it comes out when the sun finds it.' Another said 'shadows are afraid of the dark so they only come out in the light.' The class wants to understand: why do we have shadows?" / Documentation purpose: "I want to capture the children's evolving theories about shadows so I can (a) understand what they currently think, (b) plan provocations that help them refine their theories, and (c) create a documentation panel for the classroom and a summary for families." / Available tools: "iPad for photos and video, notebook, children's drawings, large paper for group work"*

---

## Documentation Protocol: Shadows Investigation — Reception

**Experience:** Reception children investigating shadows — where they come from, why they change, what makes them
**Purpose:** Capture children's evolving theories to understand their current thinking, plan next provocations, and share the learning journey with families
**Guiding question:** "What theories are the children constructing about HOW shadows work, and how are these theories changing as they encounter new evidence?"

### What to Observe

**Children's theories (the most important focus):**
Listen for causal explanations — any time a child says "because," "I think," or "maybe it's because." These are theories. Write them down EXACTLY. Examples already captured:
- "The shadow is inside you and it comes out when the sun finds it" — a theory that the shadow is part of the person, activated by the sun
- "Shadows are afraid of the dark so they only come out in the light" — a theory that personifies shadows and identifies the condition for their appearance (light)

Both theories are scientifically incomplete but cognitively sophisticated — they identify light as necessary and propose a mechanism. Watch for how these theories evolve as children encounter new evidence.

**Children's experiments:**
Watch for moments when children TEST their theories — deliberately standing in light and shade, blocking light with objects, trying to "catch" their shadow. These are experiments, even if children don't call them that. Document what they do and what they conclude.

**Dialogue between children:**
When children discuss shadows with each other, their thinking is most visible. Listen for disagreements ("No, that's not why!"), elaborations ("And ALSO, the shadow is flat because..."), and revisions ("Actually, I changed my idea..."). Record these exchanges as close to verbatim as possible.

**Representations:**
Watch for how children represent their understanding — drawings of shadows, paintings, body movements (mimicking shadows), constructions (trying to build a shadow). Malaguzzi's "hundred languages" principle: children express understanding in many forms. A drawing of a shadow may reveal understanding that the child cannot yet articulate in words.

### How to Record

**Photographs (iPad):**
- Photograph children in the ACT of investigating — crouching to examine a shadow, holding an object up to the light, tracing a shadow on paper. Frame the photograph to show the child's action AND what they're looking at, not just their face.
- Photograph the shadow itself alongside the child's reaction — their pointing, their surprise, their attempt to manipulate it.
- Photograph sequences: the same child investigating over multiple days. Three photographs from Monday, Wednesday, and Friday showing the child's evolving engagement reveal more than one photograph.
- Photograph children's drawings WITH the child's verbal explanation noted. The drawing alone may be ambiguous; the child's words give it meaning.

**Transcription (notebook):**
- Carry the notebook during outdoor play and investigation time. Write down children's exact words — not a summary. "The shadow is inside you and it comes out when the sun finds it" is documentation. "The child talked about shadows and the sun" is a lost opportunity.
- Note the context: what was the child doing when they said this? What prompted it? Who were they talking to?
- Record dialogues between children: "A said... B replied... A then said..." The exchange reveals how thinking develops through social interaction.
- Use shorthand in the moment and expand within 24 hours — before the memory fades.

**Children's work:**
- Collect shadow drawings WITH annotations. Ask the child: "Tell me about your drawing." Write their explanation on the back or on a Post-it attached to the drawing. The drawing plus the explanation together constitute the documentation.
- If children trace shadows (on paper taped to the ground), keep the tracings and photograph the tracing process.
- If children create 3D constructions related to shadows, photograph from multiple angles and record the child's explanation.

**Teacher notes:**
- After each investigation session, write a brief reflective note (2–3 sentences): "What theories did I hear today? What surprised me? What do I think the children are ready to explore next?"
- Note your own questions: "I'm not sure whether Aisha understands that the shadow is created by the object BLOCKING the light, or whether she still thinks the shadow is part of the object. How can I find out?"

### How to Interpret

**Look for theory development across time:**
Lay out the documentation chronologically. Read through the children's words from Week 1 to now. How have their theories changed? Has anyone shifted from "the shadow is inside you" to "the shadow happens when you block the light"? Has anyone's drawing changed — from a shadow drawn as a separate character to a shadow connected to an object and a light source?

**Identify the "edge" of understanding:**
What do the children ALMOST understand? If they know light is involved but haven't identified BLOCKING light as the mechanism, they're at the edge. The next provocation should create a situation where the blocking mechanism becomes visible (e.g., using a torch in a darkened room to make shadows with objects — the beam, the object, the shadow are all visible simultaneously).

**Honour the theories, don't dismiss them:**
"The shadow is inside you and it comes out when the sun finds it" is not WRONG — it's DEVELOPING. It correctly identifies: (a) there's a connection between the person and the shadow, (b) the sun is necessary for the shadow to appear, (c) there's a mechanism of some kind ("finds it"). The child needs experiences that help them refine the mechanism — from "the sun finds it" to "the sun's light is blocked by your body."

**Note individual paths AND group knowledge:**
Some children may be further along than others. Document individual journeys AND the group's collective understanding. When children share theories with each other, the group's understanding advances even if individual children are at different points.

### How to Share

**With children (revisiting — the most important use):**
Print 4–5 key photographs and display them at children's eye level with their own words written underneath in large, clear text. During a group time, revisit: "Last week, Aisha said 'the shadow is inside you and it comes out when the sun finds it.' Do you still think that? Has anyone noticed anything new?"

This revisiting serves two purposes: it helps children remember and build on their earlier thinking, and it creates a culture where theories are valued and expected to change over time.

**With families (communication):**
Create a one-page "Learning Story" for the class newsletter or digital platform:
- 3–4 photographs showing the investigation
- 2–3 direct quotes from children (with names, with family permission)
- A brief teacher commentary: "The children are investigating shadows. They are developing sophisticated theories about what causes shadows and how they work. We are supporting their investigation by providing opportunities to experiment with light and shadow both outdoors and in our 'shadow studio.' Here are some of their current theories..."
- A prompt for home: "You could extend this learning at home by exploring shadows together — notice how shadows change at different times of day!"

**With colleagues (professional dialogue):**
Bring the documentation to a team meeting. Share the children's theories WITHOUT your interpretation first. Ask colleagues: "What do you think the children are understanding? What would you offer next?" This uses the documentation as a tool for collective professional learning — not just individual reflection.

### Planning Forward

Based on the documentation, the teacher plans the NEXT provocation (not the next lesson plan — the next experience that will help children encounter the phenomenon in a new way):

**If children identify light as necessary but haven't identified blocking:** Set up a darkened area with torches. Children can experiment: "Can you make a shadow? What do you need? What happens if you move the torch? What happens if you move the object?"

**If children are personifying shadows ("the shadow is afraid"):** This is a theory to be explored, not corrected. Ask: "Can you make your shadow do something? Can you make it dance? Can you make it disappear? What makes it disappear?" Children who discover they can make their shadow appear and disappear by controlling the light are developing the understanding that THEY control the shadow, not the other way around.

**If children are drawing shadows as separate from objects:** Provide mirrors, tracing paper, and a strong light source. Challenge: "Can you draw your shadow while it's there? Can you trace it?" The act of tracing reveals that the shadow is connected to the object and the light — it's not an independent entity.

---

## Known Limitations

1. **Reggio documentation requires time that many teachers do not have.** Transcribing children's words, selecting and annotating photographs, creating documentation panels, and using documentation for planning all take time. In schools where teachers are already stretched, adding documentation on top of existing demands may be unrealistic. The protocol above is designed to be manageable (notebook and iPad, brief reflective notes), but even this requires protected time.

2. **The Reggio approach was developed for early childhood and primary education.** While Krechevsky et al. (2013) have shown it can be adapted for older students, the documentation practices described here are most naturally suited to early years and primary settings where children's learning is more visible and less constrained by subject timetables. Adaptation for secondary contexts requires rethinking what "children's theories" look like in subject-specific learning.

3. **Documentation is a pedagogical stance, not a technique.** The protocol provides practical guidance, but Reggio documentation requires a fundamental belief in the child as a capable, competent theory-builder. A teacher who documents children's words while privately dismissing them as "cute mistakes" has missed the point. The documentation is only as powerful as the respect with which it treats children's thinking.
