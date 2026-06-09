# Layer 06 — Disclosure

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Documents and copy that the user reads. The "Notification of Purpose" obligation lives here. Universal across PDP-family jurisdictions.

## Privacy Policy structure

A complete privacy policy for a PDP-compliant consumer application typically includes:

| Section | Contents |
|---|---|
| Header / Last updated date | Bump on every material change |
| 1. Data controller | Legal entity name, registered office, contact email |
| 2. Data we collect | Sub-sections per category: account data, content, technical data, location, photos, etc. |
| 3. Purposes for collection and use | Table mapping purpose → lawful basis (consent / contractual necessity / business improvement / etc.) |
| 4. How we use data | Plain-English version of section 3 |
| 5. Data sharing | Three buckets: with other users (visibility settings), with sub-processors (table), legal requirements |
| 5.1 Sub-processors | Named third parties processing user PII, with purpose, data categories, region |
| 6. Storage and security | Where data lives, encryption, access controls, RLS / equivalent |
| 6.1 Sign-in providers | Apple / Google / etc. — what they receive, what we store |
| 7. Data retention | Table per data category with retention period and trigger |
| 8. Your rights | Access / correction / withdrawal of consent / deletion — how to exercise each |
| 9. Children's privacy | Minimum age, what we do if we discover a minor |
| 10. International transfers | Cross-border story, transfer-mechanism reference |
| 11. Cookies | If applicable; "we do not use cookies" is a valid section if true |
| 12. Changes to this policy | How users will be informed |
| 13. Supervisory authority | The relevant regulator (PDPC SG, MOCI ID, PDPC TH) with contact |
| 14. Contact | DPO email |

**Update discipline:** whenever a layer 03–05 change introduces a new data category, purpose, sub-processor, or retention rule, the corresponding privacy-policy section updates in the **same PR**. Drift between code and disclosure is one of the most common audit findings.

## Sub-processor disclosure

The "Sub-processors" table is where many privacy policies are weakest. Common failure modes:

- **Generic placeholder language** ("we use cloud infrastructure providers") instead of named vendors.
- **Stale list** — vendors get added in code but the policy isn't updated.
- **Over-disclosure** of vendors that don't actually process PII (CDNs, source-code hosts, dev tools).
- **Under-disclosure** of vendors integrated for admin-only flows that nonetheless process user data (e.g. an admin email digest provider).

**Inclusion test:** does the vendor receive a value that maps to an individual user (UUID, email, name, IP, push token, etc.)? If yes, list them.

**Exclusion test:** is the vendor purely transit (CDN, edge cache) or developer tooling (source control, CI)? If yes, exclude — listing them dilutes the disclosure and confuses users.

## T&C structure

Less prescriptive than the privacy policy but typically includes:

| Section | Contents |
|---|---|
| Acceptance | The user agrees to these terms by using the service |
| Eligibility | Minimum age, geographic limitations |
| Account | Username uniqueness, password security, transfer prohibition |
| User content | Ownership (user retains), licence to operate the service |
| Acceptable use | Prohibited behaviours |
| Service availability | No uptime guarantee, modification rights |
| Termination | Self-deletion right, suspension grounds |
| Liability limitation | Standard exclusions and caps |
| Indemnification | User indemnifies for their content / misuse |
| Governing law | Jurisdiction of the courts |
| Age & child safety | Minimum age, reporting channel for child-safety concerns |

## OS permission usage strings

Any OS-level permission your app requests (camera, photos, location, notifications, contacts, microphone, etc.) requires a usage string explaining why.

**iOS** — `Info.plist` keys:
- `NSCameraUsageDescription`
- `NSPhotoLibraryUsageDescription`
- `NSLocationWhenInUseUsageDescription`
- `NSMicrophoneUsageDescription`
- etc.

**Android** — runtime permission rationale UI shown before requesting.

**Rules for the strings:**
- **Specific, not generic.** "We need access to take photos for your profile" — not "we may use the camera."
- **In your app's voice.** First-person plural is conventional ("We use…").
- **Match the privacy policy.** If the permission collects data, the privacy policy section 2 must list it as a data category and section 3 must justify the purpose.

When adding a new permission, update three places in the same PR:
1. The platform manifest (Info.plist / AndroidManifest)
2. The just-in-time prompt UI (soft-prompt dialog before the OS prompt)
3. The privacy policy

## Contextual notices

Beyond permission prompts, in-app notices to consider for new data uses:

- **Onboarding tooltips** for sensitive permissions (camera, location).
- **Settings page explainers** for what each toggle controls.
- **Banners for unverified states** (unverified email, expired tokens).
- **Material-change banners** when the privacy policy or T&C is updated and re-acceptance is needed.

When adding any such notice: keep copy plain-language, no jargon, name the data category and purpose explicitly.

## Marketing notifications copy (when applicable)

If your application sends marketing pushes or emails:

- Each marketing message must include an unsubscribe mechanism (one-tap for email; in-app toggle for push).
- The first marketing message after opt-in should clarify the user can opt out at any time.
- Frequency must match what the user opted into ("weekly newsletter" cannot become daily without re-consent).

## Languages

If your application is offered in multiple languages, the privacy policy and T&C must be translated. Some jurisdictions require this (e.g. Indonesian for ID PDP if serving Indonesian users in Bahasa Indonesia). Translation should be reviewed by a native speaker familiar with privacy terminology — automated translation often loses precision on terms of art ("controller", "processor", "purpose", "consent").

For v0.1 of an English-only application, document the limitation and the markets it implicitly excludes.
