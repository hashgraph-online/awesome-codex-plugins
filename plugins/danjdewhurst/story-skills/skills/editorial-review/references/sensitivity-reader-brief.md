# Sensitivity and Authenticity Readers

A sensitivity or authenticity reader is someone with lived or
professional experience of what the book portrays, paid to read for
inaccuracy, stereotype, and harm the author cannot see from outside.
Sources and research notes (the `research` skill) cannot replace them.

## When to suggest one

- A POV or major character's identity, culture, faith, disability,
  illness, sexuality, or gender is one the author does not share
- A setting, community, or historical trauma the author knows only from
  reading
- A trade, institution, or experience the plot depends on (policing,
  nursing, prison, the military, addiction, immigration)
- Portrayals of violence, abuse, or self-harm aimed at younger readers

One reader speaks for their own experience, not a whole community. For a
central portrayal, two readers with different perspectives are better
than one. An expert reader (a paramedic, a lawyer) checks technical
accuracy; record them with `method: expert-review` on the research note.

## Finding and paying readers

- Search for professional sensitivity-reading services, editor
  directories, and writing organisations for the relevant community.
  Only name specific services the user or a verified search supplies.
- Ask for the reader's rates, turnaround, and sample report. Fees are
  commonly quoted per manuscript, per word, or per hour; help the user
  budget from the reader's own quote, not a remembered figure.
- Pay readers. Never suggest asking friends from a community, online
  groups, or strangers to do this work for free.
- Agree in advance whether the reader wants to be credited (in
  acknowledgments and in `reviewed-by`) or kept anonymous.

## Brief template

Save as `feedback/briefs/{reader-kebab}.md` or send as the body of the
user's email. Keep briefs out of the `feedback/round-{N}/` folders, which
hold only reader feedback files and the synthesis.

```markdown
# Reading brief: {Title}

**Book:** {genre, category (adult/YA/MG), form, word count}
**Logline:** {one sentence}
**What you are receiving:** {chapters or full manuscript; format: DOCX / HTML review copy}
**Deadline:** {date}
**Fee:** {agreed fee and payment terms}

## Why I am asking you
{The portrayal in question and why the author is outside it.}

## Characters and places to focus on
- {Character}: {role, how much page time, chapters}
- {Setting}: {chapters}

## Specific questions
1. {Does the family's Eid in chapter 6 ring true for a Glasgow Pakistani household in 1998?}
2. {Is the hearing character's reaction to BSL in chapter 4 plausible, or does it centre the wrong person?}
3. Anything else that pulled you out of the story or felt harmful.

## What I have researched
{Sources and research notes the portrayal relies on; decisions already made and why.}

## How to send notes
{Comments in the DOCX, or notes citing paragraph anchors like ch04-p12, plus a summary letter.}

## Credit
{Would you like to be named in the acknowledgments? Yes / no / role only.}
```

Specific questions get better notes than "is this okay?". Include what
the author is most worried about.

## Incorporating notes

1. Record the notes as a reader file in `feedback/round-{N}/` with
   `feedback-template.md` from the `feedback-triage` skill; quote the
   reader, do not paraphrase their judgement away.
2. Synthesise through `feedback-triage`. Sensitivity notes carry the
   reader's expertise: decline one only with a recorded reason the author
   can defend, and never dismiss a note because it is inconvenient.
3. Hand accepted changes to `revision-continuity` (events, character
   facts) or `line-editing` (wording).
4. When incorporated, add the reader to each relevant research note's
   `reviewed-by` (name with consent, or role) and set `status: verified`
   if the note's findings now rest on sources and the review.
5. Run `story validate .`: notes with a `risk` used in final chapters and
   no `reviewed-by` are warned.

A read is not a certificate. Tell the user that it lowers the chance of
harm and error; it does not guarantee a reception.
