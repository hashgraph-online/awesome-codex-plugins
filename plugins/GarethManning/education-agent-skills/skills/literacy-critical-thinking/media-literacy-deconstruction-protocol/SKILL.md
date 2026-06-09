---
# AGENT SKILLS STANDARD FIELDS (v2)
name: media-literacy-deconstruction-protocol
description: "Design a media deconstruction protocol analysing persuasion, bias, or representation in media texts. Use when teaching students to critically read advertisements, news, or social media content."
disable-model-invocation: false
user-invocable: true
effort: medium

# EXISTING FIELDS

skill_id: "literacy-critical-thinking/media-literacy-deconstruction-protocol"
skill_name: "Media Literacy Deconstruction Protocol"
domain: "literacy-critical-thinking"
version: "1.0"
evidence_strength: "moderate"
evidence_sources:
  - "Hobbs (2010) — Digital and Media Literacy: a plan of action"
  - "Buckingham (2003) — Media Education: literacy, learning and contemporary culture"
  - "Kellner & Share (2007) — Critical media literacy, democracy, and the reconstruction of education"
  - "Aufderheide (1993) — Media Literacy: a report of the national leadership conference on media literacy"
  - "Hobbs & Jensen (2009) — The past, present, and future of media literacy education"
input_schema:
  required:
    - field: "media_type"
      type: "string"
      description: "The type of media text being analysed — e.g. advertisement, news article, social media post, political campaign material, film clip, infographic, podcast"
    - field: "analysis_focus"
      type: "string"
      description: "What the teacher wants students to notice — e.g. persuasive techniques, representation, bias, audience targeting, omission"
    - field: "student_level"
      type: "string"
      description: "Age/year group"
  optional:
    - field: "specific_text"
      type: "string"
      description: "Description of the specific media text being analysed"
    - field: "student_profiles"
      type: "array"
      description: "From context engine: prior media literacy experience, cultural background"
    - field: "subject_area"
      type: "string"
      description: "The curriculum subject context — e.g. English, PSHE, Media Studies, Citizenship"
    - field: "learning_objectives"
      type: "string"
      description: "Specific learning objectives for this analysis"
output_schema:
  type: "object"
  fields:
    - field: "deconstruction_protocol"
      type: "object"
      description: "Structured analysis framework with media-type-specific questions organised by analytical category"
    - field: "teacher_modelling"
      type: "string"
      description: "Script showing the teacher modelling the analysis with a specific example"
    - field: "student_activity"
      type: "object"
      description: "Structured activity students complete using the protocol"
    - field: "extension_questions"
      type: "array"
      description: "Deeper analytical questions for students who complete the basic protocol"
chains_well_with:
  - "source-credibility-evaluation-protocol"
  - "critical-thinking-task-designer"
  - "argument-structure-scaffold-generator"
  - "socratic-questioning-sequence-generator"
teacher_time: "3 minutes"
tags: ["media-literacy", "critical-thinking", "representation", "persuasion", "deconstruction"]
---

# Media Literacy Deconstruction Protocol

## What This Skill Does

Generates a structured analysis framework for deconstructing a specific type of media text — an advertisement, a news article, a social media post, a political campaign, a film clip, an infographic. The framework goes beyond surface-level observation ("What colours are used?") to teach students to analyse how media texts are constructed to position audiences, represent people and ideas, and serve particular purposes. The output includes a media-type-specific deconstruction protocol organised by analytical category (construction, representation, audience, purpose, omission), a teacher modelling script, and a structured student activity. AI is specifically valuable here because media literacy requires both general analytical principles and media-type-specific knowledge — the techniques used to persuade in a television advertisement are different from those used in a news headline or a social media post, and effective analysis protocols must reflect these differences.

## Evidence Foundation

Hobbs (2010) established that media literacy requires five competencies: access (finding and using media), analyse (understanding how media messages are constructed), create (producing media), reflect (considering one's own media consumption), and act (using media responsibly in civic life). This skill focuses on the "analyse" competency. Buckingham (2003) identified four key concepts for media analysis: production (who made this and why?), language (what techniques are used?), representation (how are people, events, and ideas portrayed?), and audience (who is the intended audience and how are they positioned?). These concepts provide the analytical framework for media deconstruction. Kellner & Share (2007) emphasised that critical media literacy must go beyond technical analysis to address issues of power, ideology, and social justice — asking not just "how is this made?" but "whose interests does this serve?" and "whose perspective is missing?" Aufderheide (1993) established the foundational principle that all media messages are constructed — they are the result of choices about what to include, exclude, emphasise, and downplay. This principle of construction is the starting point for all media deconstruction. Hobbs & Jensen (2009) argued that media literacy must be taught explicitly and scaffolded — students do not naturally develop critical analysis skills through media exposure alone.

## Input Schema

The teacher must provide:
- **Media type:** The type of media text. *e.g. "Instagram advertisement" / "BBC News article" / "Political campaign poster" / "TikTok video" / "Newspaper front page" / "Documentary clip"*
- **Analysis focus:** What to notice. *e.g. "Persuasive techniques targeting teenagers" / "How the article frames the issue as controversial" / "Representation of gender in the advertisement" / "What information is included and what is left out"*
- **Student level:** Year group. *e.g. "Year 10"*

Optional (injected by context engine if available):
- **Specific text:** Description of the actual media text
- **Student profiles:** Prior media literacy experience, cultural background
- **Subject area:** The curriculum subject
- **Learning objectives:** Specific objectives for this analysis

## Prompt

```
You are an expert in media literacy education, with deep knowledge of Hobbs' (2010) media literacy competencies, Buckingham's (2003) four key concepts for media education (production, language, representation, audience), Kellner & Share's (2007) critical media literacy framework, and Aufderheide's (1993) principle that all media messages are constructed. You understand that effective media analysis requires both general critical thinking principles and media-type-specific knowledge of how particular media forms use specific techniques to construct meaning.

Your task is to generate a media deconstruction protocol for:

**Media type:** {{media_type}}
**Analysis focus:** {{analysis_focus}}
**Student level:** {{student_level}}

The following optional context may or may not be provided. Use whatever is available; ignore any fields marked "not provided."

**Specific text:** {{specific_text}} — if not provided, create a plausible example of this media type for the modelling script.
**Student profiles:** {{student_profiles}} — if not provided, assume students have everyday experience consuming this type of media but have not been formally taught to analyse it critically.
**Subject area:** {{subject_area}} — if not provided, design for a general media literacy context.
**Learning objectives:** {{learning_objectives}} — if not provided, infer appropriate objectives from the media type and analysis focus.

Apply these evidence-based principles:

1. **All media messages are constructed (Aufderheide, 1993):**
   - The foundational principle: nothing in a media text is accidental. Every element — image, word, colour, angle, framing, sequence, what's included, what's excluded — is the result of a choice.
   - The protocol should train students to ask "Why was this choice made?" rather than just "What do I see?"

2. **Buckingham's (2003) four key concepts:**
   Structure the analysis around four categories:
   - **Production:** Who made this? Why? Who funded it? What are their interests?
   - **Language:** What specific techniques are used? (This is media-type-specific — an advertisement uses different techniques from a news article.) How do these techniques create meaning or emotion?
   - **Representation:** How are people, events, places, and ideas represented? What stereotypes or assumptions are present? Whose perspective is centred, and whose is marginalised or absent?
   - **Audience:** Who is the intended audience? How does the text try to position the audience (to feel, think, or do something)? How might different audiences respond differently?

3. **Add the "omission" question (Kellner & Share, 2007):**
   - What is NOT shown, said, or included? This is often the most powerful analytical question.
   - What alternative perspectives, evidence, or representations are missing?
   - Whose voice is not heard?

4. **Media-type-specific techniques:**
   - Adapt the "Language" analysis to the specific media type.
   - Advertisements: camera angles, lighting, colour, body language, music, slogans, celebrity endorsement, lifestyle association, emotional appeal
   - News articles: headline framing, source selection, quote placement, active/passive voice, image selection, story positioning
   - Social media: algorithm awareness, engagement techniques, parasocial relationships, filter effects, shareability design
   - Film/video: shot composition, editing, music, narrative structure, point of view
   - Political material: emotional appeal, us/them framing, statistics presentation, visual symbolism

5. **Model the analysis explicitly:**
   - Include a teacher modelling script that demonstrates the analytical thinking process — not just identifying techniques but explaining how they position the audience.

Return your output in this exact format:

## Media Deconstruction Protocol: [Media Type]

**For:** [Student level]
**Focus:** [Analysis focus]
**Key principle:** All media messages are constructed — every choice serves a purpose.

### The Protocol

**Category 1: Production — Who made this and why?**
[Questions specific to this media type]

**Category 2: Language — What techniques are used?**
[Media-type-specific technique analysis questions]

**Category 3: Representation — How are people and ideas portrayed?**
[Questions about representation, stereotypes, perspectives]

**Category 4: Audience — Who is this for and how does it position them?**
[Questions about target audience and audience positioning]

**Category 5: Omission — What's missing?**
[Questions about what's not shown, said, or included]

### Teacher Modelling Script

[Think-aloud script demonstrating the analysis of a specific example, working through the protocol categories]

### Student Activity

[Structured activity where students apply the protocol — format appropriate for the media type and student level]

### Extension Questions

[3–4 deeper analytical questions for students who complete the basic protocol]

**Self-check before returning output:** Verify that (a) the protocol is specific to the stated media type, not generic, (b) each category includes questions that teach critical thinking, not just observation, (c) the "omission" category is included, (d) the modelling script demonstrates analytical thinking (explaining WHY choices were made), not just identification of techniques, and (e) the student activity requires genuine analysis, not just description.
```

## Example Output

**Scenario:** *Media type: "Instagram advertisement" / Analysis focus: "Persuasive techniques targeting teenagers — how the ad creates desire for the product through lifestyle association and social proof" / Student level: "Year 10" / Subject area: "English / Media Literacy"*

---

## Media Deconstruction Protocol: Instagram Advertisement

**For:** Year 10 English / Media Literacy
**Focus:** Persuasive techniques targeting teenagers — lifestyle association and social proof
**Key principle:** All media messages are constructed — every choice serves a purpose. An Instagram ad that looks casual and "real" is the result of dozens of deliberate decisions about how to make you feel a certain way.

### The Protocol

**Category 1: Production — Who made this and why?**
- Who is the brand? What do they sell? What do they want you to DO after seeing this ad? (Buy, follow, share, feel something?)
- Is this clearly labelled as an advertisement, or does it look like organic content? Why might the brand want it to look organic?
- If an influencer is featured: are they paid? Is there a #ad or #sponsored tag? (Note: many sponsored posts are not clearly labelled.)
- What is the business model? How does the brand make money from you seeing this ad?

**Category 2: Language — What techniques are used?**
*Visual techniques:*
- What is the colour palette? Warm, cool, muted, vibrant? What mood does it create?
- What is the setting? Does it associate the product with a particular lifestyle (travel, fitness, luxury, friendship, creativity)?
- How is the person photographed? Candid or posed? Close-up or full body? Looking at the camera (creating connection) or looking away (creating aspiration)?
- Does the image look "real" or "curated"? How can you tell? If it looks effortlessly natural, consider: how much effort went into making it look effortless?

*Text and caption techniques:*
- What tone is the caption? Casual, funny, inspirational, urgent? Does it sound like a friend talking, not a company selling?
- Does the caption include a call to action? ("Shop now," "Link in bio," "Tag a friend who needs this")
- Does it use social proof? ("Thousands of happy customers," "As seen on...," engagement numbers)
- Does it create urgency or scarcity? ("Limited edition," "Only available today," "Selling fast")

*Platform-specific techniques:*
- How does this ad use Instagram's specific features? (Stories format, swipe-up, carousel, Reels, shopping tags)
- Is it designed to be shared or saved? What makes it shareable?
- How does it interact with the algorithm? (Engagement bait, comment prompts, save-worthy content)

**Category 3: Representation — How are people and ideas portrayed?**
- Who is shown in the ad? What do they look like? (Age, body type, ethnicity, gender, style)
- What kind of life are they shown living? Is this realistic, or is it an idealised version?
- What VALUES are being associated with the product? (Freedom, beauty, confidence, popularity, success, rebellion, belonging)
- Are stereotypes being used or challenged? How?
- Who is NOT shown? What bodies, identities, lifestyles, or experiences are absent?

**Category 4: Audience — Who is this for and how does it position them?**
- Who is the target audience? How do you know? (Consider: age, interests, lifestyle, values, insecurities)
- How does the ad WANT the audience to feel? (Inspired, inadequate, excited, envious, included, empowered)
- What desire does the ad create or activate? (The desire to look like that, live like that, be part of that group)
- What is the implied message? "If you buy this product, you will..." (Complete the sentence — this is the ad's underlying promise.)
- How might someone OUTSIDE the target audience respond to this ad differently?

**Category 5: Omission — What's missing?**
- What is NOT shown about the product? (Price, quality, ethical production, environmental impact)
- What is NOT shown about the lifestyle? (The effort, expense, privilege, or staging behind the "effortless" image)
- What is NOT shown about the person in the ad? (Editing, filters, professional lighting, multiple takes, their actual relationship to the product)
- What alternative perspectives on the product are absent? (Negative reviews, competitors, people who don't want or can't afford it)
- If this is influencer content: what is NOT disclosed about the financial relationship between the brand and the influencer?

### Teacher Modelling Script

"I'm going to show you how I analyse an Instagram ad. I'm looking at a post from a fitness clothing brand — it shows a young woman in workout clothes, stretching on a rooftop at sunrise, with a city skyline behind her. The caption says: 'Your only competition is yourself. Start your journey. 🌅 #NoBoundaries #FitnessGoals. Shop the collection — link in bio.'

Let me work through this.

**Production:** This is from a fitness clothing brand. They want me to buy their clothes. But notice — this doesn't LOOK like an ad. There's no 'BUY NOW' in big letters. It looks like something a real person posted about their morning workout. That's a deliberate choice — they want this to feel authentic, not commercial, because we trust authentic-looking content more than obvious advertising.

**Language:** Look at the visual choices. Sunrise — warm, golden light. A rooftop — elevated, aspirational. She's alone — this says 'independent, strong, self-motivated.' The city below her — she's literally above it all. None of this is accidental. Someone chose this location, this time of day, this angle, to create a feeling of calm, strength, and aspiration.

The caption is interesting: 'Your only competition is yourself.' It sounds like a motivational quote, not a sales pitch. It positions the brand as being about self-improvement, not consumerism. But it IS a sales pitch — it just doesn't want you to notice.

**Representation:** The woman is young, slim, fit, and conventionally attractive. She represents an idealised version of the 'fitness lifestyle.' This is who the brand wants you to WANT TO BE. Ask yourself: how many people actually do yoga on rooftops at sunrise? This is a fantasy — but it's presented as an achievable reality, if you just buy the clothes and 'start your journey.'

**Audience:** This targets young women who are interested in fitness and self-improvement. It WANTS me to feel inspired but also slightly inadequate — like I COULD be this calm, this fit, this together, if I just took that first step. And conveniently, that first step is... buying their clothes.

**Omission:** What's NOT here? We don't see the photographer, the lighting rig, the twenty takes it took to get this shot. We don't see the price tag. We don't see the factory where the clothes were made. We don't see the model's actual morning (which probably started at 4am for a paid photoshoot, not a spontaneous rooftop workout). The 'real' feeling is completely manufactured — but that's the point."

### Student Activity

**Step 1 — Individual analysis (10 minutes):**
Each student selects an Instagram advertisement (provided by the teacher or found from their own feed). They work through the protocol categories, recording their analysis in the following table:

| Category | What I notice | What choices were made and WHY |
|----------|--------------|-------------------------------|
| Production | | |
| Language (visual) | | |
| Language (text) | | |
| Representation | | |
| Audience | | |
| Omission | | |

**Step 2 — Pair comparison (5 minutes):**
Students swap advertisements with a partner and compare analyses. Focus question: "Did your partner notice something you missed? What did they see in the 'omission' category?"

**Step 3 — Class discussion (5 minutes):**
"What was the most effective persuasive technique you found? Why is it effective? And — now that you can see how it works — does it still work on you? Can you be persuaded by a technique you can identify?"

### Extension Questions

1. "Find two ads for similar products (e.g., two fitness brands, two skincare brands). How do they differ in their representation and audience positioning? What does this tell you about how brands create identity through advertising?"

2. "Choose an ad that uses an influencer. Research the influencer: how much are they paid? How many similar brand deals do they have? Does knowing this change how you read their 'authentic' endorsement?"

3. "Redesign the ad from the perspective it omits. If the ad shows an idealised lifestyle, create a version showing the reality behind the image. What changes? What's lost?"

4. "Should Instagram require all ads to be clearly labelled? Should filters be disclosed? Argue your position using the analytical framework we've practised."

---

## Known Limitations

1. **Media literacy analysis can become formulaic.** If students apply the protocol mechanically ("Colour: warm. Audience: teenagers. Technique: lifestyle association") without engaging with WHY these choices matter, the analysis becomes a descriptive exercise rather than a critical one. Teachers should push for the "So what?" — not just "What techniques are used?" but "What effect do they have on YOU?"

2. **The protocol reflects a primarily Western media analysis tradition.** Media conventions, advertising techniques, and audience expectations vary across cultures. Students from different cultural backgrounds may read the same media text differently — these differences should be treated as enriching the analysis, not as errors. The protocol should be adapted when analysing media from non-Western contexts.

3. **Analysing media critically is not the same as rejecting all media.** A risk of media literacy instruction is that students become cynical rather than critical — distrusting everything rather than evaluating specifically. The protocol should help students distinguish between legitimate persuasion (which is transparent about its purpose) and manipulation (which disguises its purpose), not teach them that all media is deceptive.
