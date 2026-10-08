# Toil evidence

Rank repeated operational friction in explicitly supplied history. This
operation reads and reports; it creates no tracker items, automations,
ownership or queue.

Read only the explicitly supplied, authorized history within the stated window.
Preserve queries, filters and representative source references. Exclude machine
echoes and restored copies before clustering equivalent human actions. For
supplied Codex JSONL in a source checkout, the optional helper
`python3 scripts/toil-mining/recent_human.py --since <zoned-time> --until <zoned-time>
<explicit-session-paths>` extracts to stdout without discovering sessions or
reading attachments. Missing `client_id`, malformed records and exclusions stay
counted and disclosed; the extractor does not itself infer toil. It is not
bundled with standalone skill installs and adds no Python runtime dependency
to ordinary Memory use.

Report frequency, observed elapsed/token cost and failure or correction rate
separately. A recurring-toil claim needs three resolvable occurrences; smaller
groups remain tentative with their actual count. For a composite ranking, show
the measured inputs and formula; missing factors remain unmeasured, never an
invented average. Rank by demonstrated burden, not frequency or salience alone.
Each candidate includes clustering confidence, representative evidence, limits
and the smallest plausible automation shape. Separate observations from advice.

Return the ranked evidence inline by default, with checked/not-checked sources.
Only write a report when requested, using the authorized destination under
[Memory's storage rules](../SKILL.md#access-storage-and-honest-limits). A
packaging request can use [Skill Builder](../../skill-builder/SKILL.md);
evidence alone grants no authority to adopt a rule or schedule a job.
