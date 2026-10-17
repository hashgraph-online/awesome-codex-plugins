---
name: errors
description: 'Use this skill whenever a design must accommodate the inevitability of human error — typos, wrong-button presses, misread instructions, mistimed actions, misunderstandings of system state. Trigger when designing form validation, input handling, destructive flows, complex multi-step procedures, alert systems, or any UI where users can do the wrong thing. Trigger when post-incident analyses reveal patterns of "human error" — most are design errors in disguise. Errors is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003), grounded in Norman''s and Reason''s foundational human-error research.'
---

# Errors

Most "accidents" attributed to human error are actually design errors. The user took the action the design invited; the action's consequence wasn't what the user intended. Reframing errors as a *design* property — rather than a *user* failing — opens the design space dramatically: errors can be prevented, made impossible, made obvious, or made recoverable. The right strategy depends on the kind of error.

## Definition (in our own words)

An error is any action (or omission) that produces an unintended result. Errors come in two distinct kinds, and they need different design responses. **Slips** are skill-based failures: the user knew what to do but their action didn't match their intent — a typo, a wrong-button click, a slip of attention. **Mistakes** are knowledge-based failures: the user did exactly what they intended, but the intent was wrong because their model of the situation was wrong — they misread an alarm, misunderstood a diagram, made a wrong choice based on incomplete information. The two kinds happen for different reasons; they're prevented by different design moves.

## Origins and research lineage

- **Donald Norman**, "Categorization of Action Slips" (*Psychological Review*, 1981, vol. 88) and *The Design of Everyday Things* (1988). Norman introduced the slip/mistake distinction to design vocabulary and argued that error is a property of design, not user.
- **James Reason**, *Human Error* (Cambridge University Press, 1990). The standard reference work in human-error research, originally from industrial-safety domains (aviation, nuclear, medical). Reason expanded Norman's framework with detailed taxonomies (skill-based / rule-based / knowledge-based errors) and the "Swiss cheese" model of cascading failures.
- **Lidwell, Holden & Butler** (2003) compactly distinguished slips (errors of execution, automatic/unconscious) from mistakes (errors of intention, conscious mental processes). The book identifies two slip subtypes (Action, Attention) and three mistake subtypes (Perception, Decision, Knowledge).
- **Charles Perrow**, *Normal Accidents* (1984). Argued that complex tightly-coupled systems produce errors as an emergent property of system design, not as failures of individual operators. Influential in industrial-safety and software-system design.
- **Atul Gawande**, *The Checklist Manifesto* (2009). Documented how checklists prevent slip-type errors in complex high-stakes domains (surgery, aviation).

## Why the slip/mistake distinction matters

The two error types are caused by different mechanisms and prevented by different design moves:

| Property | Slip | Mistake |
|---|---|---|
| Cause | Automatic, unconscious, distraction | Conscious, but wrong model |
| User awareness | Often noticed immediately | Often unrecognized at the time |
| Common context | Routine tasks, interrupted procedures | Novel situations, ambiguous information |
| Design fix | Affordance, constraint, confirmation, undo | Better information, training, clearer system state |
| Population most affected | Experienced users on routine tasks | Less-experienced users, or anyone in unfamiliar context |

A confirmation dialog can prevent slips ("Did you really mean to click delete?") but doesn't prevent mistakes (the user *intended* to delete; they just had the wrong file selected). Conversely, better explanations help with mistakes but don't help with slips (the user already knows what they meant).

Designs that treat all errors the same fail on at least one type.

## The book's slip and mistake subtypes

### Slip subtypes

#### Action slips

Wrong action despite correct intent. Examples:

- Typing the wrong word despite knowing the right one.
- Clicking the wrong button (intended Save, hit Submit).
- Hitting Reply All when meaning to Reply.

**Design responses**: confirmations for critical tasks; constraints; clear distinctive feedback; affordances and mappings that make wrong actions structurally harder.

#### Attention slips

Lapses in attention during procedures. Examples:

- Forgetting to attach a file before sending an email.
- Skipping a step in a multi-step process.
- Resuming an interrupted task at the wrong point.

**Design responses**: status cues that survive interruption; orientation aids when resuming; alarms for critical situations.

### Mistake subtypes

#### Perception mistakes

Wrong action because of misread information. Examples:

- Nurse misreading a temperature curve as stable when it's trending up.
- Pilot misjudging altitude from a single-point readout.
- User misinterpreting an icon's meaning.

**Design responses**: clearer information presentation; trend / historical displays vs. point-in-time; reduce ambiguity in icons and labels.

#### Decision mistakes

Wrong choice under stress, bias, or overconfidence. Examples:

- Software engineer choosing a quick-fix that creates bigger problems.
- Medical professional anchoring on an initial diagnosis despite evidence.
- Designer ignoring user research that contradicts their intuition.

**Design responses**: decision trees, checklists, second-opinion mechanisms, training in error recovery.

#### Knowledge mistakes

Wrong action because of missing knowledge. Examples:

- New user not knowing how to use an unfamiliar tool.
- Operator unfamiliar with edge-case procedures.
- Visitor lost in a building they've never been in.

**Design responses**: memory aids, conventions and standards, training, simulations, accessible documentation, mnemonic devices.

## When to apply

- **Always**, on every design that involves user actions with consequences.
- **Especially** on destructive, irreversible, or high-stakes flows.
- **Critically** in safety-relevant domains (medical, aviation, financial, security).
- **In post-incident analysis** — every "user error" report should be examined for the design that invited it.

## Worked examples

### Example 1: preventing a common slip (wrong-recipient email)

The "send to wrong person" slip happens when the user types a recipient's name and the autocomplete suggests someone with a similar name; the user accepts on autopilot.

**Design responses**:

- **Distinct affordances** — show the recipient's full name, photo, and email when adding to To/Cc/Bcc.
- **Confirmation for high-stakes recipients** — Gmail prompts when sending to a new external recipient: "You've never emailed person@external.com before. Are you sure?"
- **Undo Send** — covers slips after they happen.
- **Reply-All caution** — extra prompt when replying to large groups.

```html
<!-- After clicking Send -->
<div class="undo-toast" role="status">
  Sending...
  <button onclick="cancelSend()">Undo</button>
</div>
<!-- After 5 seconds with no Undo, the message actually transmits. -->
```

### Example 2: preventing an attention slip (forgot the attachment)

Common slip: writing "see attached" in an email, then sending without attaching the file.

**Design response**: Gmail and most modern email clients scan the message body for words like "attached" or "attachment"; if found and no attachment exists, prompt before sending: "You wrote 'see attached' but didn't attach a file. Send anyway?"

A simple heuristic that catches a common slip before it commits.

### Example 3: preventing a perception mistake (misread chart)

A monitoring dashboard shows current CPU usage as a single number: "23%."

The user perceives "23%, fine" — but doesn't see that CPU has been climbing from 5% to 23% over the last hour. By the time they notice, the system is overloaded.

**Design response**: show trends, not just point-in-time values. A sparkline next to the number reveals the trajectory.

```html
<div class="metric">
  <p class="label">CPU usage</p>
  <p class="value">23%</p>
  <canvas class="sparkline" data-trend="up"></canvas>
  <p class="status status--warning">Trending up over last hour</p>
</div>
```

The same number; the perception is now of a trend, not an instant.

### Example 4: preventing a decision mistake (high-stakes destructive action)

A user clicks "Delete account." The decision is irreversible; making it under stress (frustration, time pressure) carries a high mistake risk.

**Design response**:

- **Type-to-confirm**: user must type their email to enable the destructive button.
- **Clear consequences**: list what will be lost (12 projects, 38 team-member access, 3.2 GB of files).
- **Recovery window**: account is soft-deleted for 30 days; user can restore.
- **Email confirmation**: post-delete email with a "Reactivate" link.

Multiple design layers turn a single decision into a deliberate process; each layer is a chance for the user to step back.

### Example 5: preventing a knowledge mistake (user doesn't know the procedure)

A user is troubleshooting their Wi-Fi. They don't know the steps.

**Design response**: a guided walkthrough that takes them step-by-step ("First, restart your router by unplugging it for 30 seconds. Then rejoin the network."). Each step shows an image of what to do.

The system provides the missing knowledge in real-time, eliminating the knowledge mistake before it can happen.

## Cross-domain examples

### Aviation

The aviation industry has driven much of modern human-error research. Key findings:

- Crew Resource Management (CRM) trains pilots and crew to challenge each other's decisions, reducing decision mistakes.
- Standardized checklists prevent skill-based slips (the canonical case Gawande analyzes).
- Flight-data recorders and cockpit voice recorders allow post-incident analysis to identify design patterns that contributed to errors.
- Sterile cockpit rule (no non-essential conversation below 10,000 ft) reduces attention slips during high-workload phases.

### Medicine

Medical errors are a leading cause of preventable harm. Patterns:

- Barcode medication administration (BCMA) prevents wrong-patient or wrong-drug slips.
- The Universal Protocol (mark site, time-out before incision) prevents wrong-site surgery slips.
- "Tall man lettering" for confusable drug names (DOPamine vs. DOBUTamine) reduces perception mistakes.
- Pre-procedure huddles allow cross-checking and reduce decision mistakes.

### Industrial control

Lockout-tagout procedures prevent slips by physically blocking accidental activation. Two-key authorization for hazardous operations prevents single-person decision mistakes. Dead-man switches detect operator incapacitation.

### Software

Modern software practice borrows heavily:

- **Type systems** prevent many slip-type errors at compile time.
- **Linters** flag common mistakes pre-commit.
- **Pre-deployment checklists** in CI/CD borrow from aviation.
- **Code review** introduces second-opinion challenge.
- **Canary releases** catch errors with limited blast radius before full rollout.

## Anti-patterns

- **Blaming the user for "human error."** The design invited the action; the user took it. Reframe.
- **Confirmation for everything.** Confirmation fatigue means real destructive confirmations get dismissed too. Reserve confirmation for genuine high-stakes irreversible actions.
- **Generic error messages.** "Validation failed" with no field highlighted, no fix suggested. The user can't recover.
- **Silent failures.** An action appears to succeed but actually fails; the error surfaces only later. Always close the feedback loop.
- **Treating slips and mistakes the same.** A confirmation prevents slips; better information prevents mistakes. Wrong tool for the wrong type fails.
- **Pre-selected destructive option.** A confirmation dialog with "Delete" as default Enter target. Slips become catastrophic.

## Heuristics

1. **The slip/mistake diagnosis.** For each user error, ask: did they intend the wrong thing (mistake) or unintendedly do the wrong thing (slip)? Different design fixes.
2. **The "what does the user know?" check.** Before assuming knowledge, ask what's the user actually likely to know? Mistakes flow from knowledge gaps.
3. **The recovery audit.** For each error, can the user recover? If yes, the cost is small. If no, prevention must be stronger.
4. **The post-incident review.** When an error happens, don't ask "who made the mistake"; ask "what design invited it?" Patterns emerge.
5. **The error-message audit.** Every error message should answer: what happened, why, what to do next.

## Related principles

- **`forgiveness`** — error recovery is the user-side complement.
- **`affordance`** — wrong actions become harder when affordances are clear.
- **`constraint`** — constraints structurally prevent wrong actions.
- **`confirmation`** — explicit verification step for high-stakes actions.
- **`feedback-loop`** — feedback lets users notice errors quickly.
- **`mental-model`** — mistakes flow from wrong models; better-aligned models reduce mistakes.
- **`expectation-effect`** — when actions don't match expectation, slips happen.

## Sub-aspect skills

- **`errors-slips`** — designing for execution errors (wrong actions despite right intent).
- **`errors-mistakes`** — designing for intention errors (right actions for wrong reasons).

## Closing

Errors are not failures of users; they are properties of designs. The most-used products in any category are usually those whose designers internalized this — they prevent what can be prevented, make recoverable what can't, and design error messages as if every user would encounter them. The investment is unglamorous and pays continuously across every user, every day.
