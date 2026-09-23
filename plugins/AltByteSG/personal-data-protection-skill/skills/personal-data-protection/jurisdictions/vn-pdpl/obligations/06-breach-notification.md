# Personal Data Breach Notification — Điều 23

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

Vietnam has a **72-hour** clock running from **detection of the violating act**, to the specialised authority under the Ministry of Public Security. The trigger is **harm-based, not scale-based** — there is no affected-count threshold to measure against.

## Điều 23(1) — The rule

The controller, controller-and-processor, or **third party** that detects a violation of personal-data-protection rules which **may cause harm to**:

- national defence, national security, social order and safety; **or**
- the **life, health, honour, dignity or property** of the data subject

must notify the specialised authority **no later than 72 hours from detecting the violating act** (`chậm nhất là 72 giờ kể từ khi phát hiện hành vi vi phạm`).

Where the **processor** detects the violation, it must promptly notify the controller or controller-and-processor.

**Read the trigger carefully.** Two things differ from the rest of this skill:

1. **The clock starts at detection of the act**, not at assessment (SG s26D) and not at awareness of a breach's consequences. There is no assessment window buffering the deadline.
2. **The threshold is qualitative.** "May cause harm" to the listed interests — including *honour* and *dignity*, which have no counterpart in the other four regimes. A small leak of embarrassing data can qualify where a large leak of innocuous data may not.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

## Điều 23(2) — Record and cooperate

The controller or controller-and-processor must **make a written record** (`biên bản`) confirming that the violation occurred, and coordinate with the specialised authority in handling it.

**Operationalisation:** the incident log is not merely good practice here — a confirmation record is a statutory artefact. Capture detection time, detector, the act, affected data categories, and the notification timestamp. Detection time is the field that determines whether you met the clock, so record it the moment anyone raises the alarm, not when triage concludes.

## Điều 23(3) — Additional notification cases

Organisations and individuals notify the specialised authority where:

- a) a violation of personal-data-protection rules is detected;
- b) personal data is processed **for the wrong purpose**, or contrary to the agreement between the subject and the controller;
- c) the **rights of the data subject** are not ensured, or are performed incorrectly;
- d) other cases provided by law.

**This is broader than a security-incident duty.** Điều 23(3)(b) and (c) mean a purpose-creep bug, or a failure of your access/deletion path, is itself a notifiable matter — not only a leak. Nothing equivalent exists in SG, TH, ID, MY or PH.

## Điều 23(4) — Authority's role

The specialised authority receives notifications and handles violations.

## Decree Điều 28 — What the notification must contain

The Decree fixes both the content and the channel.

**Content (Điều 28(1)):**

- a) **Nature of the violation** — time, place, the act, the organisations and individuals involved, the **categories of personal data** and the **volume** concerned
- b) **Contact details** of the data-protection unit or personnel, or of the service provider
- c) Description of the **possible consequences and damage**
- d) Description of the **measures taken** to resolve and mitigate

**Channel (Điều 28(2)):** submitted to the specialised authority **or via the national personal-data-protection portal**, using **Form No. 08** in the Decree's Appendix.

**Operationalisation:** pre-fill Form No. 08 before you need it, and make sure your incident log captures the fields it asks for — especially *data categories* and *volume*, which are hard to reconstruct after the fact under time pressure. Điều 29 covers notification specifically for sensitive personal data.

## Examples that should be triaged

Use the general detection-signal and triage guidance in [layer 07 Operational](../../../layers/07-operational.md#sub-processor--vendor-breaches). VN-specific additions:

- A bug that processed data outside its consented purpose → Điều 23(3)(b), notifiable in its own right
- A broken export or deletion path → Điều 23(3)(c)
- Leak of data touching honour or dignity (private messages, images, health) at **any** scale → Điều 23(1)

## Operational checklist (incorporate into the runbook)

General readiness items: [layer 07 Operational](../../../layers/07-operational.md#runbook-readiness-checklist). VN-specific:

- [ ] Detection timestamp captured at first signal — the 72h clock runs from here, with no assessment buffer
- [ ] **Form No. 08** (Decree Appendix) pre-filled; route confirmed — specialised authority or the national personal-data-protection portal — with two people holding access
- [ ] `biên bản` confirmation-record template pre-staged (Điều 23(2))
- [ ] Incident log captures **data categories and volume** (Decree Điều 28(1)(a)) — hard to reconstruct later
- [ ] Triage rules cover the Điều 23(3)(b)/(c) non-security cases, not only leaks
