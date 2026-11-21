# Reachable states and representative stress fixtures

Inventory the component's actual inputs and branches before selecting cases.
Use product vocabulary and give every case a stable fixture ID. Record the
source branch or prop that makes the case reachable. An absent expected state
is a finding or coverage gap, not permission to invent product behavior.

| Dimension | When it applies | Representative cases and evidence |
|---|---|---|
| Data | Component receives async or repeated data | Loading held pending, zero, one, typical count, plausible large count, partial/stale result; verify the displayed fixture is the selected one. |
| Completion | A local action changes state | Idle, submitting, success, recoverable error, retry, repeated activation; exercise the real handler through its non-mutating adapter. |
| Access | Component reads roles, plans, flags, or limits | Allowed, member without access, disabled/locked, expired or limit reached; verify inaccessible actions produce no adapter call. |
| Text length | Component accepts variable text | Empty, short, typical, several lines, realistic long unbroken value; preserve fixed approved labels and claims. |
| Locale/content | Supported content can contain these forms | Diacritics, emoji, mixed direction, long translations, large numbers and date formats; use supported locales without claiming untested localization. |
| Container | Every component | Actual desktop and mobile viewport, constrained parent, supported narrow width; viewport behavior and container behavior are separate checks. |
| Interaction | Interactive controls | Tab/Shift+Tab, visible focus, activation, validation, disabled behavior, hover where meaningful, recovery and focus return. |
| Environment | Supported by project/platform | Zoom/reflow, reduced motion, existing light/dark themes; use real theme selectors rather than redeclaring tokens in the harness. |

Start with the smallest set that covers meaningful branches and the primary
task. Combine dimensions when production can reach the combination, such as
an access-denied mobile view or an error containing a long server message.
Do not use a blind Cartesian product. Document omitted axes and why they do
not apply so an incomplete fixture is not mistaken for full coverage.

## State record

For each case record:

- Fixture ID, domain name, source path/branch, and synthetic inputs.
- Expected action or recovery, preserved content, and isolated adapter result.
- Viewport dimensions, relevant theme/locale, and keyboard/pointer sequence.
- Observed result, screenshot or trace path, and source-only/unverified gaps.

A screenshot shows a frame. A transition claim additionally needs the action
and resulting state. A disabled visual treatment needs a keyboard/activation
check; a permission fixture needs evidence that no protected action ran.

## Workbench controls

Use a labeled native select or grouped controls suited to the number of states.
Indicate the selected value accessibly, allow normal Tab navigation, and keep
the fixture identifier deterministic. A state link must contain only a local
fixture ID, not arbitrary data or a target URL. Reject unknown IDs instead of
falling back to production data. Reset local mock history when changing cases.

Keep controls outside the measured component. At narrow widths put them above
the stage without overlaying actions or focus. Hide them for captures only if
the fixture ID remains in the evidence manifest. Verify that a resize does not
change the selected case or reintroduce live providers. Avoid global shortcuts;
if useful, ignore input/editable targets, modifiers, and handled events.

## Worked contract: reservation workbench

An existing reservation component accepts available times, a status, an access
flag, and an action callback. Import it unchanged. Supply synthetic slots at
fixed dates and replace its reservation callback with an in-memory recorder.
Keep available, loading, empty, failed, confirmed, disabled, and
member-without-access cases as distinct fixtures only where those inputs or
branches exist.

At representative desktop and mobile sizes, inspect each state and Tab through
reachable controls. Invoke the available state's reservation action locally;
assert the recorded slot and inspect whether the actual component transitions.
Verify zero calls in denied and disabled cases. Inspect long time-zone labels
and error recovery without changing the approved offer. If confirmed is only
reachable as a supplied prop, report its visual render separately from the
unverified submission-to-confirmation transition.

If a state is blank because the fixture is lost in a server/client boundary,
repair the harness. If the real component accepts the fixture but still fails,
report the component defect. Fix it only when authorized, then recapture the
same cases and any adjacent states affected by the change.
