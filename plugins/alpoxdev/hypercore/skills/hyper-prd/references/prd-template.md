# PRD Template

Use this reference when creating or restructuring `prd.md`. It owns the section order, the skeleton, and one worked example.

## Contents

- Section order
- Skeleton
- Worked example
- Release gate table
- Data collection matrix
- Rules

## Section order

1. Meta: status, platforms, size, questions asked of the budget, sources read, updated
2. One-line definition
3. Problem and evidence
4. Target users and explicit exclusions
5. Goals and metrics
6. Scope: P1/P2/P3 stories, non-goals, must-not-change behavior
7. Functional requirements
8. Acceptance scenarios
9. Platform requirements: one block per decided platform, a release gate table in each block, and the shared data collection matrix when both `ios` and `android` are targets
10. Assumptions
11. Open questions
12. Risks and dependencies
13. Change history
14. Handoff block

Delete a section that does not apply. Never keep a heading without content, and never write `N/A`.

## Skeleton

```markdown
# <Product or feature name> PRD

## Meta

- Status: draft | ready | revised
- Platforms: web | ios | android | desktop (one or more) - <one-line reason for the decision>
- Size: S | M | L - <one-line reason for the decision>
- Questions: <asked>/<budget>
- Sources read: <repository paths, documents, and pasted context read before the first question>
- Updated: YYYY-MM-DD

## Definition

<One sentence. What this is, for whom, and what changes.>

## Problem and evidence

- One concrete case: <who, when, what happened, with real values>
- Current alternative: <what people do today instead>
- Evidence grade: observed | reported | assumed

## Target users and exclusions

- Users: <the people this serves, specifically>
- Excluded: <who this deliberately does not serve>

## Goals and metrics

| Goal | Metric | Target | Measurement means | Measurement time |
|---|---|---|---|---|
| <goal> | <primary metric> | <number + unit> | <where the number comes from> | <window> |
| <goal> | <secondary metric> | <number + unit> | <source> | <window> |
| <goal> | <counter-metric> | <floor + unit> | <source> | <window> |

## Scope

### P1 - <story name>

- Priority reason: <why now, what breaks if it slips>
- Independent test: <how this story alone is proven>
- Requirements: FR-001, FR-002

### P2 - <story name>

- Priority reason: <...>
- Independent test: <...>
- Requirements: FR-003

### P3 - <story name>

- Priority reason: <...>
- Independent test: <...>
- Requirements: FR-004

### Non-goals

- <A thing this deliberately does not do, and what it would have added>
- <A second thing, cutting a different part of the scope>

### Must not change

- FR-010 WHEN <existing condition>, the system SHALL CONTINUE TO <existing behavior>.

## Functional requirements

| Id | Priority | Requirement | Verification |
|---|---|---|---|
| FR-001 | P0 | <EARS sentence> | <what a reviewer does and sees> |
| FR-002 | P1 | <EARS sentence> | <...> |

## Acceptance scenarios

### <Story name>

```text
Scenario: <happy path name> (FR-001, FR-002)
Given <concrete starting state>
When <one action>
Then <observable outcome>

Scenario: <failure or edge name> (FR-002)
Given <concrete starting state>
When <one action>
Then <observable outcome>
```

## Platform requirements

### web

<One block per decided platform, in the order the platforms were decided. Name the checklist file the block was filled from. A platform that was not decided gets no block and its checklist is never read.>

#### Release gate

| ID | Grade | Item | Conclusion | Evidence | Re-check |
|---|---|---|---|---|---|
| W5 | `[M-조건]` | <the item sentence, short form> | applies, or not applicable with the condition, or `[확인 필요: <question>]` | <document, screen, or measurement that settles it> | <the date the dated value is checked again, or `none`> |
| W6 | `[M-조건]` | <...> | <...> | <...> | <...> |
| W1 | `[G]` | <only when relevant to this product> | <...> | <...> | <...> |

### Data collection matrix (ios and android)

Write this once, inside the platform requirements section and outside any single platform block, only when the decided platforms include both `ios` and `android`.

| Data type | Collected | Shared with third parties | Linked to the user's identity | Used for tracking | Purpose | Optional | Ephemeral |
|---|---|---|---|---|---|---|---|
| <e.g. email address> | yes | no | yes | no | account sign-in | no | no |
| <e.g. coarse location> | no | - | - | - | not collected; named so both stores agree | - | - |

Apple privacy label view: <which rows of the table map to which App Privacy label data types, and what the label says for each>.

Play Data safety view: <which rows map to which Data safety data types, and what the declaration says for each, including "no data collected" when that is the answer>.

- The matrix is written once. The App Privacy label (`I4`) and the Play Data safety declaration (`A2`, `A3`) both read from it; neither restates the data types from memory.
- A data type one platform handles and the other does not is a product decision: record the difference and its reason next to the matrix.

## Assumptions

- A-001: <statement>
  - Evidence grade: repo fact | convention default | guess
  - Basis: <path, quote, or convention>
  - If wrong: <what changes>

## Open questions

- Q-001: <question>
  - Answerer: <role>
  - Blocking: yes | no
  - History: Q: <question> → A: <answer or unanswered>

## Risks and dependencies

- Risk: <what could fail, and the early signal>
- Dependency: <what this needs from outside this document>

## Change history

| Date | Mode | What changed |
|---|---|---|
| YYYY-MM-DD | create | Initial document |

## Handoff

- Platforms: <decided platforms>
- Size: <S | M | L>
- P1 scope: <the stories and requirements that ship first>
- Remaining blocking questions: <Q ids, or "none">
- Inputs for the next stage: <what the next stage reads from this document>
```

## Worked example

```markdown
# Focus Timer PRD

## Meta

- Status: draft
- Platforms: ios, android - the support thread reports a phone timer, and the request names both stores
- Size: S - one screen and one behavior change on a new single-purpose app
- Questions: 1/1
- Sources read: the support thread quoted in Problem and evidence; no repository documents (new product)
- Updated: 2026-11-07

## Definition

A single-purpose focus timer that starts a fixed session and blocks mid-session edits, for people who lose the thread when a timer is too configurable.

## Problem and evidence

- One concrete case: a support thread on 2026-10-28 reports a user restarting a 25-minute session four times because the settings screen offered six duration presets mid-session.
- Current alternative: a general timer app plus a paper note of the intended duration.
- Evidence grade: reported

## Target users and exclusions

- Users: individual knowledge workers who run several short focus blocks a day
- Excluded: teams needing shared session dashboards; people who need interval or pomodoro chaining

## Goals and metrics

| Goal | Metric | Target | Measurement means | Measurement time |
|---|---|---|---|---|
| A session runs to completion | completed-session rate | 70% or more of started sessions | session start and end events | first 14 days after release |
| Sessions start fast | median time from app open to session start | 5 seconds or less | start-timestamp event pairs | first 14 days after release |
| The block does not cost the rest of the app | crash-free session rate | 99.5% or more (counter-metric floor) | crash report per session | first 30 days after release |

## Scope

### P1 - Start and finish one session

- Priority reason: without a run-to-completion path there is no product; nothing else is measurable.
- Independent test: start a 25-minute session, background the app, return after 25 minutes, see the completion state.
- Requirements: FR-001, FR-002, FR-010

### P2 - Resume after an interruption

- Priority reason: a killed process is the most common way a session dies; shipping resume doubles the useful sessions.
- Independent test: force-quit mid-session, relaunch, see the remaining time restored.
- Requirements: FR-003

### Non-goals

- Preset library and custom duration authoring: would add a settings surface and a second mental model for the same 25 minutes.
- Cross-device session sync: would add an account and a server dependency that the single-device case does not need.
- Paid tier: a subscription or one-off purchase would add store billing, a price surface, and an entitlement state the free timer does not need.

### Must not change

- FR-010 WHEN the app returns from the background during a session, the system SHALL CONTINUE TO show the remaining time without restarting the session.

## Functional requirements

| Id | Priority | Requirement | Verification |
|---|---|---|---|
| FR-001 | P0 | WHEN the user starts a session, the timer SHALL begin counting down from the fixed duration and show the remaining time. | Start a session; the remaining time decreases each second. |
| FR-002 | P0 | IF the session reaches zero, THEN the timer SHALL show the completion state and stop counting. | Run a one-minute test session to zero; the completion state appears and the count stops. |
| FR-003 | P1 | WHEN the process is killed mid-session and relaunched within 24 hours, the timer SHALL restore the remaining time. [가정: users return within a day] | Kill the process at 10 minutes remaining, relaunch, see 10 minutes. |
| FR-004 | P1 | WHERE the device is in silent mode, the completion state SHALL appear without an audible alert yet still show a visible banner. [확인 필요: is a haptic required by the design review?] | Enable silent mode, run to zero, see the banner and no sound. |
| FR-010 | P1 | WHEN the app returns from the background during a session, the system SHALL CONTINUE TO show the remaining time without restarting the session. | Background the app mid-session for two minutes, return, and see the countdown continue from the reduced remaining time. |

## Acceptance scenarios

### Start and finish one session

```text
Scenario: session runs to completion (FR-001, FR-002)
Given a fresh install with no session in progress
When the user taps Start and waits 25 minutes
Then the completion state is shown and no countdown remains

Scenario: session survives a background return (FR-001, FR-010)
Given a session started 10 minutes ago
When the user backgrounds the app for two minutes and returns
Then the remaining time shows about 13 minutes and the session is still running
```

### Resume after an interruption

```text
Scenario: a force-quit restores the remaining time (FR-003)
Given a session with 10 minutes remaining
When the user force-quits the app and relaunches within 24 hours
Then the timer shows the restored remaining time and keeps counting

Scenario: a relaunch outside the window starts a new session (FR-003)
Given a session that ended 25 hours ago
When the user relaunches the app
Then no session is restored and the start state is shown
```

## Platform requirements

### ios

Filled from `references/platforms/ios.md`.

#### Release gate

| ID | Grade | Item | Conclusion | Evidence | Re-check |
|---|---|---|---|---|---|
| I1 | `[M-조건]` | In-app account deletion under 5.1.1(v) | not applicable - the app creates no account and has no sign-in, so 5.1.1(v) has no subject | product scope above: no account, no sync | 2027-02-07 |
| I2 | `[M-조건]` | In-app purchase under 3.1.1 | not applicable - no paid digital goods or services | non-goals: no paid tier | 2027-02-07 |
| I3 | `[M-조건]` | Subscription terms under 3.1.2 | not applicable - no subscription | non-goals: no paid tier | 2027-02-07 |
| I4 | `[M]` | App Privacy label for every data type the release handles | applies - session events and crash reports, neither linked to identity nor used for tracking; the label reads from the data collection matrix below | data collection matrix | 2027-02-07 |
| I5 | `[M]` | Privacy manifest content and its owner | applies - manifest lists the same data types as the label, no tracking domains, owner is the release owner | data collection matrix | 2027-02-07 |
| I6 | `[M-조건]` | Review demo account under 2.1 | not applicable - no sign-in, so the reviewer needs no credentials | product scope: no account | 2027-02-07 |
| I7 | `[M]` | Minimum functionality under 4.2 and 4.2.2 | applies - the timer, its session state, and its completion state are the app's own function, not a repackaged site or a link collection | scope P1 | 2027-02-07 |
| I8 | `[G]` | Notification permission request in context | applies - the completion alert asks on first session start, with one sentence naming the timer | scope P1 | 2027-02-07 |

### android

Filled from `references/platforms/android.md`.

#### Release gate

| ID | Grade | Item | Conclusion | Evidence | Re-check |
|---|---|---|---|---|---|
| A1 | `[M]` | Target API level of the release | applies - the release targets API level 36, the floor in force from 2026-08-31 | build config at release time | 2027-02-07 |
| A2 | `[M]` | Play Data safety declaration | applies - the declaration is written from the data collection matrix below | data collection matrix | 2027-02-07 |
| A3 | `[M]` | Per-type collected, shared, purpose, optional, ephemeral | applies - session events and crash reports, not shared, not optional, not ephemeral | data collection matrix | 2027-02-07 |
| A4 | `[M]` | Permission list limited to promoted current features | applies - the notification permission serves the completion alert promoted in the listing | scope P1 | 2027-02-07 |
| A5 | `[M]` | Permission-to-feature mapping table | applies - one row: notification permission, completion alert, listing screenshot 2, asked on first session start | store listing plan | 2027-02-07 |
| A6 | `[M-조건]` | Sensitive or restricted permission declaration | not applicable - the release requests no sensitive or restricted permission | permission list above | 2027-02-07 |
| A7 | `[M-조건]` | Play billing for digital goods | not applicable - no digital goods are sold | non-goals: no paid tier | 2027-02-07 |
| A8 | `[M-조건]` | Play Billing library version | not applicable - the app does not use Play Billing | non-goals: no paid tier | 2027-02-07 |
| A9 | `[M]` | Published artifact format | applies - an Android App Bundle is uploaded, with no delivery split relied on | build config at release time | 2027-02-07 |
| A10 | `[G]` | Stability floor read from Android vitals | applies - the counter-metric reads user-perceived crash rate below 1.09% and ANR rate below 0.47%, per app version, in Play Console | goal 3 in the metrics table | 2027-02-07 |
| A11 | `[G]` | Interactive touch targets at 48 dp or more | applies - the start and stop controls are measured at 56 dp on one compact and one large screen | layout inspection record | 2027-02-07 |

### Data collection matrix (ios and android)

| Data type | Collected | Shared with third parties | Linked to the user's identity | Used for tracking | Purpose | Optional | Ephemeral |
|---|---|---|---|---|---|---|---|
| Session start and end events | yes | no | no | no | measuring the completed-session rate | no | no |
| Crash reports | yes | no | no | no | stability | no | no |
| Account identifiers | no | - | - | - | no account exists | - | - |
| Precise location | no | - | - | - | not requested | - | - |

Apple privacy label view: session events and crash reports are declared as usage and diagnostics, not linked to identity, not used for tracking; the label names no other type.

Play Data safety view: the same two types are declared as collected, not shared, not optional, not ephemeral; the declaration names no other type and does not claim "no data collected".

## Assumptions

- A-001: users accept a fixed 25-minute duration with no in-session settings
  - Evidence grade: convention default
  - Basis: the cited support thread is about too many presets
  - If wrong: P1 gains a duration choice and the settings non-goal is removed

## Open questions

- Q-001: does the design review require a haptic on completion?
  - Answerer: design
  - Blocking: no
  - History: Q: is a haptic required? → A: unanswered

## Risks and dependencies

- Risk: background execution limits stop the countdown; the early signal is a session that jumps on return.
- Dependency: the store listing needs the final duration copy before submission.

## Change history

| Date | Mode | What changed |
|---|---|---|
| 2026-11-07 | create | Initial document |

## Handoff

- Platforms: ios, android
- Size: S
- P1 scope: FR-001, FR-002, FR-010 with the start-and-finish story
- Remaining blocking questions: none
- Inputs for the next stage: the fixed duration, the completion state, the resume window, the iOS and Android release gate tables, and the shared data collection matrix
```

## Release gate table

One table per decided platform block, filled from that platform's checklist file.

| Column | Content |
|---|---|
| ID | The checklist item id, for example `I1` or `A2` |
| Grade | The grade copied from the checklist, unaltered: `[M]`, `[M-조건]`, `[G]` |
| Item | The obligation in one short sentence, with the threshold, measurement method, and percentile for a numeric item |
| Conclusion | `applies`, `not applicable` with the condition or reason, or `[확인 필요: <question>]` |
| Evidence | The document, console screen, or measurement that settles the conclusion |
| Re-check | The date the dated value is checked again, or `none` for an item with no dated value |

- Every `[M]` and `[M-조건]` item of the loaded checklist gets a row. A `[M-조건]` row whose condition is false reads "not applicable" with the reason; the row does not disappear.
- A `[G]` item gets a row only when it is relevant to this product.
- A `[M]` row left at `[확인 필요]` keeps the document at `status: draft`. That row is not counted toward the three-marker cap, which applies to inline markers in the prose sections.
- A store obligation is written as the clause plus the observable state the clause requires. "Follow the store guidelines" is not a conclusion.

## Data collection matrix

One matrix for the document, written only when the decided platforms include both `ios` and `android`.

| Column | Content |
|---|---|
| Data type | The data category, in the words the store forms use |
| Collected | `yes` or `no` |
| Shared with third parties | `yes` or `no`, with the recipient when `yes` |
| Linked to the user's identity | `yes` or `no` |
| Used for tracking | `yes` or `no` |
| Purpose | Why the release handles it |
| Optional | `yes` or `no`: whether the user may decline to provide the data and still use the feature |
| Ephemeral | `yes` or `no`: whether the data is processed only in transit and never stored |

- The matrix is written once. The App Privacy label and the Play Data safety declaration both read from it; neither restates the data types from memory.
- A type one platform handles and the other does not is a product decision: record the difference and its reason next to the matrix.
- A type the release handles but the matrix omits is a defect in the matrix, fixed before either store form is filled.

## Rules

- Copy the skeleton's section names exactly; they are the names a reviewer checks.
- The meta block carries the platform decision and the size decision, each with its one-line reason on the same line, for example `Platforms: web, ios - the request names a browser product and an App Store release`.
- Delete every placeholder you cannot fill with a fact, an assumption, or a marker. An empty section is a defect, not a template artifact.
- A `[가정: …]` that changes scope appears again as an `A-###` entry; a `[확인 필요: …]` that blocks scope becomes a `Q-###` with `Blocking: yes`.
- Every story gets one happy-path and one failure-or-edge scenario, so two stories produce four scenarios.
- Every decided platform block carries a release gate table. Every `[M]` and `[M-조건]` item of that platform's checklist gets a row with a conclusion; `[G]` items appear only when relevant.
- A numeric gate item states its threshold, its measurement method, and its percentile in the same cell.
- When `ios` and `android` are both decided, the data collection matrix is written once for the document, with the Apple privacy label view and the Play Data safety view derived from it.
- A store obligation is written as the clause plus the observable state the clause requires. A sentence that says to follow the guidelines without naming the clause and the state is not a requirement.
- At most three `[확인 필요: …]` markers in the whole document. This cap counts inline markers in the prose sections; a `[확인 필요: <question>]` that stands as a release gate table's conclusion is excluded from the count, and the document stays `status: draft` while any gate row is `[확인 필요]`.
- The handoff block is the only place the next stage's inputs are described; this document never contains a task list, a design, or a flow.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| One document as the canonical artifact, with a short question budget | [snarktank/ai-dev-tasks create-prd](https://raw.githubusercontent.com/snarktank/ai-dev-tasks/main/create-prd.md) - "Limit questions to 3-5 critical gaps in understanding." |
| Removing a non-applicable section instead of writing N/A | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "When a section doesn't apply, remove it entirely (don't leave as 'N/A')." |
| Independently testable stories and numbered requirements | [spec-kit spec-template](https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md) - "Each user story/journey must be INDEPENDENTLY TESTABLE" |
| The WHEN/SHALL requirement sentence | [Kiro feature specs](https://kiro.dev/docs/specs/feature-specs.md) - "WHEN [condition/event] THE SYSTEM SHALL [expected behavior]" |
| State and unwanted-event requirement forms | [EARS](https://alistairmavin.com/ears/) |
| `SHALL CONTINUE TO` for unchanged behavior | [Kiro bugfix specs](https://kiro.dev/docs/specs/bugfix-specs.md) - "WHEN [condition] THEN the system SHALL CONTINUE TO [existing behavior]" |
| Inline markers at the gap | [deanpeters prd-development](https://github.com/deanpeters/Product-Manager-Skills) - "Tag inline where the gap appears, not just at the end." |
| Assumptions and open questions kept out of the body as fact | [phuryn create-prd](https://github.com/phuryn/pm-skills) - "Don't invent. What you don't know goes to 7.4 Assumptions and open questions, clearly marked, not into the body as fact." |
| Counter-metrics in the metric set | [TerminalSkills prd-writing](https://github.com/TerminalSkills/skills) - "Counter-metrics: [Metrics we don't want to hurt]" |
| A handoff block at the end of the document | [Citadel prd](https://github.com/SethGammon/Citadel) |
| One data inventory that both store privacy forms read from | [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/) - "This information is required to submit new apps and app updates to the App Store."; [Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) - "Even developers with apps that do not collect any user data must complete this form" |
| No-naming of the internal build mechanism | [ai-conductor prd](https://github.com/jstoup111/ai-conductor) - "It MUST NOT name the new internal mechanism by which this feature is built." |

### Evidence grade

`LOCAL` - the section order and the worked example are this package's design. The sentence forms are quoted from the EARS and Kiro documentation; the marker and assumption rules are adapted from the cited guidance.
