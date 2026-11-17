---
name: usability-check
description: "Evaluate user-facing interfaces against Nielsen's 10 Usability Heuristics. Complements /mycelium:service-check (Downe = service-level quality, Nielsen = interface-level quality)."
metadata:
  instruction_budget: "45"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Usability Heuristic Evaluation

Evaluate interface-level usability using Jakob Nielsen's 10 heuristics (1994; titles unchanged, definitions refined 2020). This complements Downe's 15 Good Services principles: Downe checks end-to-end SERVICE quality, Nielsen checks screen-level INTERFACE quality. Both are needed for user-facing work.

## When to Use
- During L4 Delivery for any user-facing work (REVIEW via G-V10)
- After UI implementation, before marking delivery complete
- When users report confusion or friction

## The 10 Heuristics

### 1. Visibility of System Status
The system should always keep users informed about what is going on through timely and appropriate feedback.
- [ ] Loading states visible for any operation > 1 second
- [ ] Progress indicators for multi-step processes
- [ ] Success/failure feedback for user actions
- [ ] Current location/state clearly indicated (breadcrumbs, active nav)

### 2. Match Between System and Real World
The system should speak the users' language, using familiar words, phrases, and concepts rather than system-oriented terms.
- [ ] No technical jargon in user-facing text
- [ ] Familiar icons and metaphors
- [ ] Information in natural, logical order
- [ ] Real-world conventions followed (calendar = dates, cart = shopping)

### 3. User Control and Freedom
Users often perform actions by mistake. They need a clearly marked "emergency exit" to leave the unwanted action.
- [ ] Undo/redo available for destructive actions
- [ ] Cancel option in all multi-step flows
- [ ] Back button works as expected
- [ ] Easy to return to a known state

### 4. Consistency and Standards
Users should not have to wonder whether different words, situations, or actions mean the same thing.
- [ ] Same action = same word everywhere (don't mix "delete" and "remove")
- [ ] Platform conventions followed (OS patterns, web standards)
- [ ] Internal consistency (same patterns across all screens)
- [ ] Visual consistency (colors, typography, spacing)

### 5. Error Prevention
Even better than good error messages is a careful design that prevents problems in the first place.
- [ ] Confirmation before destructive actions
- [ ] Constraints that prevent invalid input (date pickers vs free text)
- [ ] Disabled states for unavailable actions (not hidden, not error-on-click)
- [ ] Autosave or draft state for long forms

### 6. Recognition Rather Than Recall
Minimize the user's memory load by making elements, actions, and options visible.
- [ ] Recently used items visible/accessible
- [ ] Labels on icons (not icon-only buttons)
- [ ] Options visible in menus (not hidden behind gestures)
- [ ] Help text near complex fields

### 7. Flexibility and Efficiency of Use
Accelerators — unseen by the novice user — may speed up the interaction for the expert user.
- [ ] Keyboard shortcuts for frequent actions
- [ ] Search/filter for large lists
- [ ] Customizable settings for power users
- [ ] Both simple and advanced paths available

### 8. Aesthetic and Minimalist Design
Dialogues should not contain information that is irrelevant or rarely needed.
- [ ] Every element serves a purpose
- [ ] No decorative clutter competing with content
- [ ] Important information has visual priority
- [ ] Whitespace used to group and separate

### 9. Help Users Recognize, Diagnose, and Recover from Errors
Error messages should be expressed in plain language, precisely indicate the problem, and constructively suggest a solution.
- [ ] Error messages in plain language (not codes)
- [ ] Error messages say WHAT went wrong
- [ ] Error messages suggest HOW to fix it
- [ ] Errors visually connected to the field/action that caused them

### 10. Help and Documentation
Even though it is better if the system can be used without documentation, it may be necessary to provide help.
- [ ] Help is searchable
- [ ] Help is task-oriented (not feature-oriented)
- [ ] Help is concise and actionable
- [ ] Contextual help available where needed (tooltips, inline)

## Complementary: interaction & visual axioms (optional, nudge-only)

Nielsen's heuristics are diagnostic *principles*. They do not cover the quantitative interaction-design layer: Fitts's/Hick's target-and-choice math, Gestalt grouping (proximity, similarity, closure, common-region), typography (line-length/CPL, line-height, F-pattern scanning), and cognitive-load laws. If this project has a UI surface and the user wants that layer, the `haabe/ux-axioms-mcp` server covers it. *Per its README*, the server exposes ~44 such axioms with `analyze_ui` / `suggest_axioms` / `generate_spec` / `generate_tests` tools — confirm the current install/run path against the repo before recommending a specific setup command.

Mycelium **nudges, never installs**: offer it, let the user wire it up (per `${CLAUDE_PLUGIN_ROOT}/harness/design-principles.md` — autonomy/JIT-tooling). Don't double-surface — where a Nielsen heuristic and an axiom overlap (e.g. heuristic 4 Consistency ↔ Similarity; heuristic 8 Minimalist ↔ Occam's Razor), cite once. The persuasion axioms in that registry are dual-use; the same ethics line as anti-pattern #10 (Dark Pattern Marketing) applies.

## Output Format

```
## Usability Heuristic Evaluation

| Heuristic | Status | Issues |
|-----------|--------|--------|
| 1. Visibility of status | pass/partial/fail | ... |
| 2. Match real world | pass/partial/fail | ... |
| 3. User control & freedom | pass/partial/fail | ... |
| 4. Consistency & standards | pass/partial/fail | ... |
| 5. Error prevention | pass/partial/fail | ... |
| 6. Recognition > recall | pass/partial/fail | ... |
| 7. Flexibility & efficiency | pass/partial/fail | ... |
| 8. Aesthetic & minimal | pass/partial/fail | ... |
| 9. Error recovery | pass/partial/fail | ... |
| 10. Help & documentation | pass/partial/fail | ... |

Overall: [X]/10 passing
Priority fixes: [list most impactful issues]
```

## Theory Citations
- Nielsen: 10 Usability Heuristics for User Interface Design (1994)
- Downe: Good Services (complementary -- service-level, not interface-level)
