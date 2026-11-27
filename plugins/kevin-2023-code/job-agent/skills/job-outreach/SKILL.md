---
name: job-outreach
description: "Find the right people at a company (recruiter, hiring manager, someone on the team, an alum) and draft a short, specific note the candidate sends themselves, for a referral or a question. Connected, uses the candidate's TrueInterview contacts and its public-profile people search; local, works from their own network notes in knowledge/. Use for \"who can I talk to at…?\", \"can I get a referral at…?\", \"write a note to the recruiter\", \"message the hiring manager\"."
---

# Outreach

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

A referred application gets read far more often than a cold one. Most people skip it because finding the person and writing the note is awkward. You do both; the candidate sends.

## Who

- **Their own network first**: `job-agent kb search "<company>"` — former colleagues, classmates, people they noted.
- **Connected**: `list_contacts` with `company` (free: people already found or saved). Only if that's thin and they ask, `find_contacts` with `company`, `role` and the `application_id` if tracked (spends their AI allowance; once per company). Results are search hits: they open each profile and confirm the person and current job before writing.
- **Local, with a search tool**: the company's team pages and public profiles. No guessing at emails or phone numbers, ever, in either mode.

Pick two or three, with a one-line reason each (same school, same team as the role, recruiter for that org).

## The note

Under 90 words. Specific: who they are, the role (with the link or id), one concrete reason they fit, one small ask ("would you be open to referring me?" or "is the team hiring for X?"). No flattery, no attached résumé in a first message. Offer one variant for LinkedIn (≤300 characters for a connection request) and one for email if they have the address themselves.

## After

- They send it, from their own account. You never message anyone.
- Connected: `update_contact` with `status: "contacted"` once they say they wrote, and a `note`. A referral given → `track_application` with `status: "referral_sent"`, `channel: "referral"`.
- Local: `job-agent track note <id> "Messaged <name> (<role>) on <date>"`.
- Follow up once after five to seven business days if no reply. Then let it go.
