---
name: job-run
description: "Run the candidate's job search end to end, the way they set it up: find new roles, pick the ones that fit, put picks on their to-apply list or apply to them on the company site with the right résumé, log every application and every role it couldn't do, stop at their daily cap, and send a short summary. Follows their mode (finds and applies / picks for approval / only the roles they add), who sends (their agent or them), minimum match score and applications per day, read fresh from their TrueInterview account each run (or profile.yml locally). Use for \"run my job search\", a scheduled daily run, \"work my list\", or \"apply to the roles on my list\"."
---

# Run the job search

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

One run, start to finish. Scheduled runs and "run it now" follow the same steps.

## 1. Read the settings, fresh, every run

The candidate can change them any time, so never go by an older message, including the one that set up this schedule.

- **Connected:** `get_shortlist`. Its `settings` hold `agent_mode`, `apply_by`, `min_match_score`, `max_applications_per_day` and `applications_today`; `items` is the to-apply list with each row's `approved` state. Also `get_account` once per session.
- **Connected, but `get_shortlist` isn't in your tool list** (an older server): use the defaults below and keep the list in `data/apply-list.tsv` (`job-agent list`).
- **Local:** the `agent:` block in `profile/profile.yml` (`mode`, `apply_by`, `min_match_score`, `max_applications_per_day`), and `job-agent list` for the to-apply list.

| Setting | Values | Default when unset |
| --- | --- | --- |
| `agent_mode` | `auto` (find and apply), `shortlist` (find, add picks, apply only to approved ones), `list_only` (no search; only roles the candidate added) | `shortlist` |
| `apply_by` | `agent` (you submit), `me` (you prepare everything; they submit) | `me` |
| `min_match_score` | 0–100, or none | none |
| `max_applications_per_day` | 1–20, or none | none |

On a **scheduled** run in `list_only`, do nothing else: tell the candidate this mode doesn't need the schedule and they can delete it (or switch modes), then stop.

## 2. Résumés

Connected: `get_resume` (and a résumé list, if the server offers one). Local: `profile/cv.md`, plus any files in `profile/resumes/`, each with a `kind:` line at the top (for example `kind: data engineering` or `kind: 中文`). With more than one, pick per role: the posting's language, the kind of role, what it stresses. Use that one résumé for the role from here on: fit, answers and the file you attach.

## 3. Find roles (`auto` and `shortlist` only)

- Connected: `recommend_jobs` (on a scheduled run, pass the previous run's `checked_at` as `new_since`), and `job-agent scan` for companies in `portals.yml`.
- Local: `job-agent scan`.
- Leave out what is already tracked, already on the list, or was skipped in the last 7 days.

## 4. Decide fit

Read each posting against the chosen résumé and the candidate's targets and deal-breakers.
- `min_match_score` set: only roles whose match (`match_resume_to_job` / `screen_jobs`, or `docs/scoring.md` locally) reaches it.
- Not set: judge it yourself; use a match check only when unsure.
- Every role you look at and pass on: `skip_job` with the reason (connected) so the next run doesn't look again.

## 5. Act by mode

- **`shortlist`:** add each pick with a one-line note in the candidate's language (what fits, any risk): `update_shortlist` with `action: "add"` (connected) or `job-agent list add --by agent --note "…"`. The server refuses past 40 picks waiting or past the daily cap; stop adding when it does. Then apply only to rows that are `approved`.
- **`list_only`:** only the list's rows (all of them were added or approved by the candidate). Don't search.
- **`auto`:** apply to every role that passed step 4.

## 6. Apply, one role at a time

Follow `job-apply` for each role, with the résumé from step 2.
- `apply_by: agent`: fill the form and press Submit yourself once every required field has an honest answer. Required fields only; an optional question nobody told you the answer to can stay empty. For a required question with no answer on file, pick the neutral option the form offers (for example "Prefer not to say" or "N/A") rather than drop the role; never state a fact about the candidate that isn't on record.
- `apply_by: me`: get the role ready (résumé file, every answer, the link) and hand it over; don't submit.
- A sign-in, account creation, email code or CAPTCHA: you don't do these. Ask the candidate to take over, then carry on; if they don't answer, mark the role as could-not-apply with kind `sign_in` and move on.
- After each submission: `report_application` with `submitted: true` (connected; its answer says when the daily cap is reached), or `job-agent track add … --status applied` and `job-agent list done <id>` locally. Stop applying when `max_applications_per_day` is reached.

## 7. Roles you couldn't apply to

Mark them, with a kind and a short reason: `update_shortlist` with `action: "could_not_apply"` and a note that starts with the kind (connected), or `job-agent list skip <id> --kind <kind> --note "…"`. Kinds: `sign_in`, `not_a_fit`, `required_question`, `closed`, `other`.

## 8. Summary

End every run with a short message in the candidate's language: applied (role, company), prepared for them to send, picks waiting for approval, could not apply and why, how many applications are left today, and anything they should look at (a tailored résumé, an answer you chose for them). Under ten lines.
