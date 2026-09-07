---
name: story-mine
description: "Turn a real experience — a client win, failed launch, support ticket, founder moment — into 3-5 distinct content angles from a five-type taxonomy (lesson, contrarian take, framework, proof, relatable moment), each with format, pillar, and a draft opening in brand voice, plus an honest list of angles the story does not support. Triggers on \"/digital-marketing-pro:story-mine\", \"mine this story\", \"we just had a client win\", \"is there a post in this\", \"turn this experience into content\". Client stories anonymise by default (--client-safe); reads the brand profile for voice, pillars, and compliance; angles route to /digital-marketing-pro:content-engine for drafting and strong proof angles to /digital-marketing-pro:case-study-plan."
argument-hint: "[brand-name] [--story <what happened>] [--client-safe]"
user-invocable: true
---

# /digital-marketing-pro:story-mine

Lived experience is the one content source competitors cannot copy, and most of
it evaporates in Slack. This skill takes "here's what happened" and returns the
distinct publishable angles hiding inside it — because a real story rarely
contains one piece of content; it usually contains four.

## Inputs

- **The story** — told naturally, as the user would tell a colleague. Do not
  demand structure; extracting the structure is this skill's job.
- **The brand profile** (`~/.claude-marketing/brands/{slug}/`) — voice,
  audience, pillars, and compliance rules the angles must respect.
- `--client-safe` — anonymise before angling: no client names, no identifying
  details, figures rounded or expressed as ratios. **Default ON whenever the
  story involves a client** — the user opts into naming, never out of it.

## The angle taxonomy

Work through all five; return the 3-5 that genuinely hold:

| Angle | The question it answers | Typical format |
|---|---|---|
| **The lesson** | What do we know now that we didn't before? | LinkedIn post, newsletter section |
| **The contrarian take** | What common belief did this contradict? | Short post, thread |
| **The framework** | What repeatable method fell out of it? | Carousel, long-form section |
| **The proof** | What number or before/after does this demonstrate? | Case-study seed, stat post |
| **The relatable moment** | Where will the audience see themselves? | Story-format post |

## Output structure

```
# Story mine — [one-line story summary]

## Angle 1: [name] — [taxonomy type]
**The angle:** [2-3 sentences — what this piece argues]
**Format + channel:** [e.g. LinkedIn text post / newsletter lead / carousel]
**Pillar:** [which brand pillar it serves]
**Draft opening:** [2-3 sentences, in brand voice, leading with the most
interesting part — not "We recently worked with a client..."]

[... angles 2-N ...]

## Not worth angling
[What the story does NOT support — e.g. "no proof angle: the numbers aren't
final yet". Naming the missing angle stops it being invented later.]

## Case-study check
[If the proof angle is strong: flag it for /digital-marketing-pro:case-study-plan
— this story may be a full case study, and these angles become its promotion.]
```

## Critical rules

- **Angles must be distinct, not the same insight in five outfits.** If the
  story only holds two genuine angles, return two and say so.
- **Never fabricate story details.** The angles dramatise what happened; they
  do not improve on it. Missing details are asked for or worked around — a
  invented specific in a true story poisons the whole piece. Client-data
  provenance rules from case-study work apply here in full.
- **Every draft opening leads with the interesting part** — the surprise, the
  number, the reversal — never with the chronology ("It started when...").
- **Respect compliance.** A regulated brand's story angles pass the same
  guardrails as any other content; a HIPAA-adjacent client anecdote may have
  no publishable angle at all, and saying that is the correct output.
- **Route onward, don't duplicate.** Angles feed /digital-marketing-pro:content-engine
  for drafting; a strong proof angle feeds case-study-plan. This skill finds
  the angles; it does not write the pieces.
