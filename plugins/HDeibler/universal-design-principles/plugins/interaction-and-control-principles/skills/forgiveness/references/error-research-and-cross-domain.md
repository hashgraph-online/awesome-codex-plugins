# Forgiveness: error research and cross-domain reference

A reference complementing the `forgiveness` SKILL.md with deeper grounding from human-error research and examples from safety-critical domains.

## Reason's classification of error

James Reason's *Human Error* (Cambridge University Press, 1990) is the standard reference for error analysis. Reason distinguishes:

### Slips and lapses (skill-based errors)

The user knew what to do; their action didn't match their intent. Examples:

- Typing the wrong key.
- Clicking the wrong button (intended Save, hit Submit).
- Forgetting to attach the file before sending the email.

Slips happen even to experts at familiar tasks. They are the bulk of routine errors. The forgiveness response: make the wrong action harder to take by accident (defensible space, target sizing, anti-affordance) and make the right action easy to recover (undo, soft delete).

### Mistakes (rule-based or knowledge-based)

The user's action matched their intent, but the intent was wrong because their model of the situation was wrong. Examples:

- Following the wrong instructions because they didn't know the situation differed.
- Choosing the wrong option because they misunderstood the choices.
- Building the wrong feature because requirements were misread.

Mistakes happen more to new users and in unusual situations. The forgiveness response: reduce ambiguity (clear copy, consistent behavior), provide help in context, surface confirmations for high-stakes actions where wrong intent is plausible.

### Violations

Deliberate departures from rules — sometimes routine ("speeding because everyone does it"), sometimes situational ("breaking the rule to save lives in an emergency"). Less common in software UI but worth knowing about.

The slip/mistake distinction matters because the right forgiveness mechanism differs:

| Error type | Best forgiveness response |
|---|---|
| Slip | Reversibility (undo, soft delete) |
| Mistake | Information / explanation; confirmation of intent |
| Violation | Constraints; audit logs; safety nets |

## Forgiveness in safety-critical domains

### Aviation

Aviation has driven much of the modern thinking on human error. Key forgiveness patterns:

- **Checklists** prevent slips by externalizing memory (Atul Gawande's *The Checklist Manifesto* documents this thoroughly).
- **Cockpit voice recorders and flight data recorders** are safety nets — they don't prevent error but enable diagnosis after.
- **Fly-by-wire** systems prevent some pilot inputs that would damage the aircraft (a structural prevention).
- **Crew Resource Management** (CRM) trains crews to challenge each other on mistakes — social forgiveness.

### Medicine

Medical errors are the third leading cause of death in the US (per a 2016 BMJ analysis). Forgiveness patterns:

- **Barcoded medication administration** (BCMA) — the nurse scans both the patient's wristband and the medication; mismatches block administration.
- **Pharmacy double-checks** for high-risk medications.
- **The Universal Protocol** (mark the surgical site, time-out before incision) prevents wrong-site surgery.
- **Tall-man lettering** for confusable drug names (DOPamine vs. DOBUTamine) reduces slip rates.

### Industrial

- **Lockout-Tagout** (LOTO) procedures prevent equipment from being energized during maintenance.
- **Two-key authorization** for hazardous operations (nuclear missile launch, blood-bank releases).
- **Dead-man switches** that disengage if the operator becomes incapacitated.
- **Crumple zones** and **fuses** as safety nets in failure scenarios.

### Software's parallels

Modern software has analogues:

- **Two-factor authentication** ≈ two-key authorization.
- **Pre-deployment checklists** in CI/CD ≈ aviation checklists.
- **Soft delete with recovery window** ≈ surgical time-out.
- **Permission systems** that prevent destructive operations from non-admins ≈ industrial access control.
- **Audit logs** ≈ flight data recorders.

The discipline of "designing for error" cross-pollinates between these domains continuously.

## Norman's "designing for error"

In *Design of Everyday Things* (revised 2013), Norman lists design responses to error:

1. **Understand causes of error and design to minimize them.**
2. **Make it easy to discover errors.**
3. **Make it easy to reverse them.**
4. **Make it hard to perform irreversible actions.**
5. **Add forcing functions** that prevent invalid actions.

Forcing functions are particularly powerful: they make the wrong action structurally impossible. Examples in software:

- A "Send" button disabled until required fields are filled (forcing the user to complete the form).
- A confirmation dialog with the destructive button disabled until the user types a verification string.
- A multi-step flow where each step gates on the previous (the user can't accidentally skip).

## The cost of unforgiving design

The user-experience cost is obvious — frustration, lost data, support burden. The longer-term costs include:

- **Anxious habits.** Users develop ritualistic behavior (always Cmd-S after every action) because they don't trust the system.
- **Learned helplessness.** Users stop exploring features because exploration is risky.
- **Workarounds.** Users develop external systems (spreadsheets, paper notebooks) to compensate for missing forgiveness.
- **Trust erosion.** Each loss-of-data incident damages trust in the entire product, beyond the specific feature.
- **Brand damage.** Public stories of user data loss spread; the long-term cost is reputation.

The investment in forgiveness is repaid not in any one moment but in the cumulative experience of users who feel safe to use the product without anxiety.

## Confirmation fatigue research

The phenomenon is well-studied. Key findings:

- After exposure to ~3 confirmation dialogs in a session, users dismiss new ones with declining attention.
- Users who routinely confirm reversible actions develop "Yes" autopilot.
- Confirmation rate that's calibrated to action stakes (rare for routine, frequent for destructive) outperforms uniform confirmation.
- Two-step confirmation (a typed verification, not just a click) breaks autopilot for irreversible actions.

The lesson: confirmation must be calibrated and rare to be effective. Reflexive "let's add a confirm to be safe" actually reduces safety because it teaches users to dismiss confirms.

## Resources

- **Reason, J.** *Human Error* (1990).
- **Norman, D.** *The Design of Everyday Things* (1988, revised 2013) — chapters on errors and design.
- **Gawande, A.** *The Checklist Manifesto* (2009).
- **Perrow, C.** *Normal Accidents* (1984) — system-level failure analysis.
- **NN/g** — articles on error handling, undo patterns, and confirmation design.

## Closing

Forgiveness is the principle that grows in importance as users come to rely on a product. A new user might tolerate an unforgiving design briefly; a daily user develops anxiety around it. Investing in forgiveness — undo, soft delete, version history, sensible confirmation — pays compounding returns in trust, in retention, and in support cost.
