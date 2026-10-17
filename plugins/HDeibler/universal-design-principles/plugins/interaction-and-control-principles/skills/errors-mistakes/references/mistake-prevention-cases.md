# Mistake prevention: cases and patterns reference

A reference complementing `errors-mistakes` with case studies and patterns.

## High-stakes mistake cases

### Three Mile Island (1979)

Operators at the Three Mile Island nuclear plant misperceived the state of a relief valve (perception mistake) — a stuck-open valve was indicated as closed by a status light that reflected only the command, not the valve's actual position. The misperception cascaded into the worst US nuclear accident.

Design fix: status indicators should reflect *actual* state, not commanded state. Apply to software: a "Save" indicator that turns green when the save succeeds, not when the request is sent.

### Air France 447 (2009)

Pilots experienced a perception mistake (mismatched airspeed readings) followed by a decision mistake (conflicting actions on the controls). The aircraft stalled into the ocean.

Design fix: when sensors disagree, the system should highlight the disagreement explicitly rather than displaying a single computed value that may be wrong.

### Mars Climate Orbiter (1999)

Engineering teams used different units (imperial vs. metric) — a knowledge mistake about the system's expected units. The orbiter burned up in the Martian atmosphere.

Design fix: explicit unit declaration; type systems that prevent unit-mismatch errors at compile time.

## Mistake-prevention patterns in software

### Surfacing mode

When the user is in a non-default mode (capslock, edit mode, dev mode, vim's command mode), the system displays the mode prominently. Without this, mode-confusion mistakes are common.

```html
<!-- Capslock indicator on password field -->
<div class="field" data-capslock="true">
  <input type="password" />
  <p class="hint">Caps Lock is on</p>
</div>
```

### Environment indicators

Multi-environment products (staging vs. production) should make the environment unmistakably visible:

```html
<header class="env-banner env-banner--staging">
  STAGING — actions don't affect customers
</header>
```

### Confirmation with explicit consequences

For high-stakes decisions, the confirmation dialog should spell out what will happen:

```
Delete project "Acme Q4"?

This will:
  • Delete 24 tasks
  • Remove 8 attachments (12 MB)
  • Revoke access for 3 collaborators

This action cannot be undone.
```

The user with a wrong model ("I think this is the test project") may notice the consequences don't match their expectation.

### Pre-deployment checklists

Software pre-deployment checklists borrow from aviation:

```
[ ] Tests passing
[ ] Migrations reviewed
[ ] Backwards-compatibility verified
[ ] Feature flags configured
[ ] Monitoring dashboards ready
[ ] Rollback plan documented
```

Each step prevents a common mistake. The checklist's effectiveness comes from its short, focused, pause-point structure.

### Decision support tools

For complex decisions, a decision tree or troubleshooting flow guides the user:

```
What's the symptom?
  ( ) Service is slow
  ( ) Errors in logs
  (•) Cannot connect

→ When did it start?
  (•) Just now
  ( ) Hours ago

→ Has anything changed?
  ( ) New deployment
  ( ) Config change
  (•) No recent changes

→ Likely causes: dependency timeout, network issue
```

## Cross-domain mistake-prevention

### Medicine: structured handoff (SBAR)

When transferring patient care between shifts, nurses use SBAR (Situation, Background, Assessment, Recommendation). The structured handoff prevents knowledge mistakes during transitions.

### Aviation: standardized callouts

"Gear down," "Flaps 30," "V1," "Rotate" — standardized callouts during critical phases of flight prevent perception and decision mistakes by externalizing system state.

### Software: design reviews

Code review and design review introduce second-opinion challenge. The reviewer brings a different mental model; mismatches surface as questions or pushback.

## Resources

- **Reason, J.** *Human Error* (1990).
- **Vaughan, D.** *The Challenger Launch Decision* (1996).
- **Casey, S.** *Set Phasers on Stun* (1998).
- **Norman, D.** *The Design of Everyday Things* (2013).
- **NTSB / aviation accident reports** — public; show how perception, decision, and knowledge mistakes cascade in high-stakes systems.
