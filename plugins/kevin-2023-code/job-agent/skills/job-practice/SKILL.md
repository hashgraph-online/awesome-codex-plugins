---
name: job-practice
description: "Practise for technical interviews every day: picks what to solve next (due revision, the companies in the candidate's pipeline, their weakest topics), by company, type (algorithm, system design, OOP, SQL, AI coding) or difficulty, with practice links into TrueInterview's question bank when connected; coaches without giving answers away, runs timed mock coding and design rounds, reviews their solution, and keeps a log of what they got wrong so the next session targets it. Use for \"give me a problem\", \"what should I practise?\", \"daily practice\", \"drill me on graphs\", \"practise Stripe questions\", \"review my solution\", \"mock coding round\"."
---

# Practice

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

The aim is steady, targeted practice: a little every day on what they're weakest at and what their next interviews ask, not random problems.

## 1. What to practise

- **Connected**:
  - `get_prep_plan` — the next items in order: due revision, prep for employers in their pipeline, weak-topic practice. With `company`, that employer's picks first. Each has a link and a reason.
  - `search_questions` — by `company`, `type` (`algorithm`, `system-design`, `object-oriented-programming`, `sql`, `ai-coding`), `difficulty`, or `query` ("sliding window", "rate limiter"). `locked: true` means their plan can't open the full text.
  - `get_my_progress` — solved count, mastery, weakest measured topics, recent review scores, and per active application how much of that company's list is done.
  - `search_site_content` with `kinds: ["lesson", "article"]` — the lesson or guide for a topic they keep missing.
  - `get_company_intel` — the topic mix and recently reported questions for a company.
- **Local**: their practice log (`knowledge/practice/log.md`), mock feedback in `knowledge/mocks/`, interview notes, and the tracker for upcoming interviews. Pick the weakest topic that their next interview is likely to test.

Offer three to five items with one line each on why, sized to the time they have today.

## 2. Solving

- **A TrueInterview question**: the tools return titles and links, never the statement or solution. Send them the link to solve it on the site (the editor, tests and AI review are there). Coach in chat if they paste their approach or code: hints, not answers.
- **A problem you set** (local mode, or when they want one in chat): write an original problem at the right level for the topic, with examples and constraints. Don't reproduce a company's question from memory.
- **Coaching rules**: ask for their approach before any code; give hints in steps (a nudge, then the pattern, then the key insight), never the full solution unless they ask after a real attempt. When they finish: correctness, complexity, edge cases they missed, and a cleaner version only if it teaches something.
- **Review my solution**: read their code like an interviewer: does it work, complexity, edge cases, naming and structure, what an interviewer would push on next.

## 3. Mock rounds

Timed, one at a time, in chat:
- **Coding (45 min)**: a problem at their level from the target company's reported topics (connected: from `get_company_intel` / `search_questions` topics; the problem itself is yours). Let them think aloud; ask follow-ups on complexity and variations.
- **System design (45–60 min)**: a prompt matching the level; push on requirements, estimates, data model, scaling, failure modes and trade-offs.
- **OOP / low-level design, SQL, AI coding**: the same, for that format.
End each with what worked, the two fixes that matter most, and a hire / no-hire read with the reason. Honest beats encouraging.

## 4. Keep score

After each session, append to `knowledge/practice/log.md`: date, items, outcome (solved / hint / stuck), the mistake pattern in a few words ("off-by-one in window shrink", "forgot capacity estimate"). Save mock feedback to `knowledge/mocks/<yyyymmdd>-<topic>.md`. Connected, progress on site items is recorded by the site itself; `get_my_progress` shows it.

Start the next session from the log and `get_my_progress`: repeat the patterns they got wrong until they stop getting them wrong.

## Rhythm

If they ask for a routine: 45–90 minutes a day; one revision item, one or two new items on the weakest topic, and one item for the nearest interview. A mock round every few days once an interview is booked.
