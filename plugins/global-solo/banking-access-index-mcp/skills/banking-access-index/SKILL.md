---
name: banking-access-index
description: Look up what US business banking providers publish about applicants who are not US tax residents but own a US LLC, from the Global Solo Banking Access Index (19 providers including Mercury, Relay, Wise Business and Payoneer; India, China, UK, Canada, Pakistan, Nigeria, Turkey, Brazil). Use when someone asks whether a founder living in one of those countries can open a US business account with a named provider, which providers restrict a country, or what a provider asks for (SSN or ITIN, a US phone number, remote onboarding). Every answer carries the provider's own source URL and the date that URL was read.
---

# Banking Access Index

The index records what each provider **publishes**. It is not a prediction of an underwriting
decision: an application can be declined on grounds no published page covers.

## Where the data is

| File | Size | Use it for |
|---|---|---|
| `https://www.globalsolo.global/data/banking-access-index.csv` | ~8 KB | The matrix: one row per provider, one `<country>_status` column per country, plus `non_resident_stance`, `ssn_itin_requirement`, `phone_us_required`, `remote_onboarding`, `restricted_list_url`, `verified_at`. Enough for "which providers restrict Pakistan" or "does Relay need an SSN". |
| `https://www.globalsolo.global/data/banking-access-index.json` | ~620 KB | The evidence behind one cell: `note`, `evidence[].url`, `evidence[].date`, and the two discriminators `restrict_kind` and `unknown_kind`. Read only the cells the question needs. |

With a shell, save the JSON once as `baix.json` (it is data, not code), then read single cells
instead of the whole file:

```bash
# one provider, one country, with its evidence
jq '.providers[] | select(.id=="mercury") | {display_name, cell: .countries.india}' baix.json

# every provider for one country: id, name, status, restrict_kind, unknown_kind
jq -r '.providers[] | [.id, .display_name, .countries.pakistan.status, (.countries.pakistan.restrict_kind // "-"), (.countries.pakistan.unknown_kind // "-")] | @tsv' baix.json
```

Country keys: `india`, `china`, `uk`, `canada`, `pakistan`, `nigeria`, `turkey`, `brazil`.
Without a shell, fetch the CSV first and open the JSON only for the cells you cite.

## The status vocabulary

| Status | Meaning |
|---|---|
| `explicit_accept` | The provider publishes a statement that covers applicants in this country. |
| `explicit_restrict` | The provider publishes a restriction that covers this country. |
| `no_published_restriction` | The country is absent from the published restriction list, and no acceptance statement was located. |
| `unknown` | No published position was located. |

`restrict_kind` says how a restriction is evidenced: `named_on_prohibited_list`,
`absent_from_closed_eligibility_list`, or `blanket_rule_no_country_named`.
`unknown_kind` says why a cell is unknown: `no_policy_published`, `mentioned_for_other_purpose`,
`absent_from_non_exhaustive_list`, or `conflicting_sources`.

## How to answer

1. Give the status label as written, the provider's source URL, and the access date from
   `evidence[].date`. Say the date out loud: a claim can go stale after it was read.
2. Report `no_published_restriction` as exactly that. It is not an acceptance. Write it as "the
   provider publishes no restriction for this country, and no acceptance statement was located".
3. Carry `restrict_kind` or `unknown_kind` when the cell has one. The outcome for the applicant can
   be the same while the evidence behind it differs, and the evidence is the point of the dataset.
4. A provider or a country outside the 19 × 8 was **not assessed**. Say so. Do not fill the gap
   from general knowledge or from the provider's marketing pages.
5. Describe what each provider publishes and leave the choice to the person asking. The index
   ranks no provider and gives no legal, tax or banking advice.
6. Attribute the data: *Global Solo Banking Access Index*, CC BY 4.0,
   <https://www.globalsolo.global/data/banking-access-index>. The methodology is at
   <https://www.globalsolo.global/about/methodology>.
