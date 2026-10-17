---
name: game-interface-feedback
description: Design or audit game controls, HUD, menus, feedback, input mapping, transparency, juiciness, channels, modes, and metaphors. Use when implementing UI, controls, camera, tutorials, status displays, accessibility feedback, or when players are confused about what happened.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Interface Feedback
  category: Game Development
  tags: game-design,ui,ux,controls,feedback,accessibility
---

# Game Interface Feedback

Use this skill to make player intent, system state, and consequences legible. The interface is not just menus; it is every path between player intention and game response.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapter 15 on interface, control, feedback, transparency, channels, modes, and metaphors. The workflow is transformed and paraphrased.

Supporting sources include Nielsen Norman Group usability heuristics and Microsoft Xbox Accessibility Guidelines.

## Workflow

1. Map player intent to input, game interpretation, feedback, and consequence.
2. Identify what the player must know before, during, and after each action.
3. Design feedback across visual, audio, haptic, animation, text, and spatial channels.
4. Check controls, HUD, menus, modes, camera, and tutorial prompts for conflict.
5. Add accessibility alternatives for critical information.

## Required Output

- `Interaction Map`: intent, input, system response, feedback, and failure states.
- `Feedback Spec`: channels, timing, priority, and accessibility alternatives.
- `UI/Control Notes`: HUD, menus, camera, prompts, focus, and mode behavior.
- `Implementation Tasks`: exact components, states, events, and tests.
- `Usability Risks`: ambiguity, hidden state, input conflict, overload, and missed feedback.

## Local References

Before producing an interface spec or audit, read:

- `references/core/guide.md`
- `workflows/interface-audit.md`
