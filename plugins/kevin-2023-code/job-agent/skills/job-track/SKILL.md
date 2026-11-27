---
name: job-track
description: "Keep the application tracker current and the search honest. Connected, updates the TrueInterview tracker (statuses, interview rounds and dates, notes) so it shows up on the candidate's board and drives their prep plan; local, keeps data/applications.tsv through job-agent track. Surfaces follow-ups that are due, drafts them, and gives a weekly readout from real numbers. Use for \"I heard back from…\", \"I have an interview with…\", \"rejected by…\", \"where do I stand?\", \"what should I follow up on?\"."
---

# Track applications

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

Change a row only on the candidate's word. If an email or message suggests a change ("looks like a rejection"), ask before moving it.

## Connected

- **Find the row**: `list_applications` (filter by `status`; paged, newest first, with counts per status).
- **New row**: `track_application` with `company` + `role` (or `job_id`), `status` (`saved`, `prepared`, `applied`, `referral_sent`, `oa`, `interview`, `offer`, `rejected`), `channel` (e.g. "referral"), `applied_at`, `note`. Safe to repeat; never moves backwards on its own.
- **Change a row**: `update_application` with `application_id`: `status` (any direction, on their word), `interview_round` (1–5), `next_interview_date`, `note` (who, what was said, range, next step).
- An `oa` or `interview` → offer `job-prep` right away; the update's answer points at prep for that employer. An `offer` → offer to compare with their target comp and others in play.
- A rejection → set it, note the stage, and say nothing more unless they want to talk about it.

## Local

```bash
job-agent track list [--status applied] [--company stripe]
job-agent track find "<text>"
job-agent track add --company "Stripe" --role "Backend Engineer" --url "<u>" --status applied --grade B
job-agent track set <id> --status interview --next "onsite prep" --next-date 2026-12-03
job-agent track note <id> "Recruiter: 190–230 base, Payments Infra"
job-agent track due
job-agent track stats
```

Statuses: `evaluated`, `applied`, `screen`, `interview`, `offer`, `rejected`, `withdrawn`, `skipped`, `ghosted`.

## Both

- **Recruiter emails**: if they paste one, offer to file it in `knowledge/` (it often states the level, range and loop, which prep will use).
- **Follow-ups**: every active application gets a next step. After applying, check in after 7–10 days; after an interview, a thank-you the same day and a follow-up two business days past the stated timeline. Draft each message for them to send; you never send it.
- **Weekly readout** (six lines at most): applications this week and active pipeline; reply rate and where things stall; one pattern worth acting on if the numbers show one (grade or channel vs. outcome; referrals usually win); next week's plan in one line. Connected, add `get_my_progress` for practice against the companies in play. Under ~15 applications, say the sample is too small to read much into.
