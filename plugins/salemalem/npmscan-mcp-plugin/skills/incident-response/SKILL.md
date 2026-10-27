---
name: incident-response
description: Turn a flagged npm supply-chain finding — or just a vague, non-technical description of one ("this package looks sketchy," "someone said we got hacked," "npm install did something weird") — into concrete remediation steps. Use whenever the user wants to know what to actually do about a suspicious/compromised/flagged package, however precisely or vaguely they describe it — not for the initial trust/vulnerability investigation itself (see package-trust-check/dependency-audit for that).
---

# NPMScan incident response

Use this skill once the user wants to know what to actually *do* about a
supply-chain concern, not just what was found — whether that concern is a
precise tool finding already in this conversation, or just a worried,
non-technical description of a symptom. Most users will not know terms like
"lifecycle script" or a `rule` id, and will not think to run an npmscan tool
themselves first — reformulating a vague description into the right call is
this skill's job, not something to push back on the user for. This is the
last step, not a replacement for `package-trust-check` (single-package trust
questions) or `dependency-audit` (multi-package audits): those skills
investigate and report; this one turns a concern — precise or vague — into
an actionable plan.

## Reading a vague or non-technical request

Do not require the user to already know a `rule` id, a playbook name, or
npmscan's own vocabulary. Translate what they actually said using their
intent, not their exact words. Common shapes and what they map to:

| What the user says (any rough equivalent) | What to do |
|---|---|
| Names a specific package and says it's "sketchy," "hacked," "compromised," or just "is this safe" | Run `package-trust-check`'s investigation first (get_package, check_maintainer_changes, check_package_provenance, analyze_install_script as applicable) — you need real findings before a remediation plan means anything. Once findings exist, continue to step 2 below. |
| Names a package AND describes a specific symptom ("it downloads something during install," "the maintainer changed") | Run the one finding tool that actually checks that symptom (analyze_install_script for install-time behavior, check_maintainer_changes for ownership, check_package_provenance for publish/build mismatches) rather than the full trust-check sweep — faster, and still grounds the answer in a real finding. |
| Describes a symptom with NO package name — "what do we do about a postinstall that downloads a binary," "how do we respond to a typosquat," "what's the process for a maintainer takeover" | No finding tool has anything to check. Go straight to `get_remediation_playbook({ id: "..." })` with your best-guess playbook id from the table below. A wrong guess is harmless — it comes back `matched: false` — so guess confidently rather than asking the user to be more specific first. |
| Totally generic, no package, no symptom — "we got a security alert, what do I do," "help, is this bad" | The one case worth a single clarifying question: ask what specifically happened or which package/alert, since there is nothing yet to ground a plan in. Don't guess a playbook id from nothing. |

Symptom → playbook `id` guesses for the no-package-name case:

- downloads/runs a binary, executable, or installer during install → `postinstall-binary`
- name looks like / is close to a well-known package, "typosquat," "fake version of X" → `suspected-typosquat`
- general "hacked," "compromised," "malicious code," "supply chain attack" with no more specific detail → `supply-chain-compromise`
- "we published something we didn't," "our npm token was stolen," "our package got hijacked," a worm spreading through packages we maintain (Shai-Hulud) — the user is the PUBLISHER, not a consumer → `compromised-publisher` (token revocation, credential rotation, deprecating/unpublishing the bad versions, telling users). If both apply — they installed something malicious AND it then published from their account — present both playbooks.
- runs shell commands, `exec`, spawns a process during install → `child-process-in-install`
- "calls out," "connects to a server," "phones home" during install → `unexpected-network-install`
- "new maintainer," "ownership changed," "ownership transfer," "ex-employee's account" → `maintainer-change-flagged`
- "provenance," "build doesn't match the repo," "install script wasn't in the source," "someone bypassed CI" → `provenance-mismatch`

## Steps

1. Read the request per the table above. If a finding already exists in
   this conversation (a prior `analyze_install_script`,
   `check_maintainer_changes`, or `check_package_provenance` result), skip
   straight to step 2 with its `findings[].rule` value(s).
2. Call `get_remediation_playbook({ rules: [...] })` with every distinct
   `rule` value from the finding(s) in one call — it batches and deduplicates,
   so don't call it once per rule. Use `id` instead for a symptom-only
   request with no live finding (see the table above).
3. If the underlying finding's `riskTier` came back `none` (or the findings
   array was empty), say plainly that no remediation is needed rather than
   still calling this tool to manufacture a plan — an incident-response
   playbook implies there's something to respond to.
4. For each `matched: true` result, present that playbook's `title`,
   `severity`, and `steps` directly in your answer — the step `text` plus
   its `why`, in order — not a paraphrase and not just a link. Lead with the
   match's own `situationNote` when one exists (what this specific rule
   actually found) before the steps, so the response is grounded in the real
   finding rather than reading as generic boilerplate — this matters most
   when a batch has several different rules landing on the same playbook
   (see step 6). If you got here from an `id` guess rather than a real
   finding (no `situationNote`), say so plainly ("this sounds like it might
   be X — here's that playbook; tell me more if it's actually something
   else") rather than presenting a guess as a confirmed diagnosis. Close
   with the playbook's `preventionTips` when the user's question has any
   forward-looking angle ("how do we stop this happening again," a policy/CI
   question, or just naturally as part of a full incident report), and cite
   its `references` (each labeled `incident` or `reading`) so the user can
   verify the real-world grounding themselves — don't call an `incident`
   reference a "reading" or vice versa, that distinction is deliberate.
   Include the `npmscanUrl` too so the user can also read it on the docs
   site.
5. For any `matched: false` result, say so plainly using the tool's own
   `note` (e.g. "this finding is baseline/informational, not something with
   its own response plan") — don't silently drop it or invent generic advice
   in its place. If your own `id` guess came back unmatched, try the
   next-closest guess from the table, or ask the one clarifying question
   from the "totally generic" row rather than giving up.
6. When a findings array maps to more than one distinct playbook (e.g. a
   `check_maintainer_changes` result with both a turnover finding and a
   repository-transfer finding pointing at the same playbook, or a mixed
   maintainer + provenance investigation pointing at two different ones),
   present each matched playbook once, not once per originating finding.

## Do not

- Do not write your own remediation steps once a finding tool has run —
  call `get_remediation_playbook` and use its actual `steps`/`why` text,
  don't paraphrase or improvise around it.
- Do not refuse to help, or ask the user to look up a `rule`/playbook id
  themselves, just because their request was vague — that is exactly the
  case the table above exists for. Only ask a clarifying question in the
  genuinely-nothing-to-go-on case.
- Do not treat `matched: false` as "this is safe" — it means no dedicated
  playbook exists for that specific rule, which is a different statement
  than "no risk here." Say what the tool's `note` actually says.
- Do not skip a finding tool and go straight to an `id` guess when the user
  named a specific package — a guess is only for the no-package-name,
  symptom-only case. When a package is named, ground the answer in a real
  finding first.
- Do not present an `id`-guessed playbook as if it were a confirmed
  diagnosis — say plainly that it's your best read of their description.
- Do not call `get_remediation_playbook` once per rule when a findings array
  has several — batch all the rule values into one call's `rules` array.
- Do not force a playbook onto a clean/`none`-risk-tier result just because
  the user asked "what should I do" — say no action is needed.
- Do not embellish a playbook's `references` beyond what's returned — cite
  only the `label`/`url` the tool gave you, and preserve whether the tool
  marked it `incident` (a real, verified compromise) or `reading`
  (background material, not itself a breach) rather than upgrading a
  `reading` reference into a claimed incident.

- Do not answer a "we were the ones who got compromised" description with
  only the consumer-side `supply-chain-compromise` steps — pinning and
  auditing don't revoke a stolen token; use `compromised-publisher`.
- Do not attempt to install, upgrade, or publish packages yourself; this
  skill only reads data through NPMScan's read-only MCP tools.

## Tools used

`get_remediation_playbook`, plus whichever of `analyze_install_script`,
`check_maintainer_changes`, `check_package_provenance` is needed to produce
the finding this skill responds to — all provided by the `npmscan` MCP server bundled with this plugin
(`.mcp.json`). See [references/test-prompts.md](references/test-prompts.md)
for prompts to manually verify this skill after installing or editing it.
