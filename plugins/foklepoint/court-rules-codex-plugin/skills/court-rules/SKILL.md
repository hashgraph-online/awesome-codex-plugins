---
name: court-rules
description: Find U.S. federal and state court filing rules, local rules, judge standing orders and court holidays with the Court Rules MCP tools, and answer with the source document cited. Use when a task asks about page or word limits, courtesy copies, pre-motion conferences, e-filing, service, filing timing or fees, a specific judge's practices, or which days a court is closed.
---

# Court Rules

Use the `court-rules` MCP server (tools listed below) to answer questions about how to file in a specific court or in front of a specific judge. Every rule the server returns carries the URL of the court's own document. Report that URL with the answer.

## Workflow

1. **Find the court.** Call `list_courts` with `query` set to part of the court name or ID (for example `"eastern district of new york"`, `"edny"`, `"cook"`). Copy the `district_id` from the result (examples: `edny`, `sdny`, `il-cook-circuit`, `ca-los-angeles-superior`). Results come in pages: to read on, call again with `offset` set to the previous `next_offset`; `next_offset` is null on the last page.
2. **Find the judge, if the question names one.** Call `search_judges` with `district_id` and `name` (partial match). Copy the `judge_slug`. Judges who no longer sit are hidden by default because they carry no current rules; set `include_inactive` only when the user asks about a former judge.
3. **Get the rules.**
   - For a topic across a court or a judge, call `search_filing_rules` with `district_id`, and optionally `judge_slug`, `q` (search terms such as `"courtesy copies"` or `"rejected cure"`), `logic_type`, `workflow_phase`, `case_type` and `limit`. Use `judge_slug` `"court"` for court-wide rules. When `judge_slug` is a judge, court-wide rules are included unless `include_court_rules` is false.
   - For every rule held for one judge, call `get_judge_rules` with `judge_slug` and `district_id`.
4. **Court closures.** Call `list_court_holidays` with `district_id` and either `year` or `date_from` and `date_to`.
5. **Compliance check.** `check_compliance` does not run a check. It returns the request parameters for the REST compliance check (documented at https://docs.courtrules.app/api-reference/check), which needs an API key and runs for the Eastern District of New York (`edny`) today. Show the parameters to the user and say that the check itself is a separate API call they make with their own key.

## Filter values

- `logic_type`: `CourtesyCopyRule`, `PageWordLimitRule`, `PreMotionConferenceRule`, `AdjournmentRequirementRule`, `BundlingRule`, `FormatConstraint`, `DocumentRequirement`, `CommunicationRule`, `SealingProcedure`, `ElectronicFilingRule`, `FilingTimingRule`, `ServiceRule`, `FilingFeeRule`, `JuniorLawyerIncentive`.
- `workflow_phase`: `FILING`, `CASE_INITIATION`, `MOTION_PRACTICE`, `TRIAL_PREP`, `POST_JUDGMENT`.
- Narrow with `district_id`, `judge_slug` or `logic_type` before searching broadly. A search that is too broad is refused.

## How to answer

- Quote or summarize the rule, then give the `source_url` and any page, section or paragraph from the citation fields.
- Fields the server omits are not stated in the source text. Do not fill them in with defaults, and do not turn a missing field into "no limit" or "not required".
- If a search returns nothing, say so and name the court page or document the user should read. Do not answer from memory for a specific court or judge.
- Rules and holidays change. Tell the user to confirm the cited source before filing. This is reference information, not legal advice.
- The enforcement tools (`search_enforcement_actions`, `get_enforcement_details`, `get_enforcement_stats`) cover privacy and regulatory enforcement actions. Use them only when the question is about enforcement, not filing rules.

## Sign-in

The server asks the MCP client to sign in on first use (a browser window opens console.courtrules.app; Google or email). Clients without a browser can send an API key from the same console as an `Authorization: Bearer <api_key>` header. See https://docs.courtrules.app/authentication.
