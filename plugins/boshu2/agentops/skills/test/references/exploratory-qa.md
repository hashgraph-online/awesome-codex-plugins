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

Attribute the running instance the same way. Take its address from its own
output, a printed tunnel origin or the caller rather than a predicted default
port, and confirm the process answering there serves the build under test: the
selected checkout's build, or the deployment the caller named. A server left running from another worktree or an older
build is no evidence about this change. Probe within a bounded wait, show logs
only from an instance this run started, and keep dependent checks `not_checked`
until the instance is attributed. Ask the caller before stopping an
unattributed process that holds the port.

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
   When the journey writes state, include the re-entry cases the contract or
   changed surface makes relevant (repeated submit, back or refresh mid-flow, a
   stale second tab, an expired session); a duplicate or lost input the
   accepted behavior does not allow is a finding.

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

Some steps belong to the caller: a provider sign-in, an inbox or SMS code, a
sandbox payment, a system permission prompt or a third-party console. Never
enter the caller's credentials. When the caller is present, name the single
step and what they should see, ask once, and continue from the state their
answer reports. Record that step as caller-observed, apart from what the tools
observed, and a reported problem as a finding in their words. An unanswered
step, or any such step in an unattended run, stays `not_checked` with its
reason, as do the checks that depend on it; check the rest of the journey
instead of waiting.

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
observation, route/viewport/tool bounds, reproduced defects, caller-observed
steps and `not_checked` gaps. Preserve useful evidence at the caller's selected
destination only when requested or required. Findings do not authorize repair,
commits or delivery.
