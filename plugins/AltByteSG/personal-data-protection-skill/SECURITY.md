# Security Policy

This repository is **documentation, not running software** — there is no service to attack, no API to exploit, and no user data held by the project. That said, the content shapes how engineers think about personal-data-protection compliance, so accuracy and integrity matter.

This file tells you how to report concerns.

## Where to report

Everything goes through this repository's GitHub issues and pull requests — no email, no separate channel.

| Concern | What to do |
|---|---|
| **Content that could mislead a user into a real compliance breach** (e.g. wrong breach-notification deadline, wrong penalty cap, wrong statute citation that materially changes the obligation) | Open an issue with the `compliance-concern` label. Cite the official source (regulator's website, statute text on the official portal) so we can verify quickly. |
| **Suspected malicious pull request** (e.g. a PR that subtly weakens consent guidance, inserts a backdoor link) | Comment on the PR. Maintainers review every PR before merge. |
| **Compromised maintainer account / repo takeover** | Report to **GitHub Support** at [support.github.com](https://support.github.com). We can't fix what we no longer control — GitHub can. |
| Typo, formatting bug, broken link, stale citation | Open an issue or PR — public is fine. |
| Disagreement with interpretation of a statute | Open an issue with sources — public discussion welcome. |
| Suggestion for new content / new jurisdiction | Open an issue using the relevant template. |

## What to expect

- Issues with the `compliance-concern` label are triaged ahead of typo / formatting reports
- We aim to respond to high-priority reports within **5 business days** and publish a fix or correction within **30 days** of confirming the issue
- These are aspirational targets, not contractual commitments — the maintainers are a small team

## What we ask of reporters

- **For high-priority content issues, please don't escalate publicly (social media, blog posts) before opening an issue and giving maintainers a reasonable chance to fix it.** Coordinated disclosure protects users.
- **Cite authoritative sources.** "This file is wrong" is hard to act on; "Pasal 46 says X but the file says Y, see [official source]" is actionable in minutes.
- **Be specific.** Filename, line number, and exact quote from the official statute beats vague description every time.

## What this repository is **not**

- **Not a vulnerability disclosure programme** for any product, application, or service. If you've found a vulnerability in an *application that uses this skill*, contact that application's vendor — not us.
- **Not a hotline for compliance emergencies.** If you suspect your organisation has had a personal-data breach, do not file an issue here — engage your DPO and your local regulator according to your statutory obligations. See [`DISCLAIMER.md`](DISCLAIMER.md).
- **Not a substitute for the regulator's official channels.** If you have a regulatory complaint about an organisation, contact the relevant regulator directly:
  - Singapore: [www.pdpc.gov.sg](https://www.pdpc.gov.sg)
  - Thailand: [www.pdpc.or.th](https://www.pdpc.or.th)
  - Indonesia: Komdigi via [www.komdigi.go.id](https://www.komdigi.go.id)

## Disclaimer

Reporting an issue does not create any contractual or professional advisory relationship with the maintainers. See [`DISCLAIMER.md`](DISCLAIMER.md) for the full terms governing your use of this repository.
