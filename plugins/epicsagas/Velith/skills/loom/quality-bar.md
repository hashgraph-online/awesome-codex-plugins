# Velith Quality Bar

Shared reference for every writing, editing, and reviewing agent. Read this before drafting, critiquing, or scoring. `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md`.

## The bar

A cold reader who buys books in this genre finishes the manuscript and cannot tell it was machine-drafted. Not "acceptable for AI." Not "good for a first draft." Publishable, next to the top titles in its category, judged by someone who reads that category for pleasure or profession.

The pipeline exists to reach this bar. Word counts, frontmatter, and file existence are bookkeeping. The bar is the reader's experience.

## Scoring rubric (5 axes, 1-10 each)

Every critique, readiness report, and self-review scores these five axes. Anchors describe what a 4, 7, and 9 look like. Be honest: a 7 is a real achievement, a 9 is rare.

### 1. Voice and prose

- **4** — Competent, interchangeable. Could be any book. Sentences are correct and forgettable. Rhythm is uniform.
- **7** — A recognizable voice. Sentence length varies with meaning. Word choice is specific to this author and this book. Occasional flat passages.
- **9** — The voice is the reason to keep reading. Prose does work that the plot or argument alone could not. A reader would quote lines.

### 2. Structure and pacing

- **4** — Chapters are the same shape. Every scene or section runs the same length and ends the same way. Tension or argument neither builds nor releases.
- **7** — The book has a shape. Pacing changes deliberately. Setups pay off. A few sections could be cut or reordered without loss.
- **9** — Nothing is skippable. Every chapter changes the reader's position. The ending is inevitable in retrospect and surprising in the moment.

### 3. Depth (character for fiction, argument for nonfiction)

- **4** — Characters state their feelings and motives. Arguments assert conclusions and move on. Nothing contradicts itself in an interesting way.
- **7** — Characters want conflicting things and act on them. Arguments anticipate the strongest objection. There is subtext.
- **9** — People and ideas surprise the reader while remaining consistent. The book knows something the reader did not, and shows rather than announces it.

### 4. Specificity and grounding

- **4** — Generic details. "A city street." "Studies show." Numbers that could be invented. Sensory detail as decoration.
- **7** — Concrete, particular details chosen for meaning. Claims traceable to sources. Settings that could only be this place.
- **9** — Details the reader has never seen written down before but recognizes as true. Every fact checks out. The world or the evidence has texture.

### 5. Reader experience

- **4** — The reader could stop at any chapter break and not mind. Confusion or boredom appears within the first three chapters.
- **7** — The reader wants to continue at most chapter breaks. No confusion the author did not intend. One or two slow stretches.
- **9** — The reader resents interruptions. They recommend the book. They remember it a month later.

**Gates.** Voice lock requires axis 1 ≥ 7 on the sample chapter. Readiness (Phase 4 exit) requires every axis ≥ 7, mean ≥ 7.5, and no put-down point in the first three chapters. Publishing without a PASS readiness verdict requires an explicit author override.

## The 2026 AI-tell taxonomy

Frontier models no longer say "delve" or "tapestry." Readers now detect machine text through rhythm, structure, and emotional handling. These are the tells that matter. Each entry: what it looks like, why a human reader notices, how to fix it.

### Structural tells (language-independent)

| Tell | What it looks like | Why readers notice | Fix |
|------|--------------------|--------------------|-----|
| Uniform paragraph length | Paragraphs of 3-5 sentences, all similar, page after page | Human writing has one-line paragraphs and page-long ones | Vary by function. A revelation gets its own line. A description can run |
| Punch-line closure | Every paragraph and every scene ends on a short, resonant sentence | Once noticed it feels like a tic, and it is | Let most paragraphs end mid-thought. Save the punch for where it matters |
| Tricolon addiction | Lists of three: "cold, dark, and silent." Three examples. Three-beat rhythm | Human writers use two, four, or one far more often | Count them. Break most of them |
| Symmetrical scenes | Every scene: establish, complicate, turn, reflect. Same length, same shape | Real scenes are lopsided. Some are two lines | Let scene length follow the weight of the event |
| "Not X but Y" | "It wasn't fear. It was something older." "This isn't about the money. It's about trust" | Manufactured profundity; the construction substitutes for insight | State the thing. Or cut it |
| Balanced antithesis | "She had lost everything and found herself" | Sounds like a greeting card | Asymmetry. Let one side be heavier |
| Reflective coda | Scene ends with the character or narrator reflecting on what it meant | Explains the meaning the scene already delivered | End on action, image, or dialogue. Trust the reader |
| Em-dash cascade | Multiple em-dashes per paragraph, used for every kind of pause | Overuse flattens the tool. Editors flag it instantly | Commas, periods, parentheses. One em-dash per page is plenty |
| Rhetorical question chains | "What did it mean? Was it worth it? Could she go on?" | Questions the text will answer anyway | Cut. Or answer one |
| Summary-then-scene | Paragraph telling the reader what is about to happen, then the scene | Double delivery | Delete the summary |
| Thematic name-dropping | Characters or narrator naming the theme ("this was about forgiveness") | Theme should be felt, never labeled | Cut every sentence that names the theme |

### Emotional and character tells (fiction, memoir, narrative nonfiction)

| Tell | What it looks like | Fix |
|------|--------------------|-----|
| Precise self-knowledge | Characters articulate their feelings and motives exactly ("I realized I was afraid of being seen") | People misread themselves. Let them be wrong, evasive, or silent |
| Physical-reaction inventory | "Her stomach dropped. Her hands trembled. Her breath caught" as a substitute for interiority | One specific reaction, or none. Or an action that reveals the feeling sideways |
| Universal kindness | Every character is reasonable, articulate, and ultimately understandable | Some people are petty, dull, or cruel without a redemptive backstory |
| Dialogue that answers | Every line responds directly to the previous line | People interrupt, deflect, answer a different question, repeat themselves |
| "Something shifted" | "Something in her shifted." "A beat." "The air changed" | Name the specific thing, or show its consequence |
| Tidy resolution | Every setup pays off; every conflict resolves; the ending explains itself | Leave one thread loose. Let one question stay open |
| Interchangeable voices | Every character speaks in the same register with the same vocabulary | Each speaker: a verbal habit, a favorite evasion, a sentence-length signature |
| Sensory garnish | A smell, a sound, a texture added to each paragraph like seasoning | Sensory detail only where the character would notice it, and only what they would notice |

### Nonfiction and technical tells

| Tell | What it looks like | Fix |
|------|--------------------|-----|
| Hedged authority | "Many experts believe," "it could be argued," "research suggests" without a source | Name the source or make the claim in your own voice |
| Invented specificity | "A 2019 Stanford study found a 34% improvement" | Every number, study, and quote must trace to `sources/` or a verified URL. Otherwise cut |
| Framework inflation | Every chapter introduces a named framework with an acronym | One framework per book, if any. Most insight does not need a name |
| Listicle drift | Bullets replacing argument. Five bullets where two sentences would do | Convert bullets to prose unless the items are genuinely parallel and scannable |
| Preview-and-recap | "In this chapter we will..." and "In this chapter we learned..." | Cut both. Chapter titles and transitions do this work |
| Uniform confidence | Every claim delivered with the same certainty | Signal which claims are settled, contested, or the author's speculation |
| Analogy padding | An analogy for every concept, whether or not it clarifies | Keep the analogy only if it survives without the literal explanation beside it |
| Code without consequence | Code blocks that illustrate but never fail, never surprise, never get debugged | Show the wrong version first. Show the error message. Show the fix |

### English lexical tells (still worth checking)

delve, tapestry, testament to, navigate (metaphorical), landscape (metaphorical), nuanced, multifaceted, plethora, myriad, robust, seamless, leverage (verb), unpack, at its core, in today's fast-paced world, it's worth noting, it's important to remember, serves as a reminder, a beacon of, resonate, journey (metaphorical), embark, foster, underscore, pivotal, crucial (more than twice per chapter), game-changer, groundbreaking, transformative, holistic, synergy, paradigm, elevate, vibrant, bustling, whisper (of anything non-vocal), dance (of anything non-dancing), symphony (of anything non-musical).

### Korean lexical and syntactic tells (한국어 AI 문체 징후)

| 징후 | 예시 | 수정 |
|------|------|------|
| 번역투 무생물 주어 | "이 사실은 우리에게 ~을 알려준다", "그 경험은 그녀를 변화시켰다" | 사람 주어로. "그녀는 그 일을 겪고 달라졌다" |
| ~것이다 남발 | 문단마다 "~할 것이다", "~인 것이다"로 종결 | 단정형 "~다", "~했다"로. 강조는 한 장에 한두 번 |
| 피동 과잉 | "~되어졌다", "~라고 여겨진다", "~로 보여진다" | 능동으로. "~라고 본다" |
| 감정 명명 | "그녀는 슬픔을 느꼈다", "불안감이 밀려왔다" | 행동, 침묵, 사물로. 감정 단어 자체를 지운다 |
| 접속부사 연쇄 | 그러나, 하지만, 또한, 따라서, 그리고가 문장마다 | 대부분 삭제. 문장 순서가 논리를 보여준다 |
| ~에 대해/~을 통해 | "이 문제에 대해 생각했다", "대화를 통해 알게 되었다" | 조사로. "이 문제를 생각했다", "대화하다 알게 되었다" |
| 대명사 과잉 | 그, 그녀, 그것이 한 문단에 여러 번 | 한국어는 주어 생략이 자연스럽다. 이름이나 생략 |
| 복수 ~들 남발 | "사람들의 생각들", "많은 기억들" | 단수로. 한국어 복수는 필요할 때만 |
| 존댓말·반말 혼용 | 같은 인물이 같은 상대에게 말투가 바뀜 | 인물별 관계별 말투 표를 바이블에 고정 |
| 시제 흔들림 | 과거 서술 중 갑자기 현재형, 또는 반대 | 서술 시제 고정. 현재형 삽입은 의도적 장면에서만 |
| 균일한 문장 길이 | 모든 문장이 25-40자 | 한 단어 문장과 세 줄 문장이 공존해야 한다 |
| 설명형 대화 | 인물이 상황을 독자에게 설명하듯 말함 | 인물은 서로 이미 아는 것을 말하지 않는다 |
| 한자어 과밀 | "인식하였다", "존재하였다", "수행하였다" 연속 | 고유어 동사로. "알았다", "있었다", "했다" |
| 과잉 수식 | 형용사·부사가 명사·동사마다 붙음 | 수식어 절반 삭제. 남는 수식어가 힘을 얻는다 |

### Japanese notes (日本語)

Watch for: 「〜のだ」「〜のである」の連発, 「〜と感じた」による感情の名指し, 三点リーダの多用, 翻訳調の無生物主語, 敬体・常体の混在, 「そして」「しかし」の文頭連続. 会話文は人物ごとに語尾と一人称を固定する.

## How to critique (cold-read protocol)

Used by chapter-writer self-review, style-doctor, continuity-editor, beta-reader, and every editing stage.

1. **Read once at reading speed.** Do not fix anything. Mark only where your attention dropped, where you were confused, where you felt the machine.
2. **Diagnose the marks.** For each: what specifically caused it? Quote the line. Name the tell or the craft failure.
3. **Score the five axes** with one sentence of justification each. Justify the number, do not justify a generous number.
4. **Prioritize.** The three fixes that would most raise the lowest axis. Then the rest.
5. **Only now revise.** Fix the prioritized items first, then the taxonomy hits. Re-read the revised passage aloud in your head. Vary what became uniform.

A critique with no quoted lines is not a critique. A critique where every score is 8 or 9 is not a critique.

## Language and format notes

- **Korean (ko):** Length is measured in characters excluding whitespace (자), and publishers still speak in 원고지 매수 (200자 원고지: chars ÷ 200 × ~1.4 for spacing). A 장편 is 80,000-120,000자; 경장편 50,000-80,000자; 단편 15,000-25,000자. Dialogue uses 큰따옴표. Paragraph indentation is one space in print; markdown drafts use blank-line separation and let the publish stage handle indentation.
- **English (en):** Novel 70,000-100,000 words; literary and debut fiction trends shorter; epic fantasy longer. Nonfiction 50,000-75,000. Curly quotes and proper em-dash spacing per house style are a copy-edit concern, not a drafting one.
- **Japanese (ja):** Length in 文字数; 長編 is 100,000-150,000字. Dialogue in 「」. Line breaks after every dialogue line.

## What this document is not

It is not a checklist to run once at the end. It is the standard every agent holds while working. A chapter drafted to this bar needs less editing. A chapter drafted to word count needs to be rewritten.

## Visuals

Images are held to the same bar as prose: a reader should not be able to tell which model rendered them, and should never wonder why an image is there.

- **One look per book.** `art-bible.md` defines medium, palette, line, lighting, composition, character and setting constants, and the figure system. Every prompt is compiled from it (`velith.mjs images compile`); no free-form prompts.
- **Purpose before decoration.** Every image has a purpose sentence: what the reader gets that the text cannot give. "Visual interest" is not a purpose.
- **Code for anything with text, data, or dimensions.** Diagrams, charts, technical drawings, maps' base layers, ornaments are rendered from source (Mermaid, D2, Graphviz, SVG, matplotlib), never by a diffusion model. Labels are the bible's words.
- **Look lock before volume.** Three samples, the author picks, the choice and references are recorded. Then production.
- **Vision QA on every image.** The producing agent opens the file and scores palette, medium, constants, composition, artifacts, fit to purpose (1-5). A 2 rejects. Three rounds, then escalate.
- **Consistency review.** The art director views the contact sheet, including the cover, before publishing.
- **Release constraints.** 300 dpi at final size for print, grayscale-safe unless a color book, sRGB and < 500 KB for EPUB, alt text on every image, no text inside images except the cover.

Visual tells: a different palette per chapter; characters whose faces change; diffusion-rendered diagrams with garbled labels; stock-photo generic scenes; images that restate the caption; decorative spot art that repeats one motif on every page; covers that belong to a different book than the interior.
