# ATS notes

What each common application system asks, and where people trip up.

## Greenhouse
- Form lives on the posting page (`boards.greenhouse.io/<board>/jobs/<id>` or the company's embedded careers page with `gh_jid=`).
- Standard fields: name, email, phone, location (often an autocomplete: type the city, pick from the list), résumé upload, cover letter upload or text, LinkedIn, website.
- Custom questions are common and often required: work authorization, sponsorship, "How did you hear about us?", salary expectation, start date.
- The voluntary self-identification block (EEOC, US) is at the bottom and optional.
- Résumé parsing is light; the PDF is what a human reads.

## Lever
- `jobs.lever.co/<board>/<id>/apply`.
- One page. Full name in a single field. "Current company" is asked. "Additional information" is a free-text box: a two- or three-sentence note here is read more often than people think.
- Links section lets you add several URLs.

## Ashby
- `jobs.ashbyhq.com/<board>/<id>/application`.
- Clean single page; résumé upload often autofills name and email (check them).
- Companies add many custom questions; long-answer fields usually have no visible limit, keep them under ~150 words anyway.

## SmartRecruiters
- `jobs.smartrecruiters.com/<board>/<id>`; the apply step may ask to create an account (that's the candidate's to do).
- Résumé parsing fills experience and education; check dates, they are often misparsed.

## Workday
- Always needs an account per company. The candidate creates it and signs in.
- Multi-page: "My Information", "My Experience" (parsed from the résumé, re-check every entry), "Application Questions", "Voluntary Disclosures", "Self Identify", "Review".
- Sessions time out. The answer sheet makes restarting quick.

## LinkedIn Easy Apply / Indeed Apply
- Stays on the board. Questions are short (years of experience with X, authorization, sponsorship). Answers come from the profile; years of experience must match the CV dates.
- Prefer the employer's own form when the role is also posted there: it usually lands with the recruiter more directly.

## Everywhere
- Name the PDF `Firstname-Lastname-Company.pdf`.
- Salary fields: if the candidate's `saved_answers.salary_expectation` is a sentence and the field wants a number, ask them.
- Years-of-experience questions: compute from the CV dates and say how you counted.
