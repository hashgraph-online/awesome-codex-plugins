---
name: metis-check
description: Use when the user asks to check or verify a citation, DOI, identifier, reference list, case citation, company or registry id, or whether a cited source exists. Metis Check settles each identifier at the body that issues it and files a report.
---

# Metis Check

Metis Check asks the registry that issues an identifier whether it exists and what it points to. It answers with exactly one of four states per identifier and files a report. It checks the checkable parts of a text at the source; it does not grade a text true or false.

## Picking the tool

- **One identifier** (a DOI, PubMed ID, arXiv id, ORCID, ROR, ISBN, LEI, ISIN, CUSIP, SEC CIK, EIN, NPI, RxCUI, PubChem CID, OpenAlex id, Wikidata item, UK company number, FAA N-number, USGS event id, domain name or U.S. case citation): `check_identifier`. Pass `type` when the shape alone does not say what it is (a bare number could be a PubMed ID, an NPI, a CIK or a CUSIP; ask the user which if the context does not say). A DOI, ORCID, LEI, ISIN or registry URL is unambiguous on its own. Pass `name` when the user says who or what the identifier belongs to; the registry's registered name is compared and a mismatch comes back as needs a person.
- **A passage the user pasted or pointed at** (a paragraph, a reference list, an abstract, one earlier answer): `check_text` with that passage only, exactly as written. Not the whole conversation, not several turns stitched together, not a paraphrase. If the user asks to check "everything" or "the whole chat", ask which passage to check and run that one.
- **A report id** (MC-XXXX-XXXX-XXXX): `get_report`. It runs no new check.

## Presenting a result

- Lead with `explanation.headline`.
- List each item with its state in Metis's words, then the registry:
  - `settled_true`: **settled true**
  - `settled_false`: **settled false**
  - `not_decidable`: **needs a person**
  - `unreachable`: **unreachable** (a delay, not evidence; the recheck button asks again)
  - `not_checked`: **not checked**, with the reason from `why`
- Say what was not checked and why (`not_checked_reasons`). A report with nothing not checked says so in one line.
- Give `report_url` and `pdf_url`. Mention that anyone with the link can recheck the report against the registries; a recheck is filed as a new report linked to the first.
- For a case citation, add that CourtListener is a citation index, not the court that issued the decision.
- Keep to the four states and nothing stronger. The result is about the identifiers, not the argument around them: a settled-true DOI says the paper exists at Crossref as stated, not that the claim it supports holds. No claim that a source was invented, that the result settles the argument, or that the answer as a whole is accurate.
- `usage` in the result says how many checks the account has used this month; mention it only when the user asks or the allowance is nearly used.

## When a result is an error

- `isError` with `out_of_checks` or `not_entitled`: relay the sentence in `content[0].text` as it is. It already names the plans page. Add nothing about prices, plans or changing plans.
- Any other `isError`: relay the sentence; it says what to change (a type to add, a passage to shorten, a report id this account does not hold).

## Retries

A retry of the same check reuses the same `idempotency_key`; within 24 hours it returns the first result and is not metered again. A new check gets a new key.
