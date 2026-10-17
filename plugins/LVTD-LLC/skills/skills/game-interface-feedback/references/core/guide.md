# Game Interface Feedback Guide

## Interface Model

For each player action, trace:

1. Player intention.
2. Available input.
3. System interpretation.
4. Immediate feedback.
5. State change.
6. Consequence feedback.
7. Next available decision.

Breakdowns usually happen when the player cannot predict what input is possible, cannot see whether the input registered, or cannot understand why the outcome happened.

## Feedback Rules

- Critical feedback should use more than one channel when possible.
- Feedback timing should match causality: immediate for input, quick for state change, clear for consequence.
- Feedback should expose enough system state for learning without overwhelming the screen.
- The player should be able to distinguish damage, reward, danger, affordance, cooldown, selection, focus, and invalid action.
- Repeated feedback should be tunable so it remains readable rather than noisy.

## Control And Mode Risks

- Same input means different things without visible mode change.
- Camera hides the target, hazard, or destination.
- HUD competes with the playfield.
- Menus interrupt action without preserving context.
- Tutorial prompts describe actions before the player needs them.
- UI state changes visually but not semantically for assistive technology.

## Accessibility Review

Check:

- remappable input
- hold versus toggle options
- readable text size and contrast
- non-color-only communication
- subtitle and caption coverage
- screen shake and flash controls
- timing-window assistance
- menu focus order and controller navigation
- alternatives for audio-only or visual-only information

## Source Notes

- Book source: Jesse Schell, *The Art of Game Design: A Book of Lenses, Third Edition*, chapter 15 (`https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059`).
- Usability reference: Nielsen Norman Group, "10 Usability Heuristics for User Interface Design" (`https://www.nngroup.com/articles/ten-usability-heuristics/`).
- Accessibility reference: Microsoft Xbox Accessibility Guidelines (`https://learn.microsoft.com/en-us/gaming/accessibility/guidelines`).
