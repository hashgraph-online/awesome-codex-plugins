# Flow design — checklist

A practical checklist for auditing a design against the conditions for flow.

## Goal clarity

- [ ] When the user opens the product, do they know what to do?
- [ ] Is the activity's goal explicit, or implicit but obvious?
- [ ] For multi-step activities, is each step's goal clear?
- [ ] Do users have ways to set their own goals when appropriate?

## Feedback immediacy

- [ ] Do user actions produce visible results within ~200ms?
- [ ] Are state changes animated smoothly to show what changed?
- [ ] Is there real-time validation where appropriate (typing, drawing, etc.)?
- [ ] Do error states surface quickly with clear messages?

## Challenge-skill calibration

- [ ] Does the product have layered depth so different skill levels can use it?
- [ ] Are there scaffolds for novices (defaults, guides, tutorials)?
- [ ] Are there capabilities for experts (customization, shortcuts, advanced features)?
- [ ] Is the difficulty appropriate for the user's actual skill level?
- [ ] Does the product adapt as skill grows (more capability becomes accessible)?

## Concentration support

- [ ] Is there a clear focal point on each screen?
- [ ] Is the chrome (sidebars, headers, etc.) minimal during deep activity?
- [ ] Are notifications deferred during the activity?
- [ ] Are interruptions (popups, banners) eliminated during the activity?
- [ ] Is there a "focus mode" or equivalent for deep work?

## Sense of control

- [ ] Does the user feel they're directing the activity?
- [ ] Are unexpected things avoided (the system doing things the user didn't ask for)?
- [ ] When the system does act automatically, is the action visible and undoable?
- [ ] Are settings and controls discoverable when needed?

## Self-consciousness reduction

- [ ] Are metrics about the user's performance hidden during the activity?
- [ ] Are social-comparison features minimized during the activity?
- [ ] Is the design quiet enough that users aren't reminded of being measured?

## Autotelic experience

- [ ] Is the activity itself rewarding, or framed in terms of external rewards?
- [ ] Are gamification elements (points, badges, streaks) thoughtful, or reflexive?
- [ ] Does the design respect the user's intrinsic motivation?

## Anti-pattern check

- [ ] No notifications during deep activity.
- [ ] No popups or modals during the activity.
- [ ] No live-updating metrics in peripheral vision during the activity.
- [ ] No social comparison shown during the activity.
- [ ] No latency that breaks immediate feedback.
- [ ] No streak penalties that create anxiety.
- [ ] No cluttered interface that competes for attention.
- [ ] No misaligned challenge (too easy or too hard for the audience).

## Specific design questions

**For tools:**
- Can a power user customize keybindings, shortcuts, defaults?
- Can a beginner get started without learning the customization?
- Is there a clear progression from beginner to expert use?

**For games:**
- Does difficulty adapt or offer adjustment?
- Are there clear short-term goals (the current level, the current quest)?
- Is feedback during play crisp (action-result connection clear)?

**For learning:**
- Are concepts scaffolded so each is achievable at the user's skill?
- Are there clear small wins along the path?
- Is feedback on practice exercises immediate?

**For creative work:**
- Is the canvas the focal point?
- Are tools accessible without dominating?
- Is there a "draft" mode for early-stage work?

**For reading:**
- Is the prose layout clean?
- Are interruptions during reading minimized?
- Is the typography comfortable for sustained reading?

**For meditation / reflection:**
- Is the session experience quiet?
- Are notifications suspended during the session?
- Does the design support sustained attention rather than fragmenting it?

## A simple test

Watch a user use the product for 30+ minutes. Note:

- Do they ever appear to enter a focused state (less head movement, less looking at peripheral things, sustained engagement with a single area)?
- What breaks the focused state (a notification, an unclear next step, a slow response)?
- Do they describe the experience afterward as engaging or fragmenting?

The observation is more reliable than self-report. Users in flow don't report it as such; they just describe the experience as good.

## Cross-reference

For the cost of distraction specifically, see `immersion-distraction-cost`. For the parent principle, see `immersion`.
