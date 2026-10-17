# Lesson Anatomy

The class-meeting structure this skill enforces by default. `lesson_planner_agent`
plans against it; the other build agents inherit it through the confirmed arc. It is a
default with stated flex points, not dogma — when a professor's format breaks it for a
reason, record the reason and move on (Checkpoint Protocol).

## The five-part arc

```
ACTIVATION → INPUT (segmented) → PROCESSING (active) → CHECK → CLOSURE
                 └────── repeat input/processing cycles as needed ──────┘
```

### 1. Activation (3–5 min)

Open by waking up what students already have, not with housekeeping. Default: a
retrieval starter on *prior weeks'* material (catalog #10; spacing per Pedagogy
Foundations §5). Alternatives: a prediction prompt the session will resolve, or the
real problem today's concept exists to solve. Announcements come after — latecomers
miss the slide, not the learning.

### 2. Input, segmented (≤20–25 min per segment)

First exposure to new material — lecture, demonstration, derivation. Rules applied:

- **Segmenting** (§9): one idea per segment; a segment carrying three concepts is
  three segments or a cut.
- **Signaling** (§9): each segment opens with why-this-matters and where-it-sits
  before any mechanism — signal before detail.
- **Worked examples** (§9): every new concept gets one stepped worked example with
  the reasoning narrated, before students face an open problem. For an experienced
  audience per `learner_profile`, compress toward problems — the expertise-reversal
  effect means scaffolding that helps novices actively costs experts.
- **The 20–25 minute cap** is where attention data and the active-learning evidence
  (§4) converge: input runs longer than that only with a stated reason at the arc
  checkpoint.

### 3. Processing, active (5–20 min)

Students do something with the input while feedback is still possible: the catalog
slot. The processing task rehearses what the week's outcome demands at its Bloom level
(§2, §3) — an "analyze" outcome processed only by recall questions is misalignment in
miniature. Input→processing cycles repeat as the meeting length allows.

### 4. Check (2–10 min, may merge with processing)

Evidence of whether it landed, while there's still time to react: a peer-instruction
revote, a problem attempted solo, three cold-form questions. Distinct from processing
in purpose — processing is for learning, the check is for *information*, flowing to
the professor (reteach next meeting?) and to students (do I actually have this?).
Ungraded by default; graded instruments belong to assessment-architect.

### 5. Closure (3–5 min, never skipped)

The protected segment: contingency plans cut input depth, never closure. Default:
minute paper or muddiest point (catalog #3, #4), plus a one-sentence forward link to
the next meeting. Ending mid-content at the bell costs the consolidation moment that
retrieval at closure provides (§5).

## Timing discipline

- Segment minutes sum to meeting length **minus 2–3 minutes of slack**. A plan that
  needs perfection to fit is a plan to run long.
- Activities are budgeted launch-to-debrief, not task-time-only.
- Every plan names its contingencies: which segment compresses or drops when long
  (never closure), what extends when short (a deeper debrief or a second problem —
  pre-planned, not improvised).
- `assessments_due` weeks reserve real minutes for collection/questions/debrief.

## Format flexes

### Flipped (`flipped` mode)

First-exposure input moves to the pre-class spec (video segments ≤6–8 min each,
caption note per Quality Gate U1, with an entry check — short quiz or notes prompt —
because unverified pre-class work silently reverts the room to first-exposure lecture).
The in-class arc becomes: activation = entry-check debrief targeting what the pre-class
data shows was missed → extended processing blocks (this is the entire payoff of
flipping — apply/analyze work with the professor in the room) → check → closure.
In-class re-lecture of the video's content is the classic flipped failure: it teaches
students the video is optional. Budget a 5-minute targeted-clarification cap instead.

### Online-async

The arc maps to a weekly module, not a meeting: activation = retrieval quiz unlocking
the module; input = segmented short videos/readings (same one-idea rule, captioned);
processing = structured discussion-board work or auto-checked staged problems (catalog
async variants); check = low-stakes quiz; closure = a synthesis post or one-paragraph
reflection. Timing discipline becomes *workload* discipline: estimate hours honestly
and reconcile against the passport's `workload_audit`.

### 3-hour block

Never one arc stretched thin — run 2–3 full arc cycles with a real break (8–10 min,
announced and honored) between cycles. Each cycle gets its own micro-closure; the
final closure spans the whole block. Front-load the heaviest input into cycle 1 while
attention is highest; cycle 3 leans processing-heavy (a longer catalog technique —
jigsaw, gallery walk, case discussion — earns its minutes here).

### 50-minute meeting

The arc compresses but keeps all five parts: activation 3, input 18–20, processing
8–10, check folded into processing, closure 3. What drops is the second input cycle,
not the active segment — a 50-minute pure lecture is the pattern §4's evidence
argues hardest against.
