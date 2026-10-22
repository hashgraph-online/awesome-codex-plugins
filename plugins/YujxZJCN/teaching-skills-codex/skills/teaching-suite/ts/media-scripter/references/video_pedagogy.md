# Video Pedagogy — Evidence Base for Recorded Teaching Media

What this skill designs against, and how honest the evidence actually is. Recorded
media differs from live lecture in three structural ways: no room feedback loop (the
script cannot adapt mid-delivery), a pause button (students control pacing — design
for it), and fast attention decay (nobody is socially trapped in their seat). Agents
cite this file when justifying a flag or a default; the professor's discipline and
context knowledge overrules any default here, with the decision logged.

## 1. The engagement-length findings (Guo, Kim & Rubin, 2014, ACM L@S)

Analysis of ~6.9 million video-watching sessions across four edX MOOCs:

- **The ~6-minute cliff.** Median engagement time drops sharply for videos longer
  than ~6 minutes; students watching a 12–15-minute video engaged for a median of
  barely 6 minutes regardless of total length. This drives the skill's 6–9-minute
  episode default.
- **Informal beats studio.** Videos with an informal, personal feel (instructor at a
  desk, Khan-style tablet drawing) outperformed high-production studio recordings.
  Production polish is not where the effort belongs.
- **Talking-head insets help.** Interleaving the instructor's face with slides/screen
  beat slides-only presentation for engagement.
- **Pre-production segmentation beats post-hoc chopping.** Videos planned as short
  units outperformed long lectures chopped into pieces after recording — segments
  designed as units have their own arc; saw-cuts don't.

**Honest scope caveats — read before citing as law:** this is observational MOOC
data, not a controlled experiment in university courses. Engagement (watch time) is
not learning; self-selected MOOC audiences differ from enrolled students with credit
on the line; the data predates 2015 viewing habits. Treat 6–9 minutes as a strong
default with a real mechanism behind it (attention + the segmenting principle below),
not a law of nature. A professor's logged reason — "this derivation cannot be split
without destroying it" — legitimately overrides it; the skill then recommends a
chaptered single video with markers.

**In practice:** segmenter_agent defaults to 6–9-minute episodes sized by word count;
storyboard_agent recommends talking-head alternation points; deviations require a
logged reason, not silence.

## 2. Mayer's multimedia principles, operationalized for recorded lectures

From Mayer, *Multimedia Learning* (cognitive-load grounding in Pedagogy Foundations
§9). The five that bite hardest in recorded media, each with its script-level rule:

| Principle | What it says | Script-level rule |
|-----------|-------------|-------------------|
| **Coherence** | Extraneous material hurts learning | Cut decorative b-roll, stock images, and intro music beds; every shot serves the episode's one objective |
| **Signaling** | Cues to structure aid processing | Signpost verbally *and* visually at every turn: "here's the second failure mode" + the on-screen marker, together |
| **Redundancy** | Narrating identical on-screen text hurts | Never read slides verbatim; the slide carries the anchor phrase, the narration carries the explanation — they complement, not duplicate |
| **Segmenting** | Learner-paced chunks beat continuous flow | Episodes are the chunks; within an episode, the retrieval pause is a designed stopping point — the pause button is a feature to script for |
| **Personalization** | Conversational style beats formal | Direct address ("you," "let's"), contractions in the professor's natural register — the script sounds like the professor talking to one student |

**In practice:** script_writer enforces the rules in drafting; storyboard_agent
enforces coherence and signaling in the shot table; violations are flagged with the
principle named, then the professor decides.

## 3. Retrieval integration (Pedagogy Foundations §5, applied to video)

Watching is not learning; retrieval is. Three patterns this skill builds in:

- **In-video pause prompts.** Scripted "pause and predict" beats: pose the question,
  instruct the pause, then confirm on resume. One per episode minimum (SKILL Iron
  Rule 2). Predictions before reveals beat passive worked-example viewing.
- **Between-episode questions.** The series map carries a retrieval question at every
  episode boundary, answerable from episode *n*, built on by episode *n+1* — and
  reaching back further in the sequence where dependencies allow (spacing and
  interleaving, not just immediate recall).
- **Companion quiz pointer.** When the professor wants the retrieval graded or
  LMS-embedded, the series map's questions hand off to assessment-architect (`quiz`
  mode) as seed material — this skill scripts the prompts; it does not build graded
  instruments.

## 4. Production-value honesty

The evidence ordering, bluntly: **audio quality > script quality > segmentation >
video polish.** Students tolerate a webcam and a plain wall; they abandon videos
they cannot hear clearly or that ramble. Effort spent on motion graphics before the
microphone is upgraded is misallocated.

The good-enough setup list (what the recording checklist in the script template
verifies):

- A USB or lapel microphone close to the mouth — not the laptop's built-in mic
- A quiet room and a recorded 10-second silence test before the real take
- Whatever camera exists, at eye level, with light on the face rather than behind it
- Screen recording at a resolution readable on a phone (zoom regions, not 4K hope)
- No editing suite required: single-take-friendly storyboards, cuts only at section
  boundaries

**In practice:** storyboard_agent flags shots needing skills/tools beyond this list
and offers simpler alternatives; the skill never makes studio production a
prerequisite for shipping a teaching video.

## 5. Accessibility standards (Pedagogy Foundations §7; Quality Gate U1)

Built in from the script, not retrofit after recording:

- **Captions**: accurate (terminology verified, gaps marked over guessed), ≤2 lines,
  ~42 characters/line, sense-unit breaks, non-speech information annotated
  (`[equation appears]`), speakers labeled in multi-voice recordings.
- **Audio description by construction**: narration that *describes* visuals ("the
  red curve flattens past n = 1000") instead of pointing ("as you can see") serves
  blind and low-vision students without a separate description track — which is why
  "this graph" is a banned string, not a style nit.
- **Transcripts**: a readable, paragraphed, headed transcript ships with every video
  — first-class output, required for deaf-blind students using braille displays, and
  the artifact every student studies from at review time.
- **Player-independent design**: chapter markers and stated section structure so the
  content navigates by keyboard and screen reader regardless of platform.

**In practice:** scripts are caption-ready by construction (line lengths, described
visuals); a video plan without its caption plan does not pass Phase 4 assembly; the
`audio` mode's visual-to-narration translation doubles as the audio-description test
— if the audio adaptation loses the point, the original narration was leaning on
undescribed visuals.
