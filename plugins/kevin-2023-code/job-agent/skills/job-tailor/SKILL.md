---
name: job-tailor
description: "A résumé and, when wanted, a cover letter tailored to one posting, using only facts the candidate already has on record. Connected, uses TrueInterview's tailoring and cover-letter writer (checked for invented facts, returned as an upload-ready PDF) and keeps the saved résumé untouched; local, writes a tailored Markdown copy and renders it to PDF. Shows every change before use. Use for \"tailor my resume\", \"CV for this role\", \"write a cover letter\"."
---

# Tailor a résumé and cover letter

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

Start from the evaluation report in `reports/` if there is one; its "Angle for the CV" says what to lead with. If there isn't one and the role isn't obviously right, run `job-evaluate` first.

## Connected

1. **Both documents in one call** when a letter is wanted: `generate_application_documents` (`job_id`, or `job_description` + `company` + `role`; `instruction` for the letter, e.g. "lead with the Kafka migration"; `keywords` for posting terms they want surfaced; `intensity` from their saved `resume_tailoring`, default `rewrite`). Résumé only: `tailor_resume`. Letter only: `write_cover_letter`.
2. **Show the changes** it returns (moved, reworded, cut) and the quality check. If the check flags anything, say what.
3. **The file** is `resume_file` (a PDF link). Save a copy to `output/<company>-<role>/` if they want one locally.
4. **Their saved résumé is not changed.** If they want a fix to carry over to every future application, that's `update_resume` (show the section first) or, if they keep a local file, edit it and sync with `import_resume`.
5. These use the monthly writing allowance; mention `writing_allowance` when it is low.

## Local

1. Copy, don't edit: write `output/<company>-<role>/cv.md` from `profile/cv.md`. The master changes only on "update my master CV".
2. Lead with the two or three experiences from the report's angle. Cut what doesn't serve this role; tailoring is mostly subtraction.
3. Use the posting's words where they describe the same work truthfully. Rewrite the two-line summary for this role. Order skills by the posting's priorities.
4. No new employers, titles, dates, degrees, numbers or technologies. A missing must-have stays missing: say so, and suggest how to handle it in the letter or interview.
5. List the changes (moved / reworded old → new / cut) and wait for an OK.
6. `job-agent pdf output/<company>-<role>/cv.md` → `cv.pdf` next to it. One page under ~8 years of experience, two at most.
7. A letter (when `apply.cover_letter` is `always`, the form asks, or they ask): 200–300 words in `cover-letter.md`. A specific reason for this company; the one experience that best meets their biggest need, with the result; a gap handled honestly or a second proof point; a one-line close. No "I am writing to express my interest". Show it first.

## Language

The posting's language. If the source is in another language, translate faithfully and flag phrases whose meaning may have shifted.
