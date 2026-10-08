# Active Learning Catalog

The technique library `activity_designer_agent` selects from. Each entry uses the same
compact format so techniques can be compared at a glance and matched to a slot's
purpose, minutes, class size, and modality. These are starting points to *adapt*, not
recipes to transplant — the catalog entry plus the room's actual constraints produce
the activity sheet.

Field key — **Time**: realistic total including launch and debrief. **Size**: class-size
range where it works unmodified. **Modality**: in-person (IP), online-sync (OS),
online-async (OA), with notes. **Prep**: what must exist before class. **For**: the
cognitive work it buys (Bloom levels per Pedagogy Foundations §3) and when to choose
it. **Fails when → fix**: the known failure mode and its standard repair.

---

## 1. Think-Pair-Share

Pose a question; students think/write alone (1 min), discuss in pairs (2 min), pairs
report to the room. The workhorse: lowest-friction way to make everyone commit to an
answer before hearing one.

- **Time:** 5–8 min · **Size:** any (works at 300) · **Modality:** IP, OS (breakout
  pairs); OA → post-then-reply variant
- **Prep:** one good question
- **For:** understand/apply/analyze; choose when you want universal engagement cheaply,
  or as the opening rung before whole-room discussion
- **Fails when** the question is answerable in 10 seconds (pairs chat off-topic) →
  use a question with a defensible wrong answer or a judgment call

## 2. Peer Instruction (with polling)

Concept question via clickers/phone polling → individual vote → if 30–70% correct,
pairs convince each other ("find someone who answered differently") → revote → debrief
why the wrong answers are attractive.

- **Time:** 8–12 min per question · **Size:** 30–500; polling infrastructure required
  past ~60 · **Modality:** IP, OS (poll + breakouts)
- **Prep:** high — a tested concept question with diagnostic distractors
- **For:** understand/analyze, surfacing misconceptions; choose for concepts with
  known seductive wrong answers (`learner_profile.known_difficulties` is the source)
- **Fails when** first vote is >85% correct (nothing to argue) → bank an easier and a
  harder version, deploy by first-vote result

## 3. Minute Paper

Last 3–5 minutes: students write "the most important thing you learned today" and "what
question remains." Collected (paper or form); professor opens the next meeting with
patterns found.

- **Time:** 3–5 min + 10 min instructor review after · **Size:** any · **Modality:** all
- **Prep:** none
- **For:** closure/retrieval (§5) and instructor feedback; the default closure check
  when nothing more specific fits
- **Fails when** responses are never mentioned again (students stop investing) → open
  the next class with 2 minutes of "here's what you said"

## 4. Muddiest Point

Minute paper's diagnostic sibling: "what was the muddiest point today?" One question,
anonymous, brutally honest results.

- **Time:** 2–3 min + review · **Size:** any · **Modality:** all
- **Prep:** none
- **For:** identifying where the lecture failed, especially in dense technical weeks;
  choose over minute paper when you suspect confusion but not where
- **Fails when** everything is "muddy" because the meeting was overstuffed → that's
  arc feedback, not a student problem; route it to next week's plan

## 5. Jigsaw

Topic split into N parts; "expert groups" each master one part, then regroup so each
new group has one expert per part; experts teach their piece; group completes a task
needing all parts.

- **Time:** 25–45 min · **Size:** 12–60 (logistics degrade above; possible with TAs) ·
  **Modality:** IP, OS (double breakout rounds — rehearse the mechanics)
- **Prep:** high — N self-contained materials + an integration task that genuinely
  needs all N
- **For:** apply/analyze across a body of material too large to lecture; choose when
  parts are separable and the integration is the point
- **Fails when** one expert mislearns and teaches the error downstream → give expert
  groups an answer-check key before regrouping

## 6. Gallery Walk

Groups produce an artifact (diagram, proof sketch, design) on posters/whiteboards;
groups rotate, annotating others' work with questions and critiques; authors respond.

- **Time:** 20–35 min · **Size:** 10–50, wall space permitting · **Modality:** IP;
  OS/OA → shared-document gallery with comment rounds
- **Prep:** medium — the production prompt + critique criteria
- **For:** analyze/evaluate/create; choose when comparing multiple approaches IS the
  learning (design choices, proof strategies, study designs)
- **Fails when** critique stays at "looks good" → require every group to leave one
  question and one challenge per poster, criteria on the board

## 7. Case Discussion

Structured whole-room discussion of a teaching case (see `case_study_writer_agent`):
opening stake-out, analysis passes, decision point, debrief against the epilogue.

- **Time:** 30–75 min · **Size:** 10–80 (above ~80, hybrid with pair pre-discussion) ·
  **Modality:** IP, OS; OA → structured board with role-assigned threads
- **Prep:** high — the case + teaching notes; students must have read it
- **For:** analyze/evaluate; choose for judgment under ambiguity, ethics, strategy,
  diagnosis — anywhere defensible disagreement exists
- **Fails when** half the room hasn't read the case → 3-minute open-notes reading
  quiz or pair-recap at the start; never lecture the case as a rescue

## 8. Problem-Based Pairs

Pairs work a problem just beyond the worked example's difficulty while the instructor
and TAs circulate; selected pairs present; instructor synthesizes the solution paths
on the board.

- **Time:** 10–20 min · **Size:** up to ~100 with circulation help · **Modality:** IP,
  OS (breakouts + shared scratchpad)
- **Prep:** medium — the problem, calibrated against the worked example, + the
  circulation question list ("what's your unknown?")
- **For:** apply/analyze; the default follow-up after a worked example (§9), choose
  when the skill is procedural and feedback-during beats feedback-after
- **Fails when** the difficulty jump from the worked example is too large (pairs stall
  silently) → bridge with a faded step (see #9), and circulate to the back rows first

## 9. Worked-Example Fading

Sequence: full worked example → same problem type with last steps blanked → middle
steps blanked → full problem. Each stage done by students, checked before the next.

- **Time:** 15–25 min for a 3–4 stage sequence · **Size:** any · **Modality:** all
  (OA: staged auto-checked steps)
- **Prep:** medium — one problem family, consistent surface features, staged blanks
- **For:** apply, for novices specifically (§9 expertise-reversal: skip stages for
  experienced students — fading bores experts); choose when the learner profile says
  novice and the skill is multi-step
- **Fails when** stages differ in problem type, not just support level (students learn
  four problems, not one skill) → same family throughout, vary only the scaffolding

## 10. Retrieval Starter

First 3–5 minutes: 2–3 questions from *previous* weeks (not last meeting only — spacing,
§5), answered closed-notes individually, then self-checked. Ungraded or trivially
credited.

- **Time:** 4–6 min · **Size:** any · **Modality:** all
- **Prep:** low — question bank grows weekly
- **For:** remember/understand consolidation and arrival ritual; the default opener
  in `lesson_anatomy.md` — choose something else only with reason
- **Fails when** it silently becomes a graded quiz (anxiety replaces retrieval) →
  keep stakes at zero/negligible and say so out loud

## 11. Two-Stage Quiz (collaborative testing)

Short quiz taken individually, submitted, then immediately retaken in fixed teams of
3–4 with discussion; team stage scored lightly or not at all when used formatively.

- **Time:** 20–30 min · **Size:** up to ~100 with managed logistics · **Modality:** IP,
  OS (individual form → breakout team form)
- **Prep:** medium — quiz items that reward discussion (not pure recall)
- **For:** apply/analyze + immediate feedback (§5, §8): the argument in stage two is
  the learning event; choose after a dense technical unit
- **Fails when** teams defer to the loudest member → require teams to flag their least
  confident answer; graded versions belong to assessment-architect

## 12. Fishbowl

5–8 students discuss in an inner circle; the rest observe with a listening task
(track arguments, note evidence quality); rotate membership; observers debrief.

- **Time:** 20–40 min · **Size:** 15–40 · **Modality:** IP; OS → panelists on camera,
  observers in chat with assigned tracking roles
- **Prep:** medium — discussion prompt + observer task sheets
- **For:** evaluate, plus discussion-skill modeling itself; choose in seminars when
  whole-room discussion is dominated by the same four voices
- **Fails when** observers disengage (no task) → the observer sheet is mandatory and
  the debrief calls on observers first

## 13. Role-Play / Structured Debate

Students argue from assigned positions (stakeholders, rival theories, reviewer vs
author) with prep time, timed exchanges, and a step-out-of-role debrief.

- **Time:** 25–50 min · **Size:** 8–60 (parallel pods when large) · **Modality:** IP,
  OS; OA → position-assigned thread debate
- **Prep:** medium-high — role briefs with asymmetric information where possible
- **For:** evaluate/create, perspective-taking; choose when the outcome involves
  weighing genuinely competing interests or frameworks
- **Fails when** students play their own opinion regardless of role → assign roles
  *against* surveyed views; the debrief question "what did your role see that you
  don't?" is mandatory

## 14. Send-a-Problem

Each group writes a problem (with their solution sealed), passes it to the next group
to solve, then to a third group to judge both solution and problem quality.

- **Time:** 25–40 min · **Size:** 12–60 in groups of 3–4 · **Modality:** IP, OS
  (rotating shared docs)
- **Prep:** low-medium — constraints for problem authoring ("must use this week's
  technique; solvable in 5 minutes")
- **For:** create (authoring) + apply (solving) + evaluate (judging) in one structure;
  choose late in a unit when students can already solve standard problems
- **Fails when** authored problems are trivial or impossible → the authoring
  constraints sheet, plus "your group's grade-free reputation rides on a fair problem"

## 15. Statement Correction

Students receive plausible-but-flawed statements, worked solutions with a planted
error, or AI-generated text about the topic; task: find, fix, and justify.

- **Time:** 10–20 min · **Size:** any · **Modality:** all
- **Prep:** medium — flaws must be diagnostic (drawn from `known_difficulties`), not
  typos
- **For:** analyze/evaluate; choose to attack a documented misconception head-on, or
  as an AI-era exercise in critically reading generated text
- **Fails when** students find the planted error and stop looking → state that the
  number of errors is unknown (and sometimes plant none — knowing a statement might
  be fine is part of the skill)

---

## Choosing quickly

| Slot purpose | First candidates |
|--------------|------------------|
| Open the meeting / activate prior knowledge | 10 retrieval starter, 1 TPS on a prediction |
| Break up lecture, check a concept | 2 peer instruction, 1 TPS, 15 statement correction |
| Practice a procedure after a worked example | 9 fading, 8 problem-based pairs |
| Integrate a large body of material | 5 jigsaw, 11 two-stage quiz |
| Compare approaches / exercise judgment | 6 gallery walk, 7 case discussion, 13 role-play |
| Seminar with uneven participation | 12 fishbowl, 1 TPS-first rounds |
| Close the meeting | 3 minute paper, 4 muddiest point |
