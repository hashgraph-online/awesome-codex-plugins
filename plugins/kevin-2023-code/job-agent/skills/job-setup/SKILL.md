---
name: job-setup
description: "First-run onboarding for job-agent, right after install. Signs the candidate in to TrueInterview (the default; no question asked), then configures their account in one pass: imports the résumé, saves the job search (roles, level, places, work mode, salary), every application-form answer (work authorization, sponsorship, address, links, start date, notice, salary, self-ID handling, cover-letter and tailoring preferences) and their goals and deal-breakers as notes, so the first application form is already answered. Also drafts STAR stories and the companies to watch. Local workspace only if they say they want their own data. Use for \"set me up\", \"start\", a first résumé, or whenever the account has no résumé or job search yet."
---

# Setup

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

Goal: in one sitting, the candidate's TrueInterview account holds everything an application needs, so later they only pick roles and press Submit. Ask as few questions as possible, all at once, and save their answers as part of setup (their agent may ask them to approve each write; that's expected).

## 1. Sign in (default; don't ask whether)

- `get_account`. Signed in → step 2.
- Not signed in → give the one step for their agent (see `AGENTS.md`), say a new user creates a free account on that same page, and wait for "done". Then `get_account` again.
- A code starting with `tih_` (from TrueInterview's Agent page) → `claim_setup_handoff` and follow its instructions, reporting stages with `report_setup_progress`. Keep the codes out of what you write back.
- Only if they say they want to use their own data and not TrueInterview: local mode. Run `job-agent init`, set `apply.data_source: local` in `profile/profile.yml`, and do steps 2–6 into `profile/` instead of the tools.

Run `job-agent init` in both modes: the local workspace holds `knowledge/`, `portals.yml`, reports and output either way.

## 2. Read everything first

Before any question, collect what already exists:
- `get_account` (`profile.next_in_chat` says what's missing), `get_application_checklist` (`setup.missing` with the exact questions and options, `setup.prefill` with what the résumé already says), `get_resume`, `list_context_notes`, `list_my_conversations` (what they told the site's Co-pilot).
- Local: `profile/cv.md` and `profile/profile.yml` if they're not the example person, any résumé file they point to, `knowledge/` (brag docs, reviews, recruiter emails), `job-agent changed`.

## 3. Résumé

- A résumé file they point to, or a real `profile/cv.md` → `import_resume` with its full text. It returns the parsed résumé, a PDF link and often `suggested_search`.
- None anywhere → ask for one (PDF, Word, pasted text, or a LinkedIn "Save to PDF"), then import it.
- Show the parse in three or four lines; fix what they correct with `update_resume`.
- `job-agent changed --mark cv` after an upload from `profile/cv.md`.

## 4. One message of questions

Build one numbered message from what step 2 couldn't settle, phrasing each prefilled item as a yes ("Your résumé says Seattle, WA. Is that where you live?"):
- `setup.missing` items, word for word with their options (work authorization and sponsorship per country, address, phone, start date or notice period, relocation, in-person, salary range).
- Target roles and level, places and remote/hybrid/on-site, if `suggested_search` didn't settle them (offer it as a yes).
- Deal-breakers, and why they're looking (one line).
- Preferences, each with the default in brackets: tailor the résumé per job [keywords], cover letters [when the form asks], self-identification questions [ask me each time / always decline], review the first tailored résumé [yes].
Leave out anything already known.

## 5. Save everything in one pass

- `update_job_search`: roles (main first), seniority, places, work mode, salary range.
- `update_application_answers`: every form answer they gave, plus `resume_tailoring`, `cover_letter`, `voluntary_disclosures`, `review_first_resume`. `answer_mode: full_auto` only if they agree to the sentence `prepare_application` gives for it, read word for word.
- `save_context_note`: goals and the why (`goals`), target companies (`target_companies`), deal-breakers and constraints (`constraints`), other preferences (`preferences`), in their words.
- Then `get_application_checklist` once more: `setup.complete` should be true. Ask anything still missing.
- Tell them in a short list what is now on their account.
- If they keep a local `profile/profile.yml`, update it to match and run `job-agent changed --mark`.

## 6. Stories and companies to watch

- Draft three to five STAR stories in `profile/stories.md` from the résumé and `knowledge/` (hard technical problem, conflict, failure, leading without authority, deadline), tagged and marked `DRAFT`; ask them to fix facts later, not now.
- Companies they named → `portals.yml` entries where the company uses Greenhouse, Lever, Ashby or SmartRecruiters, with title and location filters from step 4, so `job-agent scan` catches new postings the day they appear.

## 7. How their agent works

Ask once, with the default in brackets, and save it (connected: on TrueInterview at https://trueinterview.io/agent/start, where they choose it themselves; local: the `agent:` block in `profile/profile.yml`):
- Mode [pick for my approval]: find and apply on its own (`auto`), find and add picks for me to approve (`shortlist`), or only the roles I add (`list_only`).
- Who sends [me]: my agent submits (`agent`) or I press Submit (`me`).
- Minimum match score [none] and applications per day [none].

On a chat or desktop agent (Muse, Manus, Grok, Qwen, WorkBuddy), `job-agent agent <id>` prints the setup message that teaches it the rules and the run, with a daily schedule.

## 8. First results

`recommend_jobs` and show the top five in a short table (company, role, place, fit). Offer: evaluate one, apply to one, or start practice for a company (`job-practice`). Mention `knowledge/` in one line: past interview notes and brag docs there make every answer better.
