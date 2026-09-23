# Sector and Technology-Specific Duties — Điều 24–32 + Decree Điều 8–12

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

Vietnam is the only jurisdiction in this skill that imposes duties **by sector and technology** rather than only by lifecycle stage. Nine Law articles and five Decree articles sit here. Check this file whenever a feature falls into one of the categories below — the general obligation files do not repeat these duties.

## Law Điều 24–32

| Điều | Covers | Typical engineering trigger |
|---|---|---|
| **24** | Children; persons lacking or with limited civil act capacity | Any product usable by minors; age gates; guardian consent flows |
| **25** | Recruitment, management and use of employees | HR systems, applicant tracking, workforce monitoring |
| **26** | Health information and related business activity | Health features, symptom logging, fitness data, insurance |
| **27** | Finance, banking, credit information | Payments, lending, credit scoring, transaction history |
| **28** | Advertising services | Ad targeting, audience building, marketing segments |
| **29** | Social media platforms and online communication services | Feeds, messaging, profiles, UGC |
| **30** | **Big data, artificial intelligence, blockchain, virtual worlds** | Model training, analytics at scale, on-chain identifiers |
| **31** | **Personal location data and biometric data** | GPS, geofencing, face or fingerprint authentication |
| **32** | Data obtained from **audio and video recording in public places** | CCTV, dashcams, in-venue cameras, voice capture |

## Decree Điều 8–12 — the technology overlay

These are the ones to check at design time, because each constrains an architectural decision that is expensive to reverse:

| If you are… | Read | Why it changes the design |
|---|---|---|
| Training or fine-tuning on user data | **Điều 10** (AI systems, virtual worlds) | Sets the conditions under which personal data may be used for research and development. Decide before the data reaches a training set — you cannot un-train a model |
| Writing anything user-keyed on-chain | **Điều 11** (blockchain) | Immutability collides with Điều 13 correction and Điều 14 deletion. If an identifier lands on-chain you may be unable to satisfy either right |
| Choosing cloud regions or a managed service | **Điều 12** (cloud computing) + **Law Điều 20(1)(c)** | Technical and organisational measures are required of the parties involved, **and** a region outside Vietnam is a cross-border transfer — the two obligations stack, and the transfer one carries a 60-day filing deadline |
| Running analytics at scale | **Điều 9** (big data) | Applies to processing containing personal data at large scale. Note Decree Điều 4(1)(l) already makes behaviour-tracking data **sensitive**, so this usually stacks with the Điều 4(2) control requirements |
| Handling payments, lending or credit | **Điều 8** (finance, banking, credit) | Stacks with Decree Điều 4(1)(k), which makes card data, transaction history and credit information sensitive |

The blockchain and AI rows are the two that most often surface too late. Both are cheap to design around and very expensive to retrofit.

## Reading order

These articles **add to** the general obligations; they do not replace them. A feature in one of these categories still needs the Điều 9 consent mechanics, the Điều 21 impact assessment, and the Điều 23 notification path. Work the general files first, then come here for the sector overlay.

## Cross-references

- Location and biometric data are also **sensitive** under Decree Điều 4(1)(đ) and (h) — see [03-purpose](03-purpose.md).
- Behaviour-tracking data on social media and online communication services is **sensitive** under Decree Điều 4(1)(l), which interacts directly with Điều 29 and Điều 30.
- Financial and transaction data is **sensitive** under Decree Điều 4(1)(k), interacting with Điều 27 and Decree Điều 8.
