---
# AGENT SKILLS STANDARD FIELDS (v2)
name: cross-cultural-task-validity-checker
description: "Check an educational practice or task for cultural bias, WEIRD assumptions, and cross-cultural validity. Use when adapting resources for diverse contexts or questioning universal claims."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "global-cross-cultural-pedagogies/cross-cultural-task-validity-checker"
skill_name: "Cross-Cultural Task Validity Checker"
domain: "global-cross-cultural-pedagogies"
version: "1.0"
evidence_strength: "strong"
evidence_sources:
  - "Henrich, Heine & Norenzayan (2010) — The weirdest people in the world? (WEIRD bias in behavioural science)"
  - "Tobin, Wu & Davidson (1989) — Preschool in Three Cultures: Japan, China, and the United States"
  - "Alexander (2001) — Culture and Pedagogy: international comparisons in primary education"
  - "Stigler & Hiebert (1999) — The Teaching Gap: best ideas from the world's teachers for improving education in the classroom"
  - "Nsamenang (2006) — Human ontogenesis: an indigenous African view on development and intelligence"
input_schema:
  required:
    - field: "task_or_practice"
      type: "string"
      description: "The educational task, practice, strategy, or research finding to be checked for cross-cultural validity"
    - field: "intended_context"
      type: "string"
      description: "Where and with whom this task or practice will be used — the specific cultural context of the students"
  optional:
    - field: "source_context"
      type: "string"
      description: "Where the task or practice was developed or researched — the cultural context of origin"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject"
    - field: "specific_concerns"
      type: "string"
      description: "Any particular concerns the teacher has about cultural fit"
output_schema:
  type: "object"
  fields:
    - field: "validity_analysis"
      type: "object"
      description: "Analysis of the task's cross-cultural validity — what assumptions it carries, where it might not transfer"
    - field: "cultural_assumptions"
      type: "array"
      description: "Specific cultural assumptions embedded in the task — about individualism, communication styles, knowledge, authority, or values"
    - field: "adaptation_suggestions"
      type: "array"
      description: "How to adapt the task for the intended context — specific, practical modifications"
    - field: "alternative_approaches"
      type: "array"
      description: "Alternative approaches from other cultural traditions that achieve the same learning objective differently"
chains_well_with:
  - "culturally-responsive-teaching-designer"
  - "ubuntu-collective-knowledge-task-designer"
  - "belonging-classroom-culture-designer"
  - "phenomenon-based-unit-anchor"
teacher_time: "3 minutes"
tags: ["WEIRD-bias", "Henrich", "cross-cultural", "cultural-assumptions", "validity", "decolonising", "global-pedagogy"]
---

# Cross-Cultural Task Validity Checker

## What This Skill Does

Analyses an educational task, strategy, or research-based practice for hidden cultural assumptions that may limit its validity or effectiveness when used with students from different cultural backgrounds. The critical insight from Henrich, Heine & Norenzayan (2010) is that most educational research has been conducted with WEIRD populations (Western, Educated, Industrialised, Rich, Democratic) and the findings are often presented as universal when they are in fact culturally specific. A teaching strategy that "works" in research may work because it aligns with the cultural assumptions of the population studied — not because it is universally effective. The skill identifies specific cultural assumptions embedded in a task (about individualism, communication styles, authority, knowledge, competition, or values), assesses whether these assumptions hold in the intended context, and suggests adaptations or alternative approaches from other cultural traditions. The output includes a validity analysis, identification of cultural assumptions, adaptation suggestions, and alternative approaches. AI is specifically valuable here because identifying hidden cultural assumptions requires simultaneously understanding the cultural context of origin AND the cultural context of use — a cross-referencing task that requires broad knowledge across multiple cultural systems.

## Evidence Foundation

Henrich, Heine & Norenzayan (2010) demonstrated that the vast majority of research in psychology, cognitive science, and behavioural economics has been conducted with WEIRD populations — yet findings are routinely generalised to "humans" as if WEIRD populations are representative. They showed that WEIRD populations are statistical outliers on many dimensions: more individualistic, more analytically oriented, more disposed to abstract reasoning, and more likely to prioritise personal choice and autonomy than most of the world's population. This has direct implications for education: teaching strategies derived from WEIRD research may carry hidden cultural assumptions that do not hold for students from other cultural traditions. Tobin, Wu & Davidson (1989) compared preschool education in Japan, China, and the United States, revealing fundamentally different assumptions about the purpose of education, the role of the teacher, the value of individual vs. group achievement, and what constitutes "good" learning behaviour. Alexander (2001) conducted the most comprehensive international comparison of primary education, studying classrooms in England, France, India, Russia, and the United States. He found that pedagogical practices reflect deep cultural values — what counts as "good teaching" varies dramatically across cultures, and practices that are effective in one culture may be ineffective or counterproductive in another. Stigler & Hiebert (1999) compared mathematics teaching in Japan, Germany, and the United States, showing that Japanese and American teachers have fundamentally different theories about how students learn — Japanese teachers use productive struggle and whole-class discussion, while American teachers prioritise individual practice and immediate success. Neither is "wrong," but importing one into the other's cultural context without adaptation is unlikely to succeed. Nsamenang (2006) articulated an African view of human development that centres social responsibility, participatory learning, and community embeddedness — challenging Western developmental models that prioritise individual autonomy and abstract cognitive achievement.

## Input Schema

The teacher must provide:
- **Task or practice:** What to check. *e.g. "Growth mindset praise — telling students 'You worked really hard on that' instead of 'You're so smart'" / "Think-pair-share as a discussion strategy" / "Individual goal-setting where each student writes their own personal learning target" / "Using Bloom's Taxonomy to design higher-order thinking questions" / "Exit tickets where students individually write what they learned at the end of the lesson"*
- **Intended context:** Where it will be used. *e.g. "A multicultural school in London with students from diverse backgrounds including recent arrivals" / "A school in rural Kenya" / "A school in Japan" / "A classroom with a significant proportion of First Nations students in Australia" / "An international school in Singapore with students from 40+ nationalities"*

Optional (injected by context engine if available):
- **Source context:** Where the practice was developed
- **Student level:** Year group
- **Subject area:** Curriculum subject
- **Specific concerns:** Teacher's particular worries about cultural fit

## Prompt

```
You are an expert in cross-cultural education research, with deep knowledge of Henrich, Heine & Norenzayan's (2010) WEIRD bias research, Tobin, Wu & Davidson's (1989) cross-cultural comparison of early childhood education, Alexander's (2001) comparative pedagogy, Stigler & Hiebert's (1999) research on mathematics teaching across cultures, and Nsamenang's (2006) African developmental psychology. You understand that educational practices are cultural products — they emerge from specific cultural contexts and carry assumptions about learning, personhood, knowledge, authority, and community that may not transfer across cultures.

CRITICAL PRINCIPLES:
- **All educational practices carry cultural assumptions.** There is no "culture-free" pedagogy. Every teaching strategy, assessment method, and classroom routine embodies assumptions about what learning is, how people relate to each other, and what matters. The task is to make these assumptions VISIBLE, not to eliminate them (which is impossible).
- **"Evidence-based" does not mean "universally valid."** A practice that has strong research evidence may have been tested only with WEIRD populations. The evidence tells us it works in THAT context — it does not tell us it works everywhere. Be precise about what the evidence actually shows and where it was generated.
- **Identify the SPECIFIC assumption, not a vague concern.** "This might not work in other cultures" is too vague. "This practice assumes that individual public performance is motivating — but in cultures that value group harmony, being singled out may cause discomfort rather than motivation" is specific and actionable.
- **Offer adaptations, not just critiques.** Identifying cultural assumptions is useful only if it leads to practical adaptation. For each assumption identified, suggest how the practice could be modified to work in the intended context — or suggest an alternative approach from a different cultural tradition that achieves the same learning objective.
- **Avoid both cultural essentialism and cultural relativism.** Don't assume all members of a cultural group share the same values (essentialism). Don't conclude that nothing can transfer across cultures (relativism). Instead, identify specific assumptions, assess their fit with the specific context, and adapt thoughtfully.

Your task is to check the cross-cultural validity of:

**Task or practice:** {{task_or_practice}}
**Intended context:** {{intended_context}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Source context:** {{source_context}} — if not provided, identify the likely cultural origin of the practice.
**Student level:** {{student_level}} — if not provided, design for general school-age students.
**Subject area:** {{subject_area}} — if not provided, address the practice in general terms.
**Specific concerns:** {{specific_concerns}} — if not provided, conduct a general cross-cultural validity analysis.

Return your output in this exact format:

## Cross-Cultural Validity Check: [Practice Name]

**Practice:** [What is being checked]
**Source context:** [Where the practice was developed/researched]
**Intended context:** [Where it will be used]
**Overall assessment:** [Brief summary — e.g., "Partially transferable with significant adaptations needed" / "Core principle transfers well; specific implementation needs adjustment" / "Fundamental assumptions may not hold in this context"]

### Cultural Assumptions Identified

For each assumption (3–5):
**Assumption [N]: [The assumption]**
- **What the practice assumes:** [The specific cultural value or norm embedded in the practice]
- **Where this assumption holds:** [Cultures/contexts where this assumption is valid]
- **Where it may not hold:** [Cultures/contexts where this assumption may not apply]
- **Evidence:** [Research or cross-cultural comparison that supports this analysis]

### Adaptation Suggestions

For each adaptation (2–4):
**Adaptation [N]: [What to change]**
- **Original:** [How the practice currently works]
- **Adapted:** [How to modify it for the intended context]
- **Why this works:** [How the adaptation addresses the cultural assumption while maintaining the learning objective]

### Alternative Approaches From Other Traditions

[2–3 alternative approaches from non-WEIRD educational traditions that achieve the same learning objective through different cultural logic]

### What Transfers Well

[Elements of the practice that DO transfer across cultures — the universal or widely applicable principles underneath the cultural packaging]

### Honest Caveats

[Limitations of this analysis — what can and cannot be determined without direct knowledge of the specific students and community]

**Self-check before returning output:** Verify that (a) specific cultural assumptions are identified, not vague concerns, (b) the analysis avoids cultural essentialism, (c) practical adaptations are suggested, (d) alternative approaches are offered from non-WEIRD traditions, (e) the analysis identifies what DOES transfer, not just what doesn't, and (f) honest caveats acknowledge the limits of the analysis.
```

## Example Output

**Scenario:** *Task or practice: "Think-pair-share — a discussion strategy where the teacher asks a question, gives students individual thinking time, then pairs discuss, then selected pairs share with the whole class. Widely used as a 'best practice' for increasing student participation." / Intended context: "An international school in the UAE with students from diverse backgrounds — Emirati, South Asian (Indian, Pakistani, Bangladeshi), Filipino, Egyptian, Jordanian, British, American. Significant cultural diversity in the same classroom. Some students are very comfortable with public discussion; others rarely speak in class despite being capable and engaged." / Specific concerns: "I notice that think-pair-share seems to work well for some students but not others. The students who don't participate aren't disengaged — they seem uncomfortable with the format itself. I want to understand whether the strategy has cultural assumptions that might explain this."*

---

## Cross-Cultural Validity Check: Think-Pair-Share

**Practice:** Think-pair-share — individual thinking time → paired discussion → whole-class sharing
**Source context:** Developed by Frank Lyman (1981) in the United States; widely adopted in Anglophone education systems (US, UK, Australia, Canada)
**Intended context:** International school in the UAE with students from 8+ cultural backgrounds
**Overall assessment:** Core principle (giving students time to think before speaking) transfers well. Specific implementation carries significant cultural assumptions about individual expression, peer discussion norms, and public sharing that may not hold for all students in this diverse context.

### Cultural Assumptions Identified

**Assumption 1: Individual Thinking Is the Best Starting Point**
- **What the practice assumes:** The best way to process a question is to think ALONE first. This privileges internal, individual cognition as the primary mode of meaning-making.
- **Where this assumption holds:** In individualist cultures (broadly Western, particularly US and Northern European), individual thinking is valued as the foundation of authentic understanding. "Think for yourself" is a cultural norm.
- **Where it may not hold:** In collectivist cultures (broadly East Asian, South Asian, Middle Eastern, African), thinking is often RELATIONAL — meaning emerges through dialogue, not before it. Some students may think BETTER when they talk through an idea with someone else, not worse. The "think" phase may create anxiety for students who process through interaction.
- **Evidence:** Tobin, Wu & Davidson (1989) showed that Japanese preschool education values the group as the unit of thinking, not the individual. Alexander (2001) found that Russian and Indian classrooms use collective oral recitation as a legitimate form of thinking — not as "rote learning" but as communal cognitive processing.

**Assumption 2: Paired Discussion Between Peers Is Comfortable and Productive**
- **What the practice assumes:** Students will engage in open, equal-status discussion with a peer. This assumes that peer-to-peer horizontal discussion is a natural and comfortable communication mode.
- **Where this assumption holds:** In cultures with relatively flat authority structures (US, Scandinavian countries, Australia), peer discussion is a familiar format. Students are accustomed to expressing opinions to equals.
- **Where it may not hold:** In cultures with steeper authority gradients (many East Asian, South Asian, and Middle Eastern contexts), students may be accustomed to vertical communication — speaking TO the teacher or IN RESPONSE to the teacher, rather than horizontally to each other. Paired discussion may feel awkward, not because students cannot do it, but because it violates their understanding of how knowledge is supposed to flow (from authority to learner, not between peers). Additionally, mixed-gender pairing may be uncomfortable for some students from cultures where gender segregation in conversation is normative.
- **Evidence:** Hofstede's cultural dimensions research shows significant variation in power distance across cultures. Alexander (2001) found that in Indian classrooms, the teacher's voice is the primary vehicle for knowledge — student-to-student discussion is less common and less valued. Stigler & Hiebert (1999) showed that Japanese mathematics uses whole-class discussion led by the teacher, not peer pair-work — the teacher orchestrates a collective discussion that is more structured than think-pair-share.

**Assumption 3: Public Sharing of Personal Thinking Is Desirable**
- **What the practice assumes:** Sharing your thinking with the whole class is a positive act — it demonstrates confidence, contributes to collective learning, and is something students should aspire to. The practice rewards public verbal expression.
- **Where this assumption holds:** In cultures that value individual expression and public performance (US, UK), being asked to share is an opportunity. Students who speak up are often praised and rewarded.
- **Where it may not hold:** In cultures that value modesty, group harmony, or deference (many East Asian, some Middle Eastern, some Indigenous cultures), public sharing of personal opinions may be uncomfortable. Being singled out to speak — especially if the answer might be wrong — can cause loss of face. In some cultures, the "correct" behaviour is to wait to be asked, to defer to those with more knowledge, and to avoid standing out from the group.
- **Evidence:** Tobin, Wu & Davidson (1989) found that Japanese educators viewed American children's eagerness to speak publicly as immature, not confident. Castagno & Brayboy (2008) noted that Indigenous students may use silence as a respectful, thoughtful response — not as disengagement. In many Arab cultures, silence in the presence of a question can indicate deep thinking and respect, not inability or reluctance.

**Assumption 4: The "Correct" Outcome Is Verbal Articulation**
- **What the practice assumes:** Understanding is demonstrated through SPEAKING. If you can say it, you understand it. If you are silent, you may not understand.
- **Where this assumption holds:** In verbally oriented cultures (broadly Western, particularly Anglophone), verbal fluency is equated with cognitive competence.
- **Where it may not hold:** In cultures where other forms of expression are equally valued — writing, drawing, gesture, demonstration, quiet observation — silence does not indicate lack of understanding. Nsamenang (2006) describes African educational traditions where understanding is demonstrated through DOING, not through verbal explanation.

### Adaptation Suggestions

**Adaptation 1: Replace "Think" With "Think or Discuss"**
- **Original:** "Think on your own for 30 seconds." (Individual processing required)
- **Adapted:** "Take 30 seconds to start processing this question — you can think silently, jot down a note, or quietly begin talking with a partner." (Multiple processing modes available)
- **Why this works:** Removes the assumption that individual silent thinking is the only valid starting mode. Students who process through dialogue can begin talking; students who prefer silence can think. Both are legitimate.

**Adaptation 2: Offer Choice in Sharing Mode**
- **Original:** Selected pairs share verbally with the whole class. (Public verbal performance required)
- **Adapted:** After pair discussion, offer sharing options: "You can share with the class verbally, write your pair's idea on a whiteboard and hold it up, or write a sentence on a sticky note for the class display." (Multiple sharing modes)
- **Why this works:** Students who are uncomfortable with public verbal performance can still contribute their thinking. The written whiteboard is less exposing than standing and speaking. The sticky note is even lower-stakes. The learning objective (sharing thinking) is preserved; the cultural assumption (verbal public sharing) is removed.

**Adaptation 3: Use Trio or Small Group Instead of Pairs**
- **Original:** Pair discussion. (One-to-one, possibly awkward if mixed-gender or cross-status)
- **Adapted:** Use trios or groups of four, allowing students to choose their position within the group. (Shared responsibility, less pressure on individuals)
- **Why this works:** In a trio, a student can listen and contribute when ready, rather than being the sole discussion partner. The social dynamics are more flexible — there's less pressure to perform for one specific person. Groups can also be organised with sensitivity to gender and cultural norms.

**Adaptation 4: Use "Write-Pair-Share" or "Draw-Pair-Share"**
- **Original:** Think (silent individual cognition) → Pair (verbal) → Share (verbal)
- **Adapted:** Write or draw first (individual or partner) → Discuss (pair or trio) → Share (any mode)
- **Why this works:** Writing and drawing are lower-stakes entry points for students who are uncomfortable with immediate verbal discussion. A student who has written their idea has something to SHOW their partner, which is easier than generating ideas verbally in the moment.

### Alternative Approaches From Other Traditions

**Japanese Neriage (Kneading/Polishing Discussion):**
Instead of think-pair-share, the teacher poses a problem and students work on it (individually or in pairs). The teacher then selects specific student responses to share with the class — but the selection is deliberate, chosen to create a productive sequence of ideas that builds toward understanding. The teacher orchestrates the discussion, connecting student ideas: "Yuki found this approach. How does it compare to what Hiro did?" This is more structured than think-pair-share and gives the teacher control over who shares and when — reducing the anxiety of random selection while still surfacing diverse thinking. (Stigler & Hiebert, 1999)

**African Circle Discussion (Ubuntu-Informed):**
Rather than individual thinking followed by paired sharing, the group sits in a circle and builds understanding collectively. The teacher poses a question and the discussion moves around the circle — each person adds to what the previous person said, builds on it, or respectfully offers a different perspective. Knowledge is constructed communally, not individually. No one is singled out; everyone contributes as part of the flow. This honours collectivist communication norms and reduces the pressure of individual public performance. (Adapted from Letseka, 2012; Venter, 2004)

**Silent Discussion (Written Dialogue):**
Students respond to a question by writing on a shared piece of paper (or a shared digital document). No speaking — only writing. Students read each other's contributions and add to them. This is highly effective for students who are uncomfortable with verbal discussion but have rich ideas. It also creates a permanent record of the discussion. This approach has roots in Quaker education practices and has been adopted in various multilingual and cross-cultural settings.

### What Transfers Well

The CORE PRINCIPLE of think-pair-share transfers very well across cultures:
- **Giving students time to process before expecting a response** — this is universally beneficial. The problem is not the thinking time but the assumption that it must be silent and individual.
- **Reducing the number of students who can "hide"** — the pair/group structure means every student engages, not just the volunteers. This principle holds across cultures.
- **Making thinking visible** — the goal of surfacing student understanding for formative purposes is universally valuable. The issue is HOW thinking is made visible, not WHETHER it should be.

### Honest Caveats

1. **This analysis identifies POSSIBLE cultural assumptions, not certainties.** Not all students from collectivist cultures are uncomfortable with think-pair-share. Not all students from individualist cultures are comfortable with it. Culture influences but does not determine individual behaviour. The teacher must observe THEIR specific students and adapt accordingly.

2. **Cultural analysis risks stereotyping.** Saying "South Asian students may be uncomfortable with peer discussion" is a generalisation that may not apply to the specific South Asian students in this classroom. The analysis is a starting point for observation, not a conclusion.

3. **The teacher's own cultural assumptions are also at play.** A teacher trained in Anglophone pedagogy may unconsciously interpret silence as "disengagement" and verbal participation as "engagement." This interpretation is itself culturally specific. The most important adaptation may be in the teacher's assessment of participation — recognising that silence can indicate deep processing, not absence.

4. **The intended context (an international school in the UAE) is itself culturally complex.** Students in international schools are often already navigating multiple cultural norms. Some students may be very comfortable with Western-style discussion practices; others may not. The adaptations above provide OPTIONS that work across the cultural range, rather than assuming all students need the same adaptation.

---

## Known Limitations

1. **This skill identifies cultural assumptions in educational practices — it cannot identify all assumptions.** Culture is complex, multidimensional, and constantly evolving. The analysis focuses on the most well-documented dimensions (individualism/collectivism, power distance, communication norms, knowledge traditions) but cannot capture every relevant cultural factor.

2. **Cross-cultural analysis requires more than WEIRD research.** The evidence base for this skill draws on cross-cultural research, but most educational research remains WEIRD-centric. The alternative approaches from other traditions (neriage, Ubuntu circle, silent discussion) are described based on available literature, but teachers working in specific cultural contexts should seek out LOCAL educational expertise, not just Western academic research about those contexts.

3. **There is a tension between cultural adaptation and cultural change.** If a student from a high-power-distance culture is uncomfortable with peer discussion, should the teacher adapt the task (respecting the cultural norm) or persist with the task (deliberately exposing students to a different cultural norm)? This is a genuine pedagogical dilemma with no universal answer. The skill provides adaptations but does not resolve this tension — the teacher must make a professional judgement about their specific context, ideally in dialogue with families and community.
