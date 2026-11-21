# Craft evidence: design, slop tells, acting, voice, props, sheets (sources with quotes)

Compiled 2026-11-03. Every source below was opened (WebFetch, or curl + pdftotext for PDFs). Quotes marked "verbatim" come from the page text; for pages read through the WebFetch tool the quote is what the tool extracted from the page (small wording drift is possible; PDF quotes are exact). Anything not confirmed on an opened page is marked **unverified**. Rules marked **(derived)** are my synthesis from the cited sources, not a claim any one source makes.

How to use this file: each section has (a) numbered rules an agent can follow and a person can check by looking at a frame or listening to a clip, (b) templates, (c) sources with URL + quote.

---

## 1. Character design that is not generic

### Rules (checkable)

1. **Design from story and job first, looks last.** Before any image prompt, write 5 lines: job/role, what they carry every day, how long they have owned their main clothes, what they want in this video, what is in their way. Check: every visible item on the character can be traced to one of those lines. (Landis: "we're creating the people in the story"; Freund: "Every person I encounter is a collection of what they carry and what they wear"; Carter: "costume design is storytelling"; Hagen's questions.)
2. **Silhouette test.** Fill the character's full-body render with flat black on white. A stranger must name the character (or at least their role) from the black shape alone, and the cast must not be confused with each other. Check: put all cast silhouettes side by side; no two share the same outline. (Valve TF2: "Character Silhouette - Building block of character design - Identifiable at first read"; Riot: "Silhouettes are the single most important thing for champion recognition".)
3. **One defining primary feature, placed in the silhouette.** Pick one signature item or shape (a hat, a tool, a cut of coat, a hair shape) that shows their "source of power" or job, and make it break the outline. Never remove it in later shots or outfits. (Riot: "a defining primary characteristic that's unique to that champion"; "A champion's primary feature should never be removed or significantly altered in any skin.")
4. **Shape language on purpose, not by default.** Choose a dominant shape for the body and face (round = approachable, square = sturdy/reliable, triangle = sharp/dangerous) and a secondary shape for contrast; mixing is allowed and can be used to mislead. Check: you can name the dominant shape and say why. (Walt Disney Family Museum shape-language guide.)
5. **Detail hierarchy: big, medium, small.** Put detail only where the eye should go (face, hands, the signature item); leave rest areas plain. Check: squint at the frame; detail clusters in 1 to 3 places, not everywhere. (Teguh, Riot character artist: "Having detail everywhere is as good as having no detail at all.") Value contrast is highest where the action is (TF2: "Highest contrast at chest level, where weapon is held"; "Gradient from dark feet to light chest").
6. **Proportion carries age and type.** State proportions in numbers (height in cm, head-heights, eye line). Moving features changes the read: per Teguh, "a higher eye height relative to the nose and mouth will shift the character to look a bit more aged" while "bigger eyes bring out a much younger, more exaggerated look."
7. **No twins (asymmetry).** Do not let left and right sides mirror each other in pose, face or costume. Add at least two deliberate asymmetries (a parting, a scar, one rolled sleeve, a bag worn on one side, uneven wear). (Thomas & Johnston warned against "twins", via Wikipedia's 12 principles.)
8. **One flaw, one signature detail.** Give each character one physical imperfection that real people have (a chipped tooth, uneven brows, a nose bump, acne scars, freckles, reading glasses marks) and one personal object/detail with a story. **(derived)** from rules 3 and 7 and from the AI-face findings in section 2 (AI faces are "more average" and too attractive; a flaw moves the face away from the average).
9. **Costume logic: clothes are history.** For each garment write: when bought, how often worn, what work it has done, how it is cared for. Wear goes where the body acts on the cloth: "Where do they lean? Where do they sweat?" (breakdown artist, Upstage Review). New vs old is a story choice: Freund's briefcase "commutes every day on the train, so it's rubbed around on the floor every day" vs one "bought last week and is guarding it carefully, so there's almost no aging to it."
10. **Wear map for clothes (derived from the sources above + Substance wear generators in section 5):** elbows, knees, seat, cuffs, collar edge, hem, pocket mouths, where a bag strap crosses the shoulder, toe and heel of shoes; sweat at collar and underarms; fading on sun-facing surfaces (shoulders, hat crown); dirt in seams and creases. Check: at least 3 wear marks visible in a medium shot, each explainable.
11. **Layering and function fit the world.** Clothing must work for the setting and job (Summers: "Layering is essential"; Carter for Shuri's lab: protective layers for the work, not fashion defaults).
12. **Character colour: a fixed palette, a colour script for change.** Lock 3 to 5 swatches per character (skin, hair, main garment, accent, signature item) as hex + name. Change colour only along a written colour script for the story, not shot by shot. (Eggleston: "A Color Script is a shorthand version of the film that covers the emotions of the film in color and light.") Team or role can be colour-coded (TF2 read hierarchy: "Team - Friend or Foe? Color").
13. **Interior shapes echo the silhouette.** Folds, seams and shadow shapes should repeat the outline's main shape (TF2: "interior details such as clothing folds are chosen to echo silhouette shapes").
14. **Stop when it reads.** Design the 3/4 view first, then the rest (TF2: "Work out design in three quarter pose"). Stanchfield's caution against early detail applies: "Doodling with detail will cause you to lose that first impression."

### Template: character card (one per character)

```
ID: A1  Name:            Age:     Height (cm):   Build:
Story job (1 line):      Daily routine (1 line):  Wants now / obstacle:
Silhouette: dominant shape ___ ; secondary shape ___ ; primary feature that breaks the outline ___
Signature detail (with story): ___      One flaw: ___
Proportions: head-heights ___ ; eye line ___ ; notable asymmetries (>=2): ___
Face specifics (no beauty words): skin texture ___ ; brows ___ ; nose ___ ; teeth ___ ; hair (texture, flyaways) ___
Wardrobe (each item): garment | age | how worn | wear map | care
Palette (3-5 swatches, hex): skin ___ hair ___ main ___ accent ___ signature ___
Never change: ___ (primary feature, palette, scars, logo placement)
```

### Sources

- Valve, Jason Mitchell et al., "Stylization with a Purpose: The Illustrative World of Team Fortress 2", GDC 2008 PDF: https://cdn.fastly.steamstatic.com/apps/valve/2008/GDC2008_StylizationWithAPurpose_TF2.pdf
  - Verbatim: "Read Hierarchy • Team – Friend or Foe? • Color • Class – Run or Attack? • Distinctive silhouettes • Body proportions • Weapons"; "Highest contrast at chest level, where weapon is held • Gradient from dark feet to light chest"; "interior details such as clothing folds are chosen to echo silhouette shapes"; "Character Silhouette • Building block of character design • Identifiable at first read"; "Work out design in three quarter pose"; "Model Sheet ... Solve design problems using silhouette only".
- Riot Games, "Game clarity in League of Legends": https://www.leagueoflegends.com/en-us/news/dev/clarity-in-league/
  - "Silhouettes are the single most important thing for champion recognition in League. This is basically a champion's shadow: What do they look like shrouded in darkness?"; "a defining primary characteristic that's unique to that champion"; silhouette should "highlight their source of power"; "A champion's primary feature should never be removed or significantly altered in any skin."
- Walt Disney Family Museum, "Shape Language" educator PDF: https://waltdisney.org/sites/default/files/2020-04/T&T_ShapeLang_v9.pdf
  - Verbatim: "shapes can tell a story, show personality, and illicit an emotional response in the viewer without using any words"; "Circles and ovals are great to use for friendly faces"; "Square off things like jaws, shoulders, and even hands—they not only feel strong, but can feel difficult to move"; "Triangles are sharp. Exaggerating the size and length of these shapes can heighten fear"; "Circles, squares, and triangles don't always mean one thing. There might be times when shapes are used to disguise the purpose".
- Tommy Gunardi Teguh (3D character artist, Riot Games), 80.lv: https://80.lv/articles/character-design-shape-language-and-readability/
  - "Strong shape language helps push a character's appeal and personality."; "Having detail everywhere is as good as having no detail at all."; "a higher eye height relative to the nose and mouth will shift the character to look a bit more aged".
- Wikipedia, "Twelve basic principles of animation" (summarises Thomas & Johnston 1981): https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation
  - Solid drawing: "Johnston and Thomas warned against creating 'twins'—characters whose left and right sides mirror each other."
- Deborah Nadoolman Landis, Daily Bruin Q&A (2024): https://dailybruin.com/2024/12/05/qa-costume-designer-deborah-nadoolman-landis-talks-career-impact-of-work
  - "we're creating the people in the story"; "costume designers don't need to know how to sew, we need to know how to read"; "You can't design without doing research".
- Landis, NBC DFW: https://www.nbcdfw.com/local/costume-designer-author-landis-brings-dressed-to-dma/2114704/?amp=1
  - "the story always comes first. Glamour is just one tool that a director has to tell the story."
- Ruth E. Carter, ACMI: https://www.acmi.net.au/stories-and-ideas/ruth-e-carter/
  - "Research allows you to understand what you're looking at."; "costume design is storytelling."
- Ruth E. Carter, Black Enterprise: https://blackenterprise.com/meet-the-hollywood-costume-designer-behind-marvels-black-panther/
  - "First, I read through the scenes of the scripts. I get into the words and the characters."
- Ellen Freund (property master, Mad Men), NEA Arts magazine: https://www.arts.gov/stories/magazine/2016/4/making-art-happen/making-character-whole
  - "Every person I encounter is a collection of what they carry and what they wear."; "Each character has objects that make that character whole."; briefcase quotes in rule 9.
- Breakdown artist interview, Upstage Review "Everything new is old again": https://www.upstagereview.org/post/everything-new-is-old-again
  - "You have to be an artist and figure out the actors' anatomies. Where do they lean? Where do they sweat?"; "Breakdown involves taking the 'newness' out of a garment ... Distressing involves huge changes in a costume's appearance – the result of time and physical stress."
- Warner Bros. Studio Tour, costume distressing resource: https://www.wbstudiotour.co.uk/resources/costume-distressing/
  - "As the action happens, the costumes become more damaged. Look at the costume closely and think about the story being told."
- Cynthia Summers (costume designer, The Last of Us), The Art of Costume: https://theartofcostume.com/2023/12/18/the-costumes-of-the-last-of-us-a-written-history-with-costume-designer-cynthia-summers/
  - "Layering is essential"; "When you've got 30 shirts to get through all of the action he goes through, especially in this show with his stunt double, it goes through different levels of breakdown."
- Ralph Eggleston (Pixar), AWN: https://www.awn.com/animationworld/ralph-eggleston-talks-inside-out
  - "A Color Script is a shorthand version of the film that covers the emotions of the film in color and light."
- Walt Stanchfield lessons, Signal v. Noise: https://signalvnoise.com/posts/153-forget-the-detail-and-other-animation-inspired-lessons
  - "Doodling with detail will cause you to lose that first impression."; "Any line or shape you put down on the paper should mean something to the pose."
- GDC Vault, "The Art of Overwatch: Evolving a Legacy" (Petras, Tsang): https://gdcvault.com/play/1024268/The-Art-of-Overwatch-Evolving (session page only; talk content not reviewed; **unverified** beyond the description).
- **Unverified / not reached:** Tom Bancroft, *Creating Characters with Personality* (character hierarchy; only bookseller blurbs seen); Stephen Silver "Five Phases" (story, gesture, design, form, details) appears only in a search snippet; Marcos Mateu-Mestre not consulted; Disney "work in silhouette" quote seen only in a search snippet.

---

## 2. What makes AI characters look like slop (checkable tells)

### Evidence in one paragraph
Generated faces drift to the statistical middle: more average, more symmetric, more attractive, younger, lighter-skinned. People mistake these "average" faces for real ones (AI hyperrealism), so averageness is not a realism win, it is a sameness problem. Diffusion images also carry style artifacts: waxy or glossy skin, glossy eyes, over-soft windswept hair, a "cinematic" look, glitchy clothing details, and objects that do not work.

### Slop checklist (each item is a yes/no check on a frame or clip)

Face and body
1. **Waxy, shiny, glossy or plastic skin**, no pores, no uneven tone. (Kamali et al.)
2. **Glossy or hollow eyes**: overly shiny reflections, misaligned or non-round pupils, "empty gaze". (Kamali et al.)
3. **Hair too soft and windswept** while the rest of the frame is still; hair resolution or colour differs from the rest. (Kamali et al.)
4. **Average, symmetric, attractive face** with no distinctive feature: could be anyone. (Miller et al. via BPS/ANU: AI faces "more average (and therefore less distinctive)"; higher attractiveness was a valid AI cue; Thomas & Johnston "twins".)
5. **Demographic default**: young, light-skinned, slim, unless the prompt fought it. Dinkar et al.: "86.5% of generated images depicted people with lighter skin tones ... 74% were rated as being in a younger age demographic." Bianchi et al.: stereotypes appear "regardless of whether prompts explicitly mention identity". Zhou et al.: women "younger with more smiles and happiness", men "older" with "more neutral expressions and anger". arXiv 2602.00032: "All models show strong overrepresentation of young faces".
6. **The same smile**: lips only (AU12) with no cheek raise or crow's feet (AU6), and a smile that drops off abruptly. (Ekman: Pan-Am vs Duchenne; "The smile may drop off the face too abruptly.")
7. **Teeth**: unlikely alignment, wrong count, teeth overlapping lips. (Kamali et al.)
8. **Hands**: extra or missing fingers, detached thumb. (Kamali et al.)
9. **Frozen upper face while talking**: mouth moves, brows/lids/forehead do not. Tinwell et al. found this "exaggerates the uncanny", "significantly so for fear, sadness, disgust, and surprise".

Wardrobe and props
10. **Clothes straight off the rack**: no creases at elbows/knees, no fading, no lint, no stretch at pockets. **(derived)** from costume sources (wear is where bodies act on cloth; aging must match the story) and Kamali's "too perfect" style artifacts.
11. **Glitched clothing details**: atypical stitching, plaid lines not straight, a strap that merges into the shirt, odd buckles. (Kamali et al.)
12. **Perfect, factory-new props** where the story says they are used daily (Freund briefcase rule). **(derived)**
13. **Dysfunctional objects**: misaligned racket strings, wrong number of guitar strings, impossible mechanisms. (Kamali et al.)
14. **Fake text and logos**: glyph-like letters in no real language. (Kamali et al.)

Scene and style
15. **Over-cinematic**: unnaturally dramatic, picturesque light for an ordinary moment. (Kamali et al. "Cinematization"; guiding question "Does the scene look unnaturally dramatic and cinematic?")
16. **Detail or resolution mismatch** between subjects or parts of the image. (Kamali et al.)
17. **Sociocultural or historical implausibility** (wrong era detail, wrong clothing for place). (Kamali et al. category 5.)

### Counter-rules for prompts (derived)
- Replace beauty words ("beautiful", "flawless", "perfect skin", "8K", "cinematic") with specific, observable features: "visible pores on the nose, faint acne scars on the cheeks, slightly crooked lower teeth, uneven eyebrows, flyaway hairs at the crown".
- State age, skin tone, body type and an ordinary job explicitly; do not rely on defaults (Bianchi et al. show defaults are stereotyped; mitigation by counter-prompting is partial).
- Ask for ordinary light that matches the location (overhead office fluorescent, overcast window light) unless the story needs drama.
- Name wear: "collar slightly frayed, elbows shiny from wear, faded shoulders".
- Approve stills before video; check the list above on the still (matches team practice "stills before animation").

### Sources
- Kamali, Nakamura, Chatzimparmpas, Hullman, Groh, "How to Distinguish AI-Generated Images from Authentic Photographs" (2024): https://arxiv.org/abs/2406.08651 (PDF https://arxiv.org/pdf/2406.08651)
  - Verbatim: "AI-generated images often look a bit too perfect. The people may have glossy, shiny skin, windswept hair, and they may look like a photo in a magazine or a scene from a movie."; "The texture of their skin can often be characterized as waxy, shiny, cartoonish, or glossy."; "People in AI-generated images may have misaligned pupils, pupils that aren't circular, unnaturally glossy eyes, or what may feel like an empty gaze."; "hair can look excessively soft, fine-grained and windswept in a way that is not consistent with the scene."; "Small details in clothing often look glitched and distorted."; "Atypical stitching on the denim jacket and irregular stripes on the shirt. The backpack strap also becomes a part of the shirt."; "AI-generated text can appear glyph-like"; caveat: "professional photographs are often shot and edited to look clean and cinematic in similar ways".
- Miller et al., "AI Hyperrealism" (Psychological Science 2023), ANU repository: https://openresearch-repository.anu.edu.au/items/9f3aa103-8567-43aa-ad01-2290f140a2fc/full
  - "White AI faces are judged as human more often than actual human faces—a phenomenon we term AI hyperrealism."
- BPS Research Digest on the same study: https://bps.org.uk/research-digest/ai-faces-seem-realer-real
  - "AI faces were in fact more average (and therefore less distinctive) than real human faces"; participants "correctly used higher ratings of attractiveness, however, as being more suggestive of an AI than a human face"; generator: "StyleGAN2".
- Dinkar, Jiang, Abercrombie, Konstas, "Erasing 'Ugly' from the Internet" (2025): https://arxiv.org/abs/2511.00749v2
  - "86.5% of generated images depicted people with lighter skin tones, 22% contained explicit content despite Safe for Work (SFW) training, and 74% were rated as being in a younger age demographic."
- Bianchi et al., "Easily Accessible Text-to-Image Generation Amplifies Demographic Stereotypes at Large Scale" (FAccT 2023): https://arxiv.org/abs/2211.03759
  - "Stereotypes are present regardless of whether prompts explicitly mention identity and demographic language or avoid such language. Moreover, stereotypes persist despite mitigation strategies".
- Zhou et al., "Bias in Generative AI" (2024): https://arxiv.org/abs/2403.02726
  - women "were depicted as younger with more smiles and happiness, while men were depicted as older" with "more neutral expressions and anger".
- "Happy Young Women, Grumpy Old Men? Emotion-Driven Demographic Biases in Synthetic Face Generation" (2026): https://arxiv.org/html/2602.00032
  - "All models show strong overrepresentation of young faces, and most also overrepresent White-coded individuals."; "negatively valenced emotions (including sadness and fear) consistently shift outputs toward White, middle-aged, male-coded faces."
- The Persistent, "AI Skews Beautiful": https://www.thepersistent.com/beauty-generative-ai-uncanny-valley-self-esteem/
  - AI women have "flawless skin, thick lashes, big eyes, and preternaturally symmetrical faces"; cites a Washington Post analysis where "a normal woman" prompts gave women who were "thin; 98% had light skin" (Washington Post original **not opened, unverified**).
- Tinwell et al., "Facial expression of emotion and perception of the Uncanny Valley in virtual characters" (Computers in Human Behavior 2011): https://vbn.aau.dk/ws/files/63140615/Facial_expression_of_emotion_and_perception.pdf
  - Verbatim: "a lack of facial expression in the upper parts of the face during speech exaggerates the uncanny by inhibiting effective communication of the perceived emotion, significantly so for fear, sadness, disgust, and surprise but not for anger and happiness."

---

## 3. Acting and emotion that read as real

### Core acting rules (for writing the performance line of a prompt)

1. **Every shot has: objective, obstacle, action.** Write "wants ___, but ___, so she ___". (Hagen: "What do I want?", "What is in my way?", "What do I do to get what I want?"; Hooks notes: "An action pursues a longer term objective"; "A scene should have conflict, otherwise known as an obstacle.")
2. **Thought before emotion, emotion before action.** Order the prompt beats: a cue happens, the character notices (eyes move first), the thought lands (a pause), then the face changes, then the body acts. (Hooks: "Thinking tends to lead to conclusions, and emotion tends to lead to action.")
3. **Play one action until something changes it.** One action verb per beat; switch only on a new cue. (Hooks: "Your character should play an action until something happens to make him play a different action.")
4. **Acting is reacting.** In dialogue, write the listener's reaction as carefully as the speaker's line. (Hooks: "Acting is doing; acting is also reacting"; Meisner: lines delivered only after something prompted them; "living truthfully under imaginary circumstances".)
5. **Given circumstances in the prompt.** Who, where, what time, what just happened before the shot. (Hagen's nine questions.)
6. **Describe physical behaviour, never abstract emotion words alone.** Seedance 2.0 official guide: "Use specific physical details to express emotions, replacing abstract words such as 'very sad' and 'extremely angry.'" Runway: "Instead of abstract concepts, use clear, observable descriptions."
7. **Upper face must move when the character talks.** Name a brow or lid action in every speaking shot. (Tinwell et al.; Ekman via Tinwell: brows are "batons" for emphasis.)
8. **Small, slow, continuous movements beat big ones.** Seedance: "Prioritize slow, gentle, coherent subtle movements, and try to avoid high-burst, large-dynamic actions". Hooks: "Yelling is a weak acting choice." Hedra: the model "sometimes generates overly dramatic hand gestures" so restrain movement in the prompt.
9. **Timing tells.** Genuine expressions have smooth onset and offset; a smile that "drop[s] off the face too abruptly" reads false (Ekman blog). Surprise is "the briefest of all the emotions, lasting a few seconds at most" (Ekman). Krumhuber & Manstead found asymmetry, apex duration and other facial actions predicted genuineness better than AU6 alone, and that judges were worse on static than dynamic displays, so judge emotions on motion, not stills.
10. **Eyes.** Blink at human rates: about 17/min at rest, 26/min in conversation, 4.5/min when reading (Bentivoglio et al.). Thinking makes people look away: gaze aversion rises with cognitive difficulty and helps performance (Glenberg et al. 1998, summarised by Doherty-Sneddon). Listeners look at the speaker much more than speakers look at listeners (75% vs 40% in one study; Argyle 1975 as cited in Frontiers 2016). Speakers look up at the listener at key points and the listener answers with "mhm" or a nod in that "gaze window" (Bavelas et al.).
11. **Breath is part of the emotion.** Respiration tracks "calm-excitement, relaxation-tenseness" (Boiten et al.). Sighs "both express and induce relief from stress" (Vlemincx et al.).
12. **Micro-expressions are short.** A micro-expression "will typically last less than 1/2 of a second" (Wikipedia; Ekman-derived). Use them for leaks of a hidden feeling (suppressed anger, contempt), not as the main performance.

### FACS cheat sheet (EMFACS prototypes, Wikipedia)
Happiness 6+12; Sadness 1+4+15; Surprise 1+2+5B+26; Fear 1+2+4+5+7+20+26; Anger 4+5+7+23; Disgust 9+15+17; Contempt R12A+R14A (R = right side only, A = trace intensity).
AU names: 1 inner brow raiser; 2 outer brow raiser; 4 brow lowerer; 5 upper lid raiser; 6 cheek raiser (orbicularis oculi, orbital part); 7 lid tightener; 9 nose wrinkler; 12 lip corner puller (zygomaticus major); 14 dimpler (buccinator); 15 lip corner depressor; 17 chin raiser; 20 lip stretcher; 23 lip tightener; 24 lip pressor; 25 lips part; 26 jaw drop; 45 blink. Intensity A trace, B slight, C marked, D severe, E maximum.
Duchenne smile = AU6 + AU12; "the insincere and voluntary Pan-Am smile: contraction of zygomatic major alone" (Wikipedia FACS). Why fakes lack AU6: the orbital part of orbicularis oculi is mostly involuntary in enjoyment; Ekman, Davidson & Friesen 1990 found the D smile "related to enjoyment" and "other smiling was not". Nuance: Krumhuber & Manstead 2009 observed "Similar amounts of D and non-Duchenne (ND) smiles" when smiles were posed vs spontaneous, so AU6 is necessary for a good smile on screen but not proof of a felt one; timing and symmetry matter too.

### The six expressions for video (and why these six)
Chosen because they cover what dialogue video actually needs and where models fail most:
- **Neutral listening**: most screen time in a two-person scene is reaction; listeners hold gaze ~75% of the time, so a wrong listening face is visible for long stretches.
- **Genuine laugh**: the most common positive beat in ads and skits; the Pan-Am smile is the classic AI tell.
- **Suppressed anger**: drama lives in held-back feeling; models over-act anger into shouting.
- **Worry**: low-arousal negative emotion that depends on the upper face (inner brows), exactly what Tinwell shows gets lost.
- **Surprise**: the hook beat of short-form video; it must be brief, models tend to hold it.
- **Contempt / smug**: the only unilateral expression (Ekman), so it directly tests the model's symmetry bias; essential for rivals, villains, comedy.
(Plain happiness, sadness, fear and disgust are covered as components: laugh includes happiness, worry borrows sadness/fear brows.)

For each: cause, then physical tells. "Unverified" marks tells I could not confirm on an opened source; they are common acting/animation practice.

**1. Neutral listening**
- Cause: someone else is talking and the character wants to understand (objective) while waiting for a turn.
- Brow: mostly at rest; brief inner/outer brow raise (AU1+2, trace) at news or questions (brow "batons", Ekman via Tinwell).
- Eyes: on the speaker most of the time (listener gaze ~75%); blinks around 17 to 26 per minute; short glance away only when thinking about what was said (gaze aversion with cognitive load).
- Mouth: lips closed and relaxed, no smile held; small "mhm" (AU25 lips part briefly) in the speaker's gaze window (Bavelas).
- Head: small nods timed to the speaker's look (Bavelas: "'mhm,' a nod, or other reaction during this period"); slight head tilt (unverified).
- Hands: still, or one slow self-touch (unverified).
- Breath: slow, quiet, through the nose (unverified); an audible in-breath just before taking the turn (unverified).
- Prompt phrase: "listening quietly, eyes on him, nods twice when he looks at her, blinks naturally" (OmniHuman/Hedra advise explicit verbs like "listening quietly").

**2. Genuine laugh**
- Cause: something unexpected but harmless, usually social banter; Provine found "most of what we laugh at in life is not particularly funny or clever".
- Brow: relaxed or slightly lowered by the cheek push (Seedance joy: "brows and eyes relaxing").
- Eyes: narrowed by raised cheeks, crow's feet, lower-lid bulge: AU6 + AU12 (Ekman: false smiles do not show "raised cheeks, bagged skin below the eyes, crow's feet wrinkles").
- Mouth: lip corners pulled up and back, jaw drops on each laugh burst (AU25/26); smile fades smoothly, not abruptly.
- Head: tips back or forward with the bursts; shoulders shake (unverified).
- Hands: may cover mouth or touch chest (unverified).
- Breath and sound: laugh comes at the end of a phrase, not mid-phrase (Provine "punctuation effect"); bursts of notes "each note lasting about 75 milliseconds and separated by rests of 210 milliseconds"; genuine laughs have "higher and more variable" pitch than posed ones (Pinheiro et al.); a recovery inhale after (unverified).
- Timing: onset fast, offset gradual; symmetric face.

**3. Suppressed anger**
- Cause: interference, injustice, threat, betrayal (Ekman triggers) and a reason not to show it (boss, child, camera): objective = keep control.
- Brow: lowered and drawn together (AU4), held low.
- Eyes: hard stare, lids tightened (AU7) and upper lid slightly raised (AU5) ("the eyes glare", Ekman); fewer blinks (unverified).
- Mouth: lips pressed thin (AU23/24, "narrowing of the lip corners", Ekman); jaw clenched, masseter bulge (Seedance anger row "jawline tense").
- Head: very still; chin down (unverified).
- Hands: grip something (cup, pen, table edge) or a fist kept low (Seedance anger row "both fists clenched", scaled down).
- Breath: held, then a long controlled exhale through the nose (unverified); voice "may have sharp edge to it" when controlled (Ekman).
- Leak: a micro-expression of full anger under 0.5 s, or a polite smile with "traces of muscular actions associated with" anger (Ekman, Friesen & O'Sullivan 1988 masking smiles).

**4. Worry**
- Cause: a possible harm that has not happened yet ("threat of harm, real or imagined", Ekman fear; persistent fear = anxiety).
- Brow: inner corners raised and pulled together (AU1+AU4): "the angling-up of the inner corners of the eyebrows ... especially difficult to fake" (Ekman sadness; same brow appears in fear 1+2+4).
- Eyes: glance away and back, checking (Seedance anxiety row "eyes darting away"; gaze aversion while thinking); blink rate up (unverified).
- Mouth: lips pressed or lower lip bitten; slight lip stretch (AU20) at peaks (FACS fear component).
- Head: slightly down, small turns toward the source of worry (unverified).
- Hands: fidget: Seedance official row "frequently checking the watch, fingers constantly tapping the tabletop, rapid breathing, eyes darting away, unconsciously biting fingernails".
- Breath: faster, shallower, upper chest (Seedance "rapid breathing"; Boiten tenseness dimension).

**5. Surprise**
- Cause: "sudden and unexpected occurrences" (Ekman), e.g. a loud sound, someone appearing.
- Brow: raised high and curved (AU1+2), forehead wrinkles across.
- Eyes: upper lids raised (AU5B, slight-to-moderate), whites above the iris for a moment; less sclera than fear (Ekman fear: upper lid "lifted higher in fear than in surprise").
- Mouth: jaw drops, lips slack and open (AU26), "more open and slack" than fear (Ekman).
- Head: small pull back (unverified).
- Hands: freeze mid-action, then rise (unverified).
- Breath: quick in-breath / gasp (ElevenLabs tag [gasps] exists; physiological claim unverified).
- Timing: peaks fast and resolves within "a few seconds at most" into another emotion (Ekman). Do not hold the surprise face for the whole clip.

**6. Contempt / smug**
- Cause: "immoral action by a person or group of people to whom you feel superior" (Ekman); "I'm better than you and you are lesser than me".
- Brow: neutral or one brow slightly raised (unverified).
- Eyes: steady, maybe lids slightly lowered (unverified); eye roll in comedy (unverified).
- Mouth: one lip corner tightened and pulled up, dimple on that side only (R12A+R14A); "the only emotion with a unilateral facial expression" (Ekman).
- Head: slight tilt back, looking down the nose (unverified).
- Hands: still, relaxed; arms may fold (unverified).
- Breath/voice: short nasal exhale (a "huh") (unverified); ElevenLabs [sarcastic] tag.

### What video models get wrong (checks)
1. Mouth-only emotion: lips move, brows and lids do not (Tinwell). Check: freeze 3 frames during speech; brows or lids differ between them.
2. Pan-Am smile: AU12 without AU6; or smile that snaps off. Check the eyes at the smile's peak.
3. Over-acting and big gestures: wide arm moves, shouting, constant head bobbing (Hedra notes "overly dramatic hand gestures"; Seedance advises small movements).
4. Held expressions: surprise or laughter held for the whole 5 to 8 s clip. Check: expression changes at least once per beat.
5. Symmetric contempt or symmetric "smirk". Check: one side only.
6. Mismatched eyes and mouth: smiling mouth with sad or blank eyes, or gaze that drifts to nowhere (Kamali "empty gaze"). Check eye target per beat.
7. Unnatural blinking: none for long stretches or perfectly rhythmic (Bentivoglio rates as reference; "perfectly rhythmic blinking" as a tell is from vendor blogs, **unverified**).
8. Listener frozen: the non-speaking character has no nods or reactions (Bavelas).
9. Abstract prompts: "she is sad" produces stock sad (Seedance, Runway advice).
10. Demographic drift with emotion: asking for "angry" or "sad" shifts face toward older male (arXiv 2602.00032). Keep identity locked with reference images when changing emotion.

### What official model guides say about describing performance
- Veo 3.1 (Google Cloud blog): formula "[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]"; dialogue in quotes: "Use quotation marks for specific speech (e.g., A woman says, "We have to leave now.")."; example performance wording "A slight, mysterious smile plays on her lips"; "Ingredients to Video: Provide reference images of a scene, character, object, or style to maintain a consistent aesthetic across multiple shots."
- Kling 3.0 (fal prompting guide, hosted provider, not Kling's own site): "Character labels must be unique and consistent. Avoid pronouns or synonyms."; "Bind dialogue to a character's unique actions. Describe the action first, then the dialogue."; voice labels like "[Character, raspy deep voice]".
- Seedance 2.0 (BytePlus official prompt guide): actions "specific to body parts such as hands, legs, head, shoulders, and back, while also supplementing descriptions of range, speed, and force"; "Prioritize slow, gentle, coherent subtle movements"; "Specify the inertia and continuity between preceding and following actions"; "Use specific physical details to express emotions, replacing abstract words"; official examples: Joy "the corners of the mouth rising uncontrollably, brows and eyes relaxing, steps becoming light, unconsciously humming a tune"; Nervousness/anxiety (quoted above); Relief "letting out a long breath, tense shoulders completely relaxing, a long-lost faint smile appearing on the face, looking up toward the distance"; Sadness "lowering the head, shoulders trembling slightly, eyes reddening, fingers unconsciously clutching the corner of clothing, tears welling in the eyes but not falling"; Anger "both fists clenched, jawline tense, chest heaving violently, eyes as sharp as knives, squeezing words out through gritted teeth".
- Runway (Academy prompting guide): "Avoid ambiguous or conceptual language Be specific and concrete. Instead of abstract concepts, use clear, observable descriptions."; "Use positive phrasing"; "Avoid conflicting instructions".
- Runway Act-Two: help-center pages returned 403; "match direction and screen space of driving video and character" and "clear facial expressions, good lighting" come from search snippets only (**unverified**).
- Hedra Character-3: "Describe the delivery ... (e.g., 'speaking in a calm, steady voice')"; "Your audio quality heavily dictates the output. Use clean speech"; restrain over-dramatic gestures in the prompt; "generating a library of approved character angles helps maintain consistency."
- OmniHuman 1.5 (Hedra model page): "Structure your prompts sequentially: [Camera movement] + [Emotion] + [Speaking state] + [Specific actions]"; "Focus entirely on movement, behavior, and camera direction"; "add explicit verbs like 'speaking,' 'singing,' or 'listening quietly'". Dreamina page example: "background characters react subtly with expressions and gestures".

### Template: performance line (one per shot)
```
[Shot/camera]. [Character label, never a pronoun], wants [objective] but [obstacle].
Beat 1 (0-2s): cue -> eyes [target/move] -> [brow AU-level description] -> [mouth] ; hands [specific]; breath [specific].
Beat 2 (2-5s): action verb [one] ; line: "..." delivered [pace, volume, quality].
Listener: [nods / mhm in gaze window / glance away when thinking].
Keep: upper face moves while speaking; small slow movements; no shouting unless scripted.
```

### Sources
- Wikipedia, Facial Action Coding System: https://en.wikipedia.org/wiki/Facial_Action_Coding_System (EMFACS table, AU table, "Pan-Am smile" vs "Duchenne smile" quotes above).
- Ekman, Davidson & Friesen 1990, "The Duchenne smile: emotional expression and brain physiology II", PubMed: https://pubmed.ncbi.nlm.nih.gov/2319446/
  - Verbatim: "Smiling in which the muscle that orbits the eye is active in addition to the muscle that pulls the lip corners up (the Duchenne smile) was compared with other smiling ... the Duchenne smile was related to enjoyment ... and other smiling was not."
- Krumhuber & Manstead 2009, "Can Duchenne smiles be feigned?", PubMed: https://pubmed.ncbi.nlm.nih.gov/20001124/
  - Verbatim: "Similar amounts of D and non-Duchenne (ND) smiles were observed in these 2 conditions"; "The predictive value of the D smile ... was limited compared with other features such as asymmetry, apex duration, and nonpositive facial actions"; differentiation "impaired for static compared with dynamic displays".
- Ekman, Friesen & O'Sullivan 1988, "Smiles When Lying": https://humintell.com/wp-content/uploads/2022/04/Ekman-et-al-1988.pdf
  - Verbatim: "Smiles that included traces of muscular actions associated with disgust, fear, contempt, or sadness occurred more often when subjects were trying to mask negative emotions with a happy mask."
- Paul Ekman Group pages:
  - Smiling: https://www.paulekman.com/blog/science-of-smiling/ — "The smile may drop off the face too abruptly."; "the slight to moderate false smile will not show raised cheeks, bagged skin below the eyes, crow's feet wrinkles."
  - Contempt: https://www.paulekman.com/universal-emotions/what-is-contempt/ — "Contempt is the only emotion with a unilateral facial expression"; trigger "immoral action by a person or group of people to whom you feel superior."
  - Anger: https://www.paulekman.com/universal-emotions/what-is-anger/ — "In anger the eyebrows come down and together, the eyes glare, and there is a narrowing of the lip corners."; controlled anger "may have sharp edge to it".
  - Surprise: https://www.paulekman.com/universal-emotions/what-is-surprise/ — "In surprise, the eyebrows are raised but show more curve than seen in fear."; "Surprise is the briefest of all the emotions, lasting a few seconds at most."
  - Fear: https://www.paulekman.com/universal-emotions/what-is-fear/ — "upper eyelid is also lifted higher in fear than in surprise, exposing more sclera"; "lips are tensed and stretched in fear but more open and slack in surprise"; "The universal trigger for fear is the threat of harm, real or imagined."
  - Sadness: https://www.paulekman.com/universal-emotions/what-is-sadness/ — "One very strong and reliable sign of sadness is the angling-up of the inner corners of the eyebrows. Few people are able to manipulate these muscles voluntarily".
  - Enjoyment: https://www.paulekman.com/universal-emotions/what-is-enjoyment/ — Duchenne smile identified by "crows feet".
- Wikipedia, Microexpression: https://en.wikipedia.org/wiki/Microexpression — "a microexpression will typically last less than 1/2 of a second"; "emotions typically last 0.5–4.0 seconds". (Common "1/25 to 1/5 s" figure: search snippets only, **unverified**.)
- Bentivoglio et al. 1997, blink rate, PubMed: https://pubmed.ncbi.nlm.nih.gov/9399231/ — verbatim: "Mean BR at rest was 17 blinks/min, during conversation it increased to 26, and it was as low as 4.5 while reading."
- Doherty-Sneddon (Univ. of Stirling) article for The Psychologist: https://www.stir.ac.uk/research/hub/file/808611 — verbatim: "adults avert their gaze from other people's faces more when they're dealing with difficult questions and this typically improves accuracy of response (Glenberg, Schroeder, & Robertson, 1998)". (Glenberg 1998 original not opened; Springer paywall.)
- Frontiers in Psychology 2016, "Flexible Coordination of Stationary and Mobile Conversations with Gaze": https://www.frontiersin.org/articles/10.3389/fpsyg.2016.01582 — verbatim: "addressees gazing at speakers more often than the reverse (in one study, 75 and 40% of the time respectively; Argyle, 1975)".
- Kendrick & Holler 2017: https://eprints.whiterose.ac.uk/112376/1/Kendrick_Holler_2017_.pdf — verbatim: "whereas recipients tend to maintain gaze to speakers, speakers alternate their gaze towards and away from recipients as they speak".
- Bavelas, Coates & Johnson 2002, "Listener Responses as a Collaborative Process: The Role of Gaze": https://talkbank.org/ca/access/0docs/bavelas2002.pdf — verbatim: "at key points while speaking the speaker seeks a response by looking at the listener, creating a brief period of mutual gaze called here a gaze window. The listener was very likely to respond with 'mhm,' a nod, or other reaction during this period".
- Provine (laughter) via Deseret News 1997: https://www.deseret.com/1997/4/6/19305158/why-we-laugh/ — "Laughter almost never intrudes upon the phrase structure of speech."; "each note lasting about 75 milliseconds and separated by rests of 210 milliseconds"; "The average speaker ... laughs 46 percent more frequently than do those listening".
- Pinheiro et al. 2021, "Emotional authenticity modulates affective and social trait inferences from voices": https://pmc.ncbi.nlm.nih.gov/articles/PMC8558771 — genuine laughs show "higher and more variable fundamental frequency or pitch".
- Boiten, Frijda & Wientjes 1994, PubMed: https://pubmed.ncbi.nlm.nih.gov/7995774/ — verbatim: "the major dimensions are those of calm-excitement, relaxation-tenseness, and active versus passive coping."
- Vlemincx, Meulders & Luminet 2018, PubMed: https://pubmed.ncbi.nlm.nih.gov/28792624/ — verbatim: "Evidence supports the hypotheses that sighs both express and induce relief from stress."
- Tinwell et al. 2011 (see section 2) — also: "Raised eyebrows typically demonstrate the emotion surprise"; brow movements used as "batons".
- Ed Hooks' seven principles (blog transcription): https://adweaver.blogspot.com/2012/12/7-acting-principle-ed-hooks.html — "Thinking tends to lead to conclusions, and emotion tends to lead to action."; "We humans empathize only with emotion"; "Acting is doing; acting is also reacting"; "Your character should play an action until something happens to make him play a different action"; "Scenes begin in the middle not the beginning"; "A scene is negotiation". (Secondary source; book itself not opened.)
- Notes from an Ed Hooks class: https://honky-dory-trygve.blogspot.com/2009/08/fifty-two-quick-acting-notes-from-ed.html — "An action pursues a longer term objective. (Smile at the girl because you want to date her.)"; "A scene should have conflict, otherwise known as an obstacle."; "Yelling is a weak acting choice."; "A gesture need not be an illustration of the spoken word." (Student notes, secondary.)
- The exact phrase "action in pursuit of an objective while overcoming an obstacle": search snippets only, **unverified** as a Hooks quote.
- Uta Hagen's nine questions, Theatrefolk: https://theatrefolk.com/blog/uta-hagens-nine-questions — "Who am I?", "What time is it?", "Where am I?", "What surrounds me?", "What are the given circumstances?", "What are my relationships?", "What do I want?", "What is in my way?", "What do I do to get what I want?". HB Studio: https://www.hbstudio.org/hagen-institute/the-uta-approach/ — "Who am I? Where am I? What do I want? What stands in my way?"
- Sanford Meisner, Wikipedia: https://en.wikipedia.org/wiki/Sanford_Meisner — emphasis on "the reality of doing"; "live truthfully under imaginary circumstances."
- Official model guides: Veo 3.1 https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1 ; Kling 3.0 (fal) https://blog.fal.ai/kling-3-0-prompting-guide/ ; Seedance 2.0 https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide (JS page; text read from page source) ; Runway https://academy.runwayml.com/guides/prompting-guide ; Hedra Character-3 https://www.hedra.com/models/video/hedra/character-3 ; OmniHuman 1.5 https://www.hedra.com/models/video/bytedance/omnihuman-15 and https://dreamina.capcut.com/resource/dreamina-omnihuman
- **Unverified / not reached:** Walt Stanchfield on acting specifically (only drawing lessons opened); Runway Gen-4 References and Act-Two help pages (403).

---

## 4. How they speak

### Numbers to use

| Speech style | Words per minute | Source |
|---|---|---|
| US conversational (classic benchmark) | ~150 | NCVS as quoted by VirtualSpeech (NCVS page itself 404, original **unverified**) |
| Phone conversation, all words / total time (incl. pauses, overlap) | 196 avg, range 111 to 291 | Yuan, Liberman, Cieri 2006 |
| Same, excluding silences ("net" rate) | 236 avg, 158 to 312 | Yuan et al. 2006 |
| Turn-wise rate | 164 | Yuan et al. 2006 |
| BBC radio news bulletins | 168 | Wikipedia "Speech tempo" |
| Spanish RNE bulletins | 210 | Wikipedia "Speech tempo" |
| Audiobooks | 150 to 160 | VirtualSpeech (ACX "155" claims: search snippets only, **unverified**) |
| Radio hosts, podcasters | 150 to 160 | VirtualSpeech |
| Auctioneers | ~250 | VirtualSpeech |
| Sports commentators | 250 to 400 | VirtualSpeech |
| Syllables | ~4 syl/s typical English, 3.3 to 5.9 | Wikipedia "Speech tempo" |

Other facts: older speakers are slower; men slightly faster than women (about 2%); people talk slower and in longer turns with strangers (Yuan et al.). Pauses: brief < 200 ms, medium 200 to 1000 ms, long > 1000 ms, long ones "occurring only in spontaneous speech" (Campione & Véronis). Fundamental frequency: adult men 90 to 155 Hz, adult women 165 to 255 Hz (Wikipedia, Baken 2000).

### Rules (checkable)
1. **Budget words by clip length.** 150 wpm = 2.5 words per second. Max words = seconds x 2.5 (calm) or x 3 (brisk, ~180 wpm). An 8 s Veo clip fits about 20 words calm. Check: count words in the line before generating. **(derived arithmetic)**
2. **Write the pause plan.** Mark brief pauses with commas, medium with full stops or ellipses, and use a long pause (> 1 s) only when the character is thinking spontaneously. ElevenLabs: "Ellipses (...) convey pauses and emphasis"; v3/v4 do not support SSML break tags.
3. **Speed setting range.** ElevenLabs speed 0.7 to 1.2 on models that have it; "Style and Speed sliders are not available in Eleven v4", so control pace with text (punctuation, line length, tags).
4. **Specify accent as region + class/education + first language + strength.** Example: "native English, working-class Glasgow, thick" or "first language Brazilian Portuguese, São Paulo, university-educated, light accent in English". ElevenLabs advises "thick" rather than "strong" and avoiding "foreign" or "exotic". Pull a real reference from IDEA (search by age, gender, ethnicity, location, occupation) or the Speech Accent Archive (everyone reads the same paragraph, so accents compare like for like).
5. **Pitch and timbre in plain words plus a number.** "Low for a man (about 100 Hz), gravelly, slightly creaky at phrase ends." Creaky voice was rated lower on personality traits and linked with "boredom and sadness"; breathy had a small negative effect; smiling voice was rated most positive (Pearsell & Pape). Use creak and breath on purpose.
6. **One verbal habit, rooted in who they are.** A preferred word or phrase, a sentence shape (fragments vs formal), swearing or never swearing (Final Draft). Do not lean on quirks: "the real reason all their characters sound the same is that they haven't yet figured out who each character really is" (filmmaking.net). Every line must do something: "All talk responds to a need, engages a purpose and performs an action" (McKee, quoted by Lamb).
7. **Cover-the-names test.** Remove speaker names from the script; you must still know who says each line (Miyamoto, MovieMaker).
8. **Emotion via audio tags, compatible only.** v3/v4 tags: [laughs], [whispers], [sighs], [exhales], [sarcastic], [curious], [excited], [crying], [snorts], [mischievously], [clears throat], [shouts], [gasps], [strong X accent]. Pair compatible tags; conflicting pairs like [whispers] [excited] are unstable (ElevenLabs blog, search-snippet wording; the v3 prompting doc says tags work best when "the delivery is already in the voice's training data").
9. **Keep one voice consistent across lines:** same voice_id (not a voice name), same model id (e.g. eleven_v4), same stability and similarity (start 0.5 / 0.75, style 0), fixed seed (best effort only), and pass previous_text / next_text or previous_request_ids when splitting a long read. ElevenLabs: "the AI is non-deterministic; setting the sliders to specific values won't guarantee the same results every time." On varg, eleven_v4 calls by voice name have returned 404; use raw voice ids.
10. **Voice Design prompt structure.** "Native <Language>. <Gender>, <Age range>. <Quality level>. Persona: <2–5 words>. Emotion: <2–3 adjectives>." Preview text "should complement the voice description, not contradict it"; "Longer preview texts tend to produce more stable and expressive results."
11. **Match video-model dialogue labels to the voice line.** Kling: "[Character, raspy deep voice]" labels per character; Veo: line in quotes after "says:"; Hedra: describe delivery ("speaking in a calm, steady voice").

### Template: voice line (one per character)
```
Voice ID / model:  ________ / eleven_v4   seed: ____   stability 0.50  similarity 0.75  style 0
Pace:     ___ wpm default (calm 140-150 | conversational 150-170 | brisk 180-200)
          = ___ words per 8 s clip ; pauses: brief (<200 ms, comma) within phrases,
          medium (200-1000 ms, full stop/ellipsis) between thoughts, long (>1 s) only when thinking
Pitch:    low / mid / high for their range (men 90-155 Hz, women 165-255 Hz); ~___ Hz
Timbre:   2 words (e.g. warm, gravelly) ; phonation: modal / breathy / creaky (where)
Accent:   first language ___ ; region ___ ; class/education ___ ; strength: light / thick
          reference: IDEA sample ___ or Speech Accent Archive speaker ___
Verbal habit (one): ___ (and why, from character)
Emotional default: ___ ; allowed tags: [ ] [ ] ; never: ___
Voice Design prompt: "Native ___. ___, in their ___s. Excellent audio quality. Persona: ___. Emotion: ___, ___."
```

Example: "Pace 165 wpm, clips brisk, swallows the ends of sentences, brief pauses only. Pitch mid-low (~110 Hz), warm, slight creak on 'yeah'. First language English, Manchester, working-class, thick. Habit: starts answers with 'Thing is,'. Default: amused patience; tags [laughs], [sighs]; never [shouts]."

### Sources
- Yuan, Liberman & Cieri, "Towards an Integrated Understanding of Speaking Rate in Conversation", Interspeech 2006: https://www.ldc.upenn.edu/sites/default/files/interspeech2006-towards-integrated-understanding.pdf
  - Verbatim: "we find an overall average rate of 196 words per minute (WPM). For individual conversations, the rate measured in this way ranges from 111 WPM to 291 WPM. If we use the word alignments to exclude silences, non-speech noises and so on, we find an average 'net' speaking rate of 236 WPM"; "When talking with strangers or discussing certain topics, people tend to use longer turns but slower speech rates. In general older people have a slower speech, and males tend to speak slightly faster than females."
- Wikipedia, Speech tempo: https://en.wikipedia.org/wiki/Speech_tempo — "A typical speaking rate for English is 4 syllables per second"; "average rate of bulletins varied from 168 (English, BBC) to 210 words per minutes (Spanish, RNE)".
- VirtualSpeech, "Average Speaking Rate and Words per Minute": https://virtualspeech.com/blog/average-speaking-rate-words-per-minute — "the average conversation rate for English speakers in the United States is about 150 wpm" (attributed to NCVS); audiobooks 150-160; auctioneers ~250; commentators 250-400.
- Campione & Véronis 2002, "A Large-Scale Multilingual Study of Silent Pause Duration": https://mail.sprosig.org/sp2002/pdf/campione-veronis.pdf — verbatim: "categorization in brief (< 200 ms), medium (200-1000 ms) and long (> 1000 ms) pauses, the latter occurring only in spontaneous speech."
- Wikipedia, Voice frequency: https://en.wikipedia.org/wiki/Voice_frequency — "a fundamental frequency from 90 to 155 Hz" (men), "from 165 to 255 Hz" (women), citing Baken 2000.
- Pearsell & Pape 2022, "The effects of different voice qualities on the perceived personality of a speaker", Frontiers in Communication: https://www.frontiersin.org/articles/10.3389/fcomm.2022.909427 — breathy voice "with a high rate of air flow"; creaky voice "characterized by very low frequencies which can be irregularly timed".
- IDEA: https://www.dialectsarchive.com/ — "created in 1998 as the internet's first archive of primary-source recordings of English-language dialects and accents"; built "to provide actors the real-life models they need for their characters' accents and dialects"; samples with "gender, age, year of birth, ethnicity, location".
- Speech Accent Archive (George Mason University): https://accent.gmu.edu/ — "Native and non-native speakers of English read the same paragraph and are carefully transcribed."
- ElevenLabs Voice Design: https://elevenlabs.io/docs/product-guides/voices/voice-design and https://elevenlabs.io/docs/eleven-creative/voices/voice-design — template quoted in rule 10; accent examples "A middle-aged man with a thick French accent", "A young woman with a slight Southern drawl"; pacing "Deliberate and measured pacing"; "Including these types of phrases can sometimes reduce the accuracy of the prompt" (quality phrases for niche voices).
- ElevenLabs v3/v4 prompting guide: https://elevenlabs.io/docs/best-practices/prompting/eleven-v3 — tag lists; "Punctuation significantly affects delivery in v4"; "Tags land more readily when the delivery is already in the voice's training data"; "Eleven v4 is a net upgrade over Eleven v3".
- ElevenLabs audio tags help: https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-audio-tags-work-with-eleven-v3-alpha — "Wrap a short instruction in square brackets and place it in the text where the delivery should change."; "Eleven v4 Turbo (eleven_v4_turbo) also supports audio tags."
- ElevenLabs v4 overview: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4 — "Style and Speed sliders are not available in Eleven v4, and SSML is not supported."
- ElevenLabs TTS settings: https://elevenlabs.io/docs/eleven-creative/playground/text-to-speech — Stability "determines how stable the voice is and the randomness between each generation. Lowering this slider introduces a broader emotional range"; speed 0.7 to 1.2; "the AI is non-deterministic".
- ElevenLabs API, Create speech: https://elevenlabs.io/docs/api-reference/text-to-speech/convert — seed: "our system will make a best effort to sample deterministically"; previous_text "Can be used to improve the speech's continuity when concatenating together multiple generations"; previous_request_ids for "splitting up a large task into multiple requests".
- Ken Miyamoto, MovieMaker: https://www.moviemaker.com/first-draft-seven-ways-to-give-your-characters-fresh-voices/3 — "cover the character names above the dialogue ... you should be able to tell the difference between who is saying what."
- Final Draft blog: https://www.finaldraft.com/blog/how-to-give-your-characters-unique-voices-in-your-screenplays — "Give characters preferred words, phrases, and terminology. One may swear constantly while another may never."; "Don't Depend on Accents or Speech Quirks".
- filmmaking.net: https://filmmaking.net/blog/show_article.asp?id=268 — "What differentiates most character's dialogue is not how they speak...but what they say and the attitude behind it."
- Kristen Lamb on McKee's *Dialogue*: https://www.goodreads.com/author_blog_posts/22013814-talk-is-cheap-harness-the-true-power-of-dialogue — McKee: "All talk responds to a need, engages a purpose and performs an action."
- **Unverified:** NCVS original page (404); ACX 155 wpm; ElevenLabs blog sentence about compatible/conflicting tag pairs (search snippet; blog page not opened).

---

## 5. Props: material, wear, weight, motion, sound

### Rules (checkable)
1. **Every hero prop has an owner, an age and a routine.** "This briefcase is two years old and the character commutes every day" decides its wear (Freund). Check: the passport states age + use frequency.
2. **Material class first: metal or non-metal (dielectric).** Non-metals reflect about 4% at head-on view; raw metals 70 to 100%. Rust, paint and dirt on metal behave as non-metal ("Metal that is oxidized needs to be treated as dielectric"). Check: shiny areas are where bare metal or glossy coatings are, not everywhere.
3. **Roughness tells history.** The roughness map "describes the surface irregularities that cause light diffusion": handled areas polish smooth (shinier) or scuff rough; prompt the finish per zone ("satin anodised body, polished bright on the thumb rest"). **(zone examples derived)**
4. **Real colour values.** Non-metal base colour stays between about 30-50 and 240 sRGB (no pure black or white); use measured values from physicallybased.info (CC0) when describing or building props. Examples (linear RGB): brass 0.910/0.778/0.423; copper 0.932/0.623/0.522; iron 0.530/0.513/0.494; stainless steel 0.669/0.639/0.598; tire rubber 0.023 grey, roughness 0.7; office paper 0.794/0.834/0.884, roughness 0.8; glass IOR 1.52; water IOR 1.333; skin IOR 1.4, roughness 0.5.
5. **Translucency and liquids read through IOR and colour**, not glow: glass 1.52, water 1.33, honey 1.50, coffee 1.34 (physicallybased.info).
6. **Wear map = contact + exposure + time.**
   - Edges and corners most likely to be knocked or scratched (Substance Metal Edge Wear: "areas of your mesh that are most likely to be knocked or scratched").
   - Grime in crevices, edges and flat surfaces (Substance Dirt: "realistic buildup of dirt and grunge in crevices, edges, and flat surfaces").
   - Where hands touch: grip, trigger, buttons, handles, lid edges (polish, paint worn through, oil darkening). **(derived)**
   - Light/UV fading on the side that faces the sun or window; fabrics yellow and weaken (CCI: light "fades colours and weakens fibres"; UV "a major cause of yellowing").
   - Traces of past life: removed stickers leave residue (Savage, via PremiumBeat).
   - Check: each wear mark has a reason written in the passport.
7. **Weather it, then pull back.** "The goal is to dirty a prop too much, and then try to clean it as best as you can." (Savage via PremiumBeat). For AI: ask for the heavy version in a test still, then dial it to the story level.
8. **Scale is stated in mm and shown next to a hand or the character.** Prop sheets "show what they look like from all angles and the scale of the object to the character and environment" (Lemay).
9. **Weight shows in timing.** Heavy things start and stop slowly; loose parts (straps, cables, cloth, hair, liquid) keep moving after the main mass stops and lag when it starts (follow-through, drag). Natural motion follows arcs; mechanical motion can be straight. (Thomas & Johnston via Wikipedia and frankanollie.com.) Prompt the inertia explicitly (Seedance: "Specify the inertia and continuity between preceding and following actions").
10. **Sound: name the material pair and the action.** Foley splits into feet, moves (cloth) and specifics (props). Write prop sound as "material on material + action + space": "steel keys on a glass desk, quick drop, small room". **(template derived)** from Foley categories.
11. **Never-change list and versions.** Lock the identifying features (silhouette, colour, logo position, a specific dent). Productions make multiples at different breakdown levels for continuity (Summers: "30 shirts ... different levels of breakdown"). For AI, keep one approved reference image per state (new, used, damaged) and never mix states inside a scene. **(AI part derived)**
12. **Functional plausibility check.** Strings, buttons, hinges, screws, text and logos must be countable and make sense (Kamali "Dysfunctional Objects", "Text & Logos").

### Template: prop passport
```
PROP ID: P1   Name:                       Owner: A1        Story job (1 line):
State in this video: new / used daily / damaged (reference image per state: ____)
Age: ___ ; use: ___ times per day/week ; how carried/stored: ___
Dimensions (mm): L ___ W ___ H ___ ; weight: ___ g/kg ; scale ref: held in one hand / two hands / sits at A1's hip
Materials (per zone):
  zone | material | metal? | base colour (name + hex/linear) | finish/roughness 0-1 | specular/IOR | translucency
  body | brushed aluminium | yes | 0.916,0.923,0.924 | 0.35 | metal | none
  grip | black rubber      | no  | 0.023 grey         | 0.70 | F0 0.04 | none
Wear map (where + why):
  edges/corners: ___ (knocks)    contact points: ___ (hands)    crevices: ___ (dirt)
  sun side: ___ (fading)         traces: ___ (stickers, repairs, engraving)
Motion: weight feel ___ ; loose parts (strap/cable/liquid/cloth) and how they lag ___ ; arcs vs straight ___
Sound (foley specifics): handled ___ ; set down on ___ ; moving parts ___
Never change: silhouette ___ ; colour ___ ; logo/text position ___ ; signature mark ___
Do not: ___ (e.g. no visible brand logos, no text)
```

### Sources
- Adobe, "The PBR Guide – Part 2": https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2
  - "The F0 for common dielectric materials is typically set to 0.04 (linear) 4% reflective."; "The reflectance value for raw metal is going to be high, in the range of 70-100% specular, which we can map to 180-255 sRGB."; dark values "should not go under 30-50 sRGB", bright values not "higher than 240 sRGB"; "The roughness map describes the surface irregularities that cause light diffusion."; "Metal that is oxidized needs to be treated as dielectric".
- Physically Based database (Anton Palmqvist, CC0): https://physicallybased.info/ and API https://api.physicallybased.info/materials — "A database of physically based values for CG artists"; values in rule 4 read from the API.
- Adobe Substance 3D Painter, Metal Edge Wear: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/metal-edge-wear — "creates the appearance of damage and wear on areas of your mesh that are most likely to be knocked or scratched."
- Adobe Substance 3D Painter, Dirt: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/effects/generators/dirt — "adds realistic buildup of dirt and grunge in crevices, edges, and flat surfaces based on curvature, ambient occlusion."
- Canadian Conservation Institute, CCI Notes 13/1 "Textiles and the Environment": https://www.canada.ca/en/conservation-institute/services/conservation-preservation-publications/canadian-conservation-institute-notes/textiles-environment.html — "Light is essential to viewing and appreciating textiles, but it fades colours and weakens fibres."; "The UV radiation in daylight, sunlight, and some electric light sources is a major cause of yellowing and weakening of fibres."
- Ellen Freund, NEA: https://www.arts.gov/stories/magazine/2016/4/making-art-happen/making-character-whole (quotes in section 1).
- PremiumBeat, "How to weather and age props" (Adam Savage techniques): https://www.premiumbeat.com/blog/how-to-weather-and-age-props — "The goal is to dirty a prop too much, and then try to clean it as best as you can."; "fuller's earth powder to look like dust"; "adding stickers and removing them, leaving behind the residue". (Secondary; Tested videos not opened.)
- Wikipedia, Foley (sound design): https://en.wikipedia.org/wiki/Foley_(sound_design) — Feet: "This category entails the sound of footsteps."; Moves: "rubbing two pieces of the same material together near the microphone"; Specifics: doors and other effects.
- Frank & Ollie site: https://www.frankanollie.com/PhysicalAnimation.html — follow through: "When the main body of the character stops all other parts continue to catch up to the main mass of the character, such as arms, long hair, clothing, coat tails or a dress."; drag: "When Goofy starts to run, but his head, ears, upper body, and clothes do not keep up with his legs."; timing: "More drawings between poses slow and smooth the action."
- Wikipedia, Twelve basic principles: https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation — "Most natural action tends to follow an arched trajectory"; timing establishes mood and weight; "An object's volume does not change when squashed or stretched."
- Brian Lemay, "Production Art" (animation layout/design course PDF): https://brianlemay.com/Pages/animationschool/layout/Production%20Art%204/Production%20Art%20part%201.pdf — verbatim: "Prop designers come up with the 'Prop Sheets' that show what the various objects that the characters will physically interact with in their scenes. They show what they look like from all angles and the scale of the object to the character and environment."
- Cynthia Summers (multiples at breakdown levels): see section 1.
- **Unverified / not reached:** Weta Workshop on prop aging (Tim Ferriss transcript had nothing usable); Adam Savage primary videos; prop master interviews beyond Freund.

---

## 6. Turnaround and model sheet conventions

### Rules (checkable)
1. **Views:** at minimum front, 3/4 front, side (profile), back; full set adds 3/4 back. "A turn or turnaround must include at least a front view of the character, a rear view, a profile, and a three-quarter view." (Robledo, Clip Studio)
2. **Orthographic, no perspective.** "An orthographic drawing means, without perspective. It has width and height, but no depth." (Lemay) For AI sheets: ask for "orthographic, flat front-on camera, no lens distortion, same scale in every view".
3. **Same scale on one ground line with horizontal guides.** Draw lines across all views at top of head, eyes, chin, shoulders, waist, knees, feet. "align the top of the head, the bottom of the chin, the center of the eyes, the shoulders, the waist, and the feet" (Binus). Check: lay a ruler across; every feature sits on the same line in every view.
4. **Neutral pose for 3D; personality pose for 2D.** 3D shows use T-pose or A-pose: "characters are drawn in what is called a 'T-pose' ... straight-on front view, a straight-on side view, and a straight-on rear view" (Lemay). Epic's MetaHuman pipeline standardises on A-pose (conform reposes meshes "into the standard MetaHuman A-pose"); A-pose is generally preferred for shoulder deformation (practitioner forums, **unverified** as a standard). For AI image-to-video references, use a relaxed A-pose or natural standing pose, arms slightly away from the body so the silhouette of the torso is visible. **(derived)**
5. **Size comparison / line-up sheet** for the whole cast on one ground line, heights marked; include key props at scale. "There will also be a 'size comparison' sheet that shows how big the characters are to each other as well as their environments." (Lemay) Disney's Little Mermaid line-up chart was "created at the studio and used during the animation process to ensure character size consistency." (VE Galleries)
6. **Expression sheet**: the character's key expressions and "mouth positions for dialogue", plus how far they can go "without going 'of model'". (Lemay) For AI: the six expressions of section 3, same lighting and angle, same head size.
7. **Hand sheet**: hands and feet drawn separately; model sheets depict "Hand and foot sketches" and "Basic facial expressions" (Wikipedia). For AI: open hand, fist, grip on the hero prop, pointing, relaxed at side.
8. **Prop sheet**: every prop the character touches, all angles, with scale to the character (Lemay).
9. **Colour keys / colour script**: per-character palette swatches plus a scene-by-scene colour script for mood (Eggleston). Keep the character palette identical across sheets.
10. **Solve design in silhouette, design interiors with shadow shapes, work out 3/4 first** (Valve TF2 model sheet slide).
11. **The sheet is the source of truth.** Model sheets keep characters "on model" (Wikipedia); Pixar's model packets serve as design blueprints (Cooper Hewitt description via search snippet only, **unverified**: page redirected).
12. **AI-specific checks (derived):** same face identity in every view (compare eye spacing, nose shape, hairline); same costume details count (buttons, pockets, wear marks) in every view; back view invented details match the front; no perspective foreshortening between views; plain neutral background; even flat light so no view hides details.

### Template: sheet pack per character
```
1. Turnaround: front | 3/4 front | side | 3/4 back | back ; orthographic ; one ground line ;
   guide lines at head top, eyes, chin, shoulders, waist, knees, feet ; A-pose ; flat light ; grey bg
2. Expression sheet: neutral listening, genuine laugh, suppressed anger, worry, surprise, contempt
   (same head size and angle; 3/4 front; note AUs under each)
3. Hand sheet: relaxed, fist, open palm, pointing, gripping hero prop P1
4. Prop sheet: each prop front/side/top + one in-hand view; mm dimensions; wear map callouts
5. Line-up: whole cast + key props at scale, height lines every 10 cm
6. Colour key: palette swatches (hex) for character and props; scene colour script strip
```

### Sources
- Wikipedia, Model sheet: https://en.wikipedia.org/wiki/Model_sheet — "A model sheet – also called a character board, character sheet, character study, or simply study – is a document used to help standardize the appearance, poses, and gestures of a character in arts such as animation, comics, and video games."
- Julio Robledo, Clip Studio tutorial "Model Sheets for Character Designers": https://www.clipstudio.net/how-to-draw/archives/164740 — turnaround quote in rule 1; "draw the lines where the most important elements should go: the center of the eyes, the chin, the eyebrows, shoulders etc."
- Binus University DKV, "Character Turnarounds: Understanding Form in 2D Space": https://binus.ac.id/bandung/dkv/2025/11/04/character-turnarounds-understanding-form-in-2d-space/ — five views; "Simple horizontal guidelines drawn across the page that connect key features"; T-pose or A-pose.
- Brian Lemay, "Production Art" PDF: https://brianlemay.com/Pages/animationschool/layout/Production%20Art%204/Production%20Art%20part%201.pdf — quotes in rules 2, 4, 5, 6, 8.
- VE Galleries, Little Mermaid character line-up comparative size chart (1989): https://www.vegalleries.com/art/walt-disney/156/the-little-mermaid-1989/the-little-mermaid-character-line-up-comparative-size-chart-1989 — "created at the studio and used during the animation process to ensure character size consistency."
- Charles Merritt Houghton, "Character Comparison Charts": https://cmerritthoughton.substack.com/p/character-comparison-charts-establishing — "Place each character in a neutral stance, lining them up side by side. Use the height of your main character as a reference"; "Animation giants like Pixar and DreamWorks use comparison charts extensively" (studio claim **unverified** beyond this author).
- Epic Games, MetaHuman body conform controls: https://dev.epicgames.com/documentation/en-us/metahuman/body-conform-controls — verbatim: "When enabled, the fitting algorithm assumes the source body mesh is already in a MetaHuman A-pose ... When disabled, the fitting process reposes the mesh into the standard MetaHuman A-pose after joint fitting, ensuring compatibility with MetaHuman animation and retargeting assets".
- Valve TF2 GDC 2008 PDF (section 1): model sheet steps.
- Ralph Eggleston, AWN (section 1): colour script.

---

## Ten best sources (for the guide's bibliography)
1. Kamali et al. 2024, How to Distinguish AI-Generated Images from Authentic Photographs — https://arxiv.org/abs/2406.08651
2. Seedance 2.0 official prompt guide (BytePlus) — https://docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide
3. Wikipedia FACS (EMFACS table + AU list) — https://en.wikipedia.org/wiki/Facial_Action_Coding_System
4. Tinwell et al. 2011, upper-face animation and the uncanny — https://vbn.aau.dk/ws/files/63140615/Facial_expression_of_emotion_and_perception.pdf
5. Paul Ekman Group emotion pages + smiling blog — https://www.paulekman.com/blog/science-of-smiling/
6. Valve, Stylization with a Purpose (TF2) — https://cdn.fastly.steamstatic.com/apps/valve/2008/GDC2008_StylizationWithAPurpose_TF2.pdf
7. Riot, Game clarity in League of Legends — https://www.leagueoflegends.com/en-us/news/dev/clarity-in-league/
8. Yuan, Liberman, Cieri 2006, speaking rate in conversation — https://www.ldc.upenn.edu/sites/default/files/interspeech2006-towards-integrated-understanding.pdf
9. ElevenLabs Voice Design + v3/v4 prompting + API docs — https://elevenlabs.io/docs/product-guides/voices/voice-design , https://elevenlabs.io/docs/best-practices/prompting/eleven-v3 , https://elevenlabs.io/docs/api-reference/text-to-speech/convert
10. Adobe PBR Guide part 2 + physicallybased.info — https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2 , https://physicallybased.info/
(Close runners-up: Ellen Freund NEA interview; Brian Lemay Production Art PDF; Bavelas 2002 listener gaze; Bentivoglio 1997 blink rates.)
