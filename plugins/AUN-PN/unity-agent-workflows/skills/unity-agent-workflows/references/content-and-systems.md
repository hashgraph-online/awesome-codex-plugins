# Content And Systems

## Data-First Rule

Add new runtime/content behavior as data first when the repo has definition/config surfaces.

Use definitions/config for:

- level/step/session numbers, duration, pressure, unlocks
- entity/object HP, speed, score, size, tint, resistance, or availability
- actions/abilities/tools, cooldown, duration, radius, potency
- user/player/unit/support loadout and availability
- state effects, stack/refresh policy, duration bounds
- synergy rules
- localization keys and presentation identity

Add C# only when:

- a definition declares a behavior key that no runtime handler supports
- the content introduces a genuinely new runtime mechanic
- an existing service lacks the required integration seam

## System Stack For Production Readiness

When asked for broad "what is missing" or "finish the game systems" passes, verify live code first. High-value foundations often include:

- Analytics/telemetry.
- First-run/onboarding.
- Adaptive difficulty/relief.
- Missions/objectives.
- Status effects/resistance.
- Skill + support-unit synergy.
- Stage mastery/progression.
- Save migration/cloud-ready snapshots.
- Accessibility/haptics/reduced motion.
- Runtime performance/adaptive visual budget.

Do not add all of these blindly. Mark a phase complete only when a live owner exists under the correct layer and has runtime path, gateway, event, persistence, or UI proof.

## Thin System Slice

For a missing foundation, add the smallest useful owner:

1. Contract/gateway in the repo's existing contract/event/gateway boundary.
2. Runtime service in the repo's existing service/system/runtime owner path.
3. Thin feature hook beside the feature that already knows the runtime fact.
4. Event or bridge route instead of a direct feature reference.
5. Architecture docs/asmdef sync if dependency structure changes.

## Runtime Experience Pattern

For level/session pacing, tutorials, objectives, and difficulty shaping, prefer a thin planning layer:

```text
Content config/data
-> RuntimeExperiencePlan
-> director/adaptive relief/objectives/analytics
```

The planner should feed existing seams instead of growing the main manager, controller, or scene owner.

## Runtime State Step Guard

Use this for tutorials, onboarding, objectives, unlocks, quests, guided selection/action flows, navigation gates, and any user-visible state machine.

Never collapse these states into one boolean unless the live design already proves they are identical:

```text
shown != clicked != opened != selected != applied != completed != persisted
```

### Guided Flow State Proof

For guided selection/action, tutorial, onboarding, objective, or navigation flows, treat every state-step as separately provable:

- `shown`: prompt, overlay, marker, or instruction is visible.
- `clicked`: user clicked/tapped the prompt, target, or navigation control.
- `opened`: screen, panel, inventory, selection view, or section became active.
- `selected`: a domain item/option/card/loadout entry is selected.
- `applied`: selected action/value was applied to the active runtime owner.
- `completed`: the guided objective/step is marked done by the flow owner.
- `persisted`: completion or domain state is written to the save/progression store.

Opening a screen, recording a click, logging analytics, or showing the next prompt is interaction/navigation proof only. It is not proof that an item was selected, an action was applied, a tutorial/objective step was completed, or the result was persisted.

Before editing a state transition, prove:

```text
visible prompt/state:
user action:
screen/section opened:
domain action completed:
completion/persistence key:
old-save/default-content path:
already-done path:
reset/new-install path:
analytics-only path:
runtime writer/refresh path:
validation:
```

Patch the owner that actually advances domain state or persistence, and keep UI presenters presentation-only when the repo already has a service/gateway/contract layer.

## Balance Pass Rules

- Read current data/config and runtime override paths before changing values.
- Include user/player capability, action/tool power, support systems, economy, and pacing in broad balance passes.
- Make small targeted changes unless the user explicitly asks for a broad rebalance.
- Report exact constants/assets changed.
- Re-scan after broad localization or balance sweeps until the next search is clean or remaining items are out of scope.
