# Locus of control — automation design patterns

A working catalog of patterns for designing automation that maintains the right locus of control, with notes on when each applies.

## Pattern: visible auto-action with undo

The system performs an action automatically and shows the user immediately what was done, with an undo affordance.

Example: Gmail's "Conversation moved to Trash. Undo." When the user archives or deletes by gesture, the action happens immediately and a toast offers undo. The locus is mostly external (the system did the action without asking) but the undo gives the user a window to reclaim internal locus.

This pattern works when:

- The action is reversible.
- The user can plausibly want to undo (because they triggered it accidentally or changed their mind).
- The toast is visible long enough to be noticed (typically 5–10 seconds).
- The undo is genuinely fast and reliable.

This pattern fails when the action is not actually reversible, or when the toast disappears too quickly, or when the user has multiple toasts stacking up and can't tell which undo applies to what.

## Pattern: suggestion with explicit accept

The system suggests an action; the user must explicitly accept (click, tap, key) to perform it. Internal locus is preserved.

Example: a code editor showing autocomplete options that the user can accept with Tab or ignore by typing. The suggestion is visible; the action is the user's.

This pattern works when:

- Suggestions are accurate enough to be worth showing.
- The accept gesture is fast and unambiguous.
- Ignoring the suggestion is also fast (the user can keep working past it).
- The user can dismiss persistent suggestions if they're unhelpful.

This pattern fails when suggestions are noisy (more wrong than right), when the accept gesture is hard to distinguish from other intended input, or when ignored suggestions block the user's work.

## Pattern: rule-based delegation

The user explicitly defines rules; the system executes them. Internal locus is preserved despite full automation, because the user authored the rule.

Example: email filters, Zapier-style automations, calendar booking rules. The user wrote "when X happens, do Y" — the system is acting on the user's pre-stated intent.

This pattern works when:

- Rules are easy to define for the user's actual cases.
- The user can review what the rules have done.
- Rules can be edited or disabled easily.
- Rules don't accumulate so many that the user loses track.

This pattern fails when rules become so numerous and inter-dependent that the user no longer understands what's happening, or when the rule language is too restrictive to express the cases the user actually has.

## Pattern: confidence-gated automation

The system acts automatically when confident; asks when uncertain. Locus shifts based on the system's certainty.

Example: a photo-tagging system that auto-tags faces it has seen many times before but asks for confirmation on new faces. A spam filter that auto-files highly confident spam but routes uncertain mail to a "needs review" folder.

This pattern works when:

- The system has a reliable measure of its own confidence.
- The user trusts the system's confidence assessment.
- The threshold is well-calibrated (not too permissive, not too cautious).
- The user can adjust the threshold if it's mis-set.

This pattern fails when the system's confidence is poorly calibrated, when it acts too aggressively on mistaken confidence, or when "needs review" piles up and overwhelms the user.

## Pattern: explicit invocation

The system does nothing without explicit user request. Maximum internal locus.

Example: most code editors' "format document" command. The formatter is available but doesn't run unless invoked. The user is in full control.

This pattern works when:

- The user knows the capability exists.
- The user can predict what will happen when they invoke it.
- The invocation is fast and discoverable.

This pattern fails when users don't know the capability is there, or when the cost of invocation is high enough that they'd rather do without than learn the command.

## Pattern: opt-in vs. opt-out automation

A meta-pattern: automation can be on by default with the option to disable, or off by default with the option to enable. The choice has large psychological consequences.

**Opt-out (on by default):** maximum convenience, but the user is in external locus by default. Most users never change defaults, so most users will use the system in external locus mode. Appropriate when the automation is reliably useful and the cost of being wrong is low.

**Opt-in (off by default):** maximum agency, but most users won't enable. Appropriate when the automation has meaningful tradeoffs that users should evaluate, or when the cost of being wrong is high.

Many products start opt-in (when launching a new automation) and shift to opt-out once the automation is proven and trusted.

## Pattern: revealing automation in the background

The system acts automatically but its actions are continuously visible in a background area — a log, a sidebar, a status indicator. The user can scan to see what's been happening.

Example: an IDE's git auto-commit indicator. A backup tool's "last sync at 3:42pm" status. An email client's "auto-archived 12 promotional emails" summary.

This pattern works when:

- The user's overall workflow is in the foreground; the automation is in the periphery.
- The user can audit what the automation has done if they want.
- The automation doesn't surface unless something is unusual or noteworthy.

This pattern fails when the indicator is hidden too well (the user never notices) or pushed too prominently (it interrupts the foreground work).

## Pattern: no-confidence question

When the system is uncertain enough that asking would be reasonable, but the user doesn't have the information to answer well either, sometimes the right move is to not act and not ask — just present the situation and let the user decide what to do next.

Example: a package manager finding a dependency conflict it can't auto-resolve. Rather than suggesting a fix it's not confident about, it shows the conflict and lets the user investigate.

This pattern works when:

- The system is honest about its uncertainty.
- The user has tools to investigate and decide.
- The system doesn't fall into the trap of asking unanswerable questions ("Is this conflict acceptable to you?" — the user doesn't know without investigation).

## Anti-patterns

**The "are you sure?" treadmill.** Confirming every action regardless of stakes. Users habituate and click through without reading. The friction is paid; the locus is not actually preserved (because the user is no longer making real decisions); and stakes are not actually weighted.

**Aggressive automation with no audit trail.** The system makes many decisions on the user's behalf and doesn't show any of them. The user is in pure external locus, with no ability to correct mistakes or learn the patterns.

**Inconsistent locus across surfaces.** A product that auto-saves in one place but requires explicit save in another. A product that auto-categorizes some data but asks the user to categorize other data. The user can't form a stable expectation, which is a worse experience than either consistent locus.

**Locus that changes based on undisclosed factors.** A product that auto-sends some emails but holds others for review based on criteria the user can't predict. The user doesn't know what to expect from the system and starts to mistrust it. Either the criteria should be disclosed or the locus should be consistent.

**Soft automation that pretends to be a choice.** Pre-checked checkboxes, pre-selected radio buttons, defaults presented with strong visual nudges that all but one option is wrong. The user feels they chose but the system actually decided. This is manipulative and erodes trust when noticed.

## A simple test

Ask a user "what does the system do automatically, and what do you have to tell it to do?" If they can answer clearly, your locus is well-designed. If they can't — if they're surprised by automated actions or don't realize they could automate things they're doing manually — the locus is unclear and likely costing you on both convenience and agency.

## Cross-reference

For the broader principle of how much control to give users, see `control`. For the structural mechanism of layering controls for mixed audiences, see `control-power-vs-simplicity`.
