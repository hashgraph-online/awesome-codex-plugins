# Exploratory QA

Use this reference when the caller asks to explore a selected user journey or
rendered interface against accepted behavior. It adds observations to
[Test](../SKILL.md); it creates no new mode or required browser workflow.

## Bound the journey

Read the accepted promise, target route or public interface, expected endpoint,
permitted actions and relevant fixture or account state. A finding-only request
does not authorize repairs, account creation or browsing third-party systems.
Use the host's actual approved tools and existing access for the selected target.
Backend-only work can check its interface and durable state without a browser.

Establish an actual clean starting state for the journey: observe the current
route, session and records so old data or a cached result cannot impersonate the
new outcome. Clean means a known test state; it does not mean committing,
stashing or discarding someone else's work. If the necessary starting state is
unknown, report the dependent check as `not_checked` rather than assume it.

## Follow the promise to its endpoint

1. Name the accepted action and what its completion should make observable.
   Use the caller's examples and legitimate actor, inputs and permissions.
2. Observe the starting state, then perform the relevant journey actions through
   the selected interface. Record enough inputs and steps to reproduce a fault.
3. Observe intermediate errors and the action's immediate result. Keep the
   route, state and relevant viewport with each observation.
4. Independently read the promised durable endpoint after the action, using an
   authorized reload, fresh navigation, read API or stored-state query. This is
   a separate observation of the result, not a copy of the success message.
   For asynchronous work, use its stated completion condition and bounded wait.
5. Check the original accepted behavior and adjacent legitimate behavior that
   the journey could affect, such as reopening the saved record or cancelling
   another operation. Select these from the contract and changed surface.

If the durable endpoint cannot be inspected, state the observed immediate result
and mark persistence `not_checked`. An HTTP 200, screenshot or success toast
alone cannot prove that a record was saved or that a downstream action occurred.

## Observe only what the tools establish

Choose rendered states and viewports relevant to the accepted journey. Keep an
observation bound to its route, data/session state, viewport and tool capability;
a desktop pass says nothing about an unobserved mobile state.

- **Layout:** inspect whether the accepted controls and information remain
  usable in relevant viewports; capture the state that shows an obstruction.
- **Keyboard and accessibility:** exercise focus, activation and navigation with
  available host tools. Inspect accessible names or assistive behavior only when
  a tool can actually observe them; a screenshot cannot establish these facts.
- **Console and network:** use available approved observations to connect an
  error or failed request to the journey. A request's status alone does not
  establish the promised endpoint or explain the cause of a visible failure.

Missing browser, assistive or network capability stays `not_checked` for the
corresponding requested check. Do not claim simulated key presses prove a screen
reader result or install a new browser tool just to turn a gap into a pass.

## Classify the finding

A functional defect violates the accepted behavior. An accessibility obstruction
prevents a legitimate user from completing that behavior. A preference about
spacing, color or style is an optional taste suggestion unless an accepted
requirement makes it observable failure. Describe actual evidence; do not invent
bad designs, aggregate health scores or a cosmetic repair obligation.

Examples of discriminating observations:

- Create shows success, but a fresh authorized read after reload lacks the new
  record: the durable promise failed, even though the screenshot looked correct.
- On the relevant mobile viewport a control covers Submit, or keyboard focus
  cannot reach and activate that accepted action: report the observed obstruction
  and exact state. Unexamined viewports or assistive behavior remain unchecked.

Finish in the existing handoff with the promise, starting state, actions, durable
observation, route/viewport/tool bounds, reproduced defects and `not_checked`
gaps. Preserve useful evidence at the caller's selected destination only when
requested or required. Findings do not authorize repair, commits or delivery.
