---
name: job-sync
description: "Upload the candidate's changes to their TrueInterview account so every agent, the website and the next application form see them: an edited résumé file, new or changed job-search preferences, form answers, goals and deal-breakers, and tracker updates. Finds what changed locally with job-agent changed, uploads with the matching tool, and reports what was saved. Use for \"sync my profile\", \"I updated my resume\", \"I changed my mind about…\", \"update my preferences\", or when job-agent changed lists files."
---

# Sync to TrueInterview

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

Every other skill already uploads its own changes as its last step. This one is for catching up: after the candidate edits files by hand, says something new, or asks for a sync.

## Steps

1. **Connected?** `get_account`. Not signed in → the one sign-in step for their agent, then continue. Local mode by choice (`apply.data_source: local`) → nothing to upload; say so.
2. **What changed locally**: `job-agent changed`.
   - `profile/cv.md` → `import_resume` with the whole file text. Show the few lines that changed in the parse.
   - `profile/profile.yml` → map it:
     - `targets.roles`, `targets.level`, `location_prefs`, `compensation` → `update_job_search`
     - `work_authorization`, `links`, `phone`, `location`, `saved_answers`, `apply.cover_letter`, `apply.voluntary_disclosures` → `update_application_answers` (fields it doesn't have stay local)
     - `targets.why`, `deal_breakers`, `targets.industries`, `company_stage` → `save_context_note` with the right topic, unless an identical note exists (`list_context_notes`)
   - Then `job-agent changed --mark`.
3. **What they said in this conversation** that isn't saved yet (a new deal-breaker, a different salary floor, a new target company, a start date): save it with the tool from the table in `AGENTS.md`.
4. **Tracker**: if the local tracker (`job-agent track list`) has rows the account lacks (`list_applications`), add them with `track_application` (company, role, status, `applied_at`, `channel`, note). Ask once before bulk-adding more than ten.
5. **Report** in a short list: what was uploaded, and anything left local (stories, knowledge, reports never upload).

## Never upload

Self-identification answers, ID or card numbers, passwords or tokens, `knowledge/` files, interview notes, or anything about another person.
