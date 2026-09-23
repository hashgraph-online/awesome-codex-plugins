# Prohibited Acts and Penalties — Điều 7, 8

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

## Điều 7 — Prohibited acts

1. Processing personal data **against the State**, affecting national defence, security, social order and safety, or the lawful rights of agencies, organisations and individuals
2. **Obstructing** personal data protection activities
3. **Abusing** data protection activities to commit violations
4. Processing personal data **contrary to law**
5. Using another person's personal data, or letting another use yours, to commit unlawful acts
6. **Buying or selling personal data**, unless the law provides otherwise
7. **Appropriating, intentionally disclosing, or losing** personal data

Item 7 is the one to note: **intentional disclosure or loss is a prohibited act in itself**, distinct from the notification duty in Điều 23. Item 6 pairs with the Điều 8(3) penalty below.

Re-identification of de-identified data is prohibited separately — see [04-access-correction](04-access-correction.md) on Điều 14 read with Điều 2(1).

## Điều 8 — Handling of violations

**Điều 8(1):** depending on nature, severity and consequences, violators may face **administrative penalties or criminal prosecution**; where damage is caused, **compensation** is owed.

**Điều 8(2):** administrative penalties follow Điều 8(3)–(7) and the general law on handling administrative violations.

### The two caps engineers should know

| Provision | Maximum |
|---|---|
| **Điều 8(3)** — buying or selling personal data | **10× the revenue gained from the violation**. Where there is no such gain, or the calculated figure is lower than the Điều 8(5) cap, the Điều 8(5) cap applies instead |
| **Điều 8(4)** — cross-border transfer violations, organisations | **5% of revenue** |

Two features distinguish this from the rest of the skill:

- **Điều 8(3) is a multiplier on illicit gain, not a ceiling.** Selling data profitably does not cap exposure at a fixed sum; it scales it. Indonesia's 2%-of-revenue and Malaysia's fixed per-principle fines both behave differently.
- **The 5% cross-border cap is the highest revenue-based penalty among the six jurisdictions covered here** — above Indonesia's 2% under Pasal 57(3). Given how broadly Điều 20(1)(c) defines cross-border transfer, the exposure attaches to a very ordinary architectural decision: processing Vietnamese users' data on a platform outside Vietnam without having filed the assessment.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md).
