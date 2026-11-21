---
name: friction-log
description: "Draft a short, honest account of where using Mycelium was confusing or slow, for the user to edit and choose whether to send. Reports experience; never prescribes fixes. Based on Hoskins's friction logging."
metadata:
  instruction_budget: "22"
  framework_dependency: "mycelium"
  framework_dependency_note: "Designed to run within the Mycelium framework (https://github.com/haabe/mycelium)."
---

# Friction Log

**What this is, in Hoskins's words:** *"A friction log is an informal document that you write as you
use a product. You report any confusion or roadblocks you experience. When you've finished, **you
hand it off** to the engineers or PMs responsible for the product."* Its purpose: *"we also need
outside perspectives. Since outsiders don't have all day, we need a lightweight option for them to
help out."*

**Mycelium has the opposite problem from most products: it can see its own friction and has no way to
send it back.** Measured 2026-09-20 in the dogfood repo: of 91 completed outreach tasks, ~71 were
outbound and ~4 inbound. The channel runs one way.

---

## THE ONE RULE THAT MAKES THIS WORK

**Report experience. Do not prescribe remedies.** Hoskins: *"See how I described my experience rather
than giving prescriptive advice? ... **My job as friction logger is just to call attention to the
problem.** If I just said 'you should put the icons into two rows,' they might feel like I'm trying
to do their job for them, decide on their roadmap for them, or they might **reject that specific idea
and not brainstorm other options**."*

**This is the mechanism, not a style preference.** A log that proposes fixes becomes a patch list,
and a patch list gets argued with instead of read. **If you catch yourself writing "you should", cut
the sentence and describe what happened instead.**

## WHY THE AGENT DRAFTS IT

Hoskins's design is built around the fact that outsiders will not spend long. **The agent was present
for the friction and can draft in seconds; the user edits and decides.** That removes the effort
barrier without removing the user's authorship.

**It also restores a separation the solo case loses.** The handoff exists to put the problem-finder
and the problem-solver in different hands. When one person is both, nothing stops them skipping the
description and going straight to the fix — which is what destroys the record. **An agent logger
cannot implement the remedy, so the separation holds.**

---

## STEP 1 — Draft, from what actually happened this session

Write 5–15 lines. Structure it as Hoskins does — persona, then the run:

1. **Who you are, for this log.** *"I'm an agent running Mycelium for a solo builder on a CLI tool,
   three sessions in."* State priors that colour the experience.
2. **What you were trying to do.**
3. **What happened, in order** — including the parts that worked. *"I glossed over some of the flows
   that worked well, but I did sprinkle in some praise."* A log of only complaints is not credible.
4. **Where it was confusing or slow.** Name the skill, the file, the message.

**Include the friction you caused as well as the friction you hit.** If a gate fired and you did not
understand why, that is the log's best material.

## STEP 2 — Add the questions that work at any sample size

These are Ellis's, from `Hacking Growth`. **They are qualitative and need no threshold**, which
matters because his 40% benchmark requires a real sample and most projects do not have one yet.

- *What would you likely use as an alternative to Mycelium if it were no longer available?*
- *What is the primary benefit you have received from it?*
- **Have you recommended it to anyone? If so, how did you describe it?**
- *What type of person do you think would benefit most?*
- *How could it better meet your needs?*

> **The third question is the load-bearing one.** It tests whether someone who likes the framework
> can say what it is — which is the difference between a product problem and a positioning problem.
> Ellis puts that distinction in the 25–40% band: what is needed is *"tweaks either to the product
> **or to the language used to describe the product**."*

**Do NOT compute a percentage or report a PMF score.** Ellis's threshold needs a sample; over a
handful of users a percentage is not a percentage.

## STEP 3 — Hand it over, and only if the user says so

**Show the draft. Say plainly where it would go. Ask.** Then:

- **User edits freely.** It is their account, not yours.
- **Nothing is sent without an explicit yes.** No automatic transmission, no background collection,
  no "I'll include this next time".
- **A no is a complete answer** and is not asked again this session.

**Save it either way** to `.claude/evals/friction-logs/<date>.md`. A log the user keeps privately
still has value to them; the handoff is the part that needs consent.

---

## WHEN TO OFFER THIS

**At a natural pause, not on a schedule, and not every session.** Good moments: after a first run
completes; after a gate blocked something and the user worked around it; after a session where the
user said something was confusing.

**An agent cannot detect the end of a session** — a session can run for days — so do not key this to
one. Key it to a *completed piece of work*.

**Offer at most once per session, and never twice for the same friction.**

---

## WHAT THIS IS NOT

- **Not `corrections.md`.** That records build-time mistakes and is read by its author. This records
  use-time friction and is handed to someone else. *(The corrections register described itself as a
  friction log until 2026-09-20; it is a different object and the chapter reference was right.)*
- **Not telemetry.** The agent already observed everything here; the only question is whether the
  person chooses to hand it over.
- **Not a survey with a score.** See step 2.

*Sources: Drew Hoskins, `The Product-Minded Engineer`, ch. 4 (friction logging). Sean Ellis &
Morgan Brown, `Hacking Growth` (the Must-Have Survey's qualitative follow-ups).*
