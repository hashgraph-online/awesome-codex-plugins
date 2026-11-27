---
name: job-prep
description: "Prepare the candidate for a specific interview. Connected, pulls the company's real interview record from TrueInterview (process, rounds, topic mix, recently reported questions with practice links), a prioritized practice plan from their own weak spots, and interview write-ups; local, works from their knowledge/ folder and the web. Builds a day-by-day plan to the date, maps their stories to likely behavioral questions, and runs mock rounds with honest feedback. Use for \"I have an interview with…\", \"prep me for the onsite\", \"mock me\", \"what will they ask?\"."
---

# Interview prep

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

## 1. Pin it down

Company, role, level, round(s), date, hours per day they have. Read the tracker row (connected: `list_applications`; local: `job-agent track find`) and the evaluation report if any.

## 2. What is known

Track the source of every fact.

- **Their own notes first**: `job-agent kb search "<company>"`: past loops, recruiter emails describing the rounds, friends' notes.
- **Connected**:
  - `get_company_intel` — the process, rounds, topic mix, how reported loops went, and recently reported questions with links.
  - `get_prep_plan` with `company` — what to practise next, in order, from their own record and what the company asks most.
  - `search_questions` with `company` (and `type`: algorithm, system-design, object-oriented-programming, sql, ai-coding) for more by round type.
  - `search_site_content` with `company`, `kinds: ["interview", "article"]` for interview write-ups and guides.
  - `get_my_progress` — their weakest measured topics.
  Pass links on unchanged; practice happens on the site through them. The tools give titles and links, not question text.
- **Web**, if available: the company's own pages on its process.

If sources disagree, say so. If a round is unknown, say that and prepare the common format for that round type.

## 3. The plan

Write `output/<company>-<role>/prep.md`:
- The loop round by round: format, length, what's assessed, source.
- Per round, the most likely question types, their weak spots first.
- A day-by-day schedule to the date, sized to their hours. Most time on the highest-weight round they're weakest at. Connected, each day links the specific practice items from `get_prep_plan`.
- Story map: likely behavioral question → story from `profile/stories.md`. Flag gaps and help draft a story from real experience.
- Three questions for them to ask the interviewers.

## Daily practice

The plan's practice days run through `job-practice`: it picks the next problems (from `get_prep_plan` for this company when connected), runs them, and logs results.

## 4. Mock rounds

On request, play the interviewer for one round type at a time.
- **Coding**: a problem at the right level (connected: pick from the company's reported topics); let them think aloud; probe complexity and edge cases; never hand over the answer.
- **System design**: push on requirements, scale, trade-offs and failure modes.
- **Behavioral**: ask, then probe ("what did *you* do?", "what would you change?").
- End each: what worked, the two most important fixes, a hire/no-hire read with the reason. Honest beats encouraging. Save to `knowledge/mocks/<yyyymmdd>-<company>-<round>.md`.

## 5. After the interview

- Offer to write up what was asked into `knowledge/interviews/` — the most useful file they'll have for the next loop.
- Update the tracker (`update_application` with the next `interview_round` / `next_interview_date`, or `job-agent track set`), and draft the thank-you note for them to send.
