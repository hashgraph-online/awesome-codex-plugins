---
name: job-scan
description: "Find roles worth the candidate's time. Connected, uses TrueInterview's ranked recommendations and live job search across companies, screens the best in one call, and adds new postings from the candidate's own watch list of company job boards; local, scans the public Greenhouse, Lever, Ashby and SmartRecruiters boards in portals.yml and the web. Drops what was seen, tracked or skipped, then triages. Use for \"find me jobs\", \"anything new?\", \"scan\", or a daily or weekly check."
---

# Find roles

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

## Connected

1. `list_context_notes` once per session: targets, constraints, companies.
2. **Their board first**: `recommend_jobs` (ranked by fit to their résumé and saved search; pass the previous `checked_at` as `new_since` for "anything new?"). For a specific ask ("staff ML infra, remote US"), `search_jobs` with `query`, `location`, `seniority`, `work_mode`, `posted_within_days`.
3. **Their watch list too**: run `job-agent scan` if `portals.yml` has companies. It catches roles at the exact companies they named, the day they go up.
4. **Screen the shortlist**: `screen_jobs` with up to 10 ids and `match: true` gives facts, must-haves, fit and whether each is tracked in one call. For watch-list postings without an id, evaluate from the posting with `match_resume_to_job` (`job_description`).
5. **Show a short table**: company, role, place, fit, one-line keep/drop reason, link. At most 15 rows; say how many more.
6. **On their word**: `skip_job` for roles they rule out (with `why`, so similar ones stop showing up), `update_shortlist` with `action: "add"` for ones they want applied to (it puts them on their to-apply list; `track_application` with `status: "saved"` on an older server), and `job-evaluate` for the ones they want a full read on.
7. **Running unattended** (a scheduled run, or "find and apply"): use `job-run` instead. It reads their mode first: in `shortlist` mode your picks go on the to-apply list with a one-line note for them to approve.

## Local

1. Check `portals.yml` exists (else run the portals step of `job-setup`).
2. `job-agent scan` (flags: `--company <name>`, `--days <n>`, `--all`, `--json`, `--dry-run`). It prints a summary, appends new matches to `data/pipeline.md`, and remembers seen ids so the next scan shows only new ones.
3. A `404` means the board name is wrong or the company moved systems: find the careers page and fix `portals.yml`.
4. With a search tool, widen beyond the list on request. Dedupe against `job-agent track find`.
5. Quick triage (title, level, location, deal-breakers) in a short table; offer full `job-evaluate` on the keeps.
6. Keeps they want applied to: `job-agent list add --company … --role … --url …` (the candidate's own adds are approved; your picks take `--by agent --note "…"` and wait for `job-agent list approve`).

## Either way

- Never sign in to a job board or scrape a page behind a login.
- Suggest a rhythm once: two or three checks a week, evaluate keeps the same day. Postings get most of their attention in the first week.
