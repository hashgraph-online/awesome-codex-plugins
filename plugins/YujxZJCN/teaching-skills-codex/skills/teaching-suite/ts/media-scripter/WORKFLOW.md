---
name: media-scripter
description: "Recorded-media scripting for university professors. 4-agent team turning lecture notes and flipped-class specs into mini-lecture video scripts, shot-by-shot storyboards, 6–9-minute episode series, cleaned captions/transcripts, and podcast-style audio adaptations. Scripts are spoken language with built-in accessibility — not read-aloud prose. Triggers on: video script, record a lecture, lecture video, mini-lecture, screencast, storyboard, captions, transcript, subtitles, podcast, flipped video, MOOC, 录课, 慕课, 视频脚本, 微课, 录屏, 字幕, 讲稿, 播客, 翻转课堂视频."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 2
  related_skills:
    - lesson-builder
    - deck-studio
    - teaching-pipeline
---

# Media Scripter — Recorded Teaching Media Team

Scripts what the professor says into a camera or microphone: lesson-builder decides
what the pre-class material *covers*; this skill scripts the actual videos and audio.
Recorded media obeys different rules than a live lecture — there is no room to read,
the student has a pause button, and attention decays fast — so scripts are tighter,
segmented, and signposted in ways live notes never need to be. The professor brings
the content and their own voice; this skill brings spoken-register craft, the recorded-
media evidence base, and accessibility built in from the first draft.

> **Prime rule:** lecture notes are raw material, not the script. Prose that reads
> well silently dies on camera. Every script passes the read-aloud test before it
> reaches the professor — and every script ships with its transcript, because captions
> are planned at the start, not bolted on after recording.

## Quick Start

```
Write a video script for my Week 5 flipped class on hash tables
帮我把这章内容拆成几个微课视频，每个不超过 8 分钟
Storyboard a screencast demo of debugging a segfault in gdb
Clean up this auto-generated transcript — the terminology is mangled
Turn my recorded lecture into a podcast episode students can listen to commuting
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `script` | "Write a video script for…" — one mini-lecture | Two-column script: narration + visual cues + timing, from `ts/media-scripter/templates/script_template.md` |
| `storyboard` | "Storyboard / plan the shots for…" — screencasts, demos, visual-heavy segments | Shot-by-shot plan: what's on screen, what's said, screen-action cues, production notes |
| `series` | "Break this topic/week into videos" — more than one episode's worth | Episode sequence (6–9 min each) with per-episode objectives and the retrieval question between episodes, from `ts/media-scripter/templates/series_map_template.md` |
| `captions` | "Fix these captions / clean this transcript" — raw auto-transcript in hand | Accurate caption file + readable transcript document: terminology fixed against course materials, sentence-segmented, speaker/visual annotations |
| `audio` | "Make a podcast version / audio-only" | Podcast-style adaptation: visual content translated to narration or explicitly deferred, with chapter markers |

**Mode dispatch rule:** "record my Week N video" with no script source → check passport
artifacts for a lesson-builder `W<N>_preclass_spec.md` or `W<N>_lecture_notes.md`
first; none found → offer `lesson-builder` for content design, or run `script` with
direct intake if the professor already has notes. Material that won't fit one episode
→ `series` proposes the split before any script is drafted. Detect intent in any
language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Deciding WHAT the pre-class material should cover — the flipped design itself | `lesson-builder` (`flipped` mode) |
| The slides shown in the video — theme, rendering, figures | `deck-studio` |
| Lecture notes for a live class meeting | `lesson-builder` (`lecture-notes` mode) |
| Full design → materials → assessment run across stages | `teaching-pipeline` |

(The boundary in one line: lesson-builder specifies the material and writes the prose;
deck-studio renders what's on screen; this skill scripts what's *said* over it and
when. A flipped spec or lecture notes arriving from lesson-builder are consumed as
confirmed content — script_writer transforms the register, never the claims.)

## Agent Team (4)

| Agent | Role |
|-------|------|
| `script_writer_agent` | Transforms prose source into spoken-register two-column scripts: signposting, worked-example pacing, embedded retrieval prompts, timing from word count, `[VERIFY]` discipline on domain claims |
| `storyboard_agent` | Shot-by-shot plans: screen/narration/duration tables, screencast cursor-and-zoom discipline, demo error-recovery planning, talking-head alternation points, production-effort honesty |
| `segmenter_agent` | Topic → episode architecture: dependency ordering, one objective per episode, sizing from word counts, inter-episode retrieval questions, series map fed to the passport schedule |
| `transcript_editor_agent` | Raw auto-transcript → caption file + readable transcript: terminology corrected against course materials, caption line conventions, non-speech annotations, marked gaps over confident guesses |

## Workflow (`script` mode)

```
Phase 0  LOAD        — locate the source: lecture notes, slide outline, or flipped
                       spec from passport artifact_refs; else direct intake (the
                       professor's notes/outline + target audience + register sample
                       if available). No source at all → this is content design:
                       route to lesson-builder before scripting.
Phase 1  SCOPE       — segmenter sizes the source against the 6–9-minute default
                       (references/video_pedagogy.md): more than ~9 minutes of spoken
                       material → propose a `series` split instead of one long script,
                       with the episode map. One episode's worth → proceed.
         🧑 checkpoint: scope confirmed (single script vs series — cheapest moment
            to change the architecture)
Phase 2  DRAFT       — script_writer drafts the two-column script: spoken-register
                       narration, explicit signposting, one worked example per concept,
                       visual cue column synced to the narration, one embedded
                       retrieval prompt ("pause and predict…"), timing estimated from
                       word count (~130–150 wpm spoken) plus on-screen-action time.
                       The read-aloud test is part of this pass, not a later QA step.
Phase 3  STORYBOARD  — for visual-heavy segments (screencasts, demos, animated
                       figures), storyboard_agent expands the visual column into a
                       shot table with production notes; figure needs are written as
                       deck-studio specs, not vague gestures.
Phase 4  ASSEMBLE    — package: script + timing summary + recording checklist +
                       caption/transcript notes; collect every [VERIFY] marker
                       carried over from the source into one review list.
         🧑 checkpoint: script + timing + what the professor must verify before
            recording ([VERIFY] domain claims, register fit, example vetting).
            Confirmed → passport week artifact_refs updated.
```

`series` mode runs segmenter first and then this workflow per episode; checkpoint
cadence is per episode, collapsing to minimal confirmations when the professor says
"just proceed" (Checkpoint Protocol). `captions` and `audio` modes skip Phases 1–3
and run their single agent against the supplied recording artifacts.

## Iron rules

1. **Spoken register.** Scripts read aloud naturally — short sentences, direct
   address, no subordinate-clause stacks, no "as we can see." The read-aloud test is
   part of the draft pass, not a polish step; a paragraph the professor would stumble
   over on camera is a defect, not a style preference.
2. **Segment discipline.** Default 6–9 minutes per episode (Guo et al. 2014 — see
   `ts/media-scripter/references/video_pedagogy.md` for the honest scope of that evidence). Longer
   episodes only with the professor's logged reason. Every episode carries exactly one
   objective and at least one retrieval prompt.
3. **Narration–visual sync.** Every visual change has a narration anchor — the words
   during which it appears — and every narration beat that depends on a visual names
   it. Orphaned visuals (on screen, never referenced) and orphaned references ("this
   graph" with nothing scripted on screen) are defects caught at assembly.
4. **Accessibility is first-class, not retrofit** (Pedagogy Foundations §7). Narration
   describes visuals, never just points at them — "this graph" is banned; say what the
   graph shows. Caption-ready line lengths from the start; a transcript ships with
   every script. A video plan without its caption plan does not pass Phase 4.
5. **Content fidelity.** Scripts say what the source materials say — this skill adds
   register, structure, and pacing, not new domain claims. New examples invented for
   the recording are marked for professor vetting; uncertain domain claims carry
   `[VERIFY: <claim> — <why uncertain>]` inherited or added, and the package leads
   with the consolidated list.

## Outputs

- `media/W<N>_E<k>_script.md` — from `ts/media-scripter/templates/script_template.md`
- (`series` mode) `media/W<N>_series_map.md` — from `ts/media-scripter/templates/series_map_template.md`
- (`storyboard` mode) `media/W<N>_E<k>_storyboard.md` — shot table + production notes
- (`captions` mode) `media/<recording>_captions.srt` (or `.vtt`) + `media/<recording>_transcript.md`
- (`audio` mode) `media/<episode>_audio_script.md` — narration-only adaptation + chapter markers
- Updated `course_passport.yaml` week `artifact_refs[]` (after confirmation)

## References

- `ts/media-scripter/references/video_pedagogy.md` — the evidence base: Guo et al. 2014 with caveats,
  Mayer's principles operationalized, retrieval integration, production-value honesty,
  accessibility standards
- `ts/media-scripter/templates/script_template.md`
- `ts/media-scripter/templates/series_map_template.md`
- Shared: `ts/shared/pedagogy_foundations.md` (§5, §7, §9), `ts/shared/course_passport_schema.md`,
  `ts/shared/checkpoint_protocol.md`, `ts/shared/quality_gate_protocol.md`
