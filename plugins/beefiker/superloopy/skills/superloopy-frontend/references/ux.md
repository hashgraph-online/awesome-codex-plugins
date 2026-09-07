# Shared UX Contract

Use this reference once for every supported screen-based application UI route. It defines user-facing truth, implementation traceability, and proportional evidence; platform, shell, renderer, Web, and Qt references add their own ownership rules.

## Five-stage workflow

1. **Baseline and frame the delta.** Reproduce the current-state journey on a representative target before proposing changes. Locate the existing component, state owner, command or service owner, and tests. Name the affected users, job, desired outcome, affected journey, and adjacent journey that could regress. Mark every material statement as evidence, assumption, or unknown and record confidence.
2. **Map users, journeys, and capabilities.** Trace entry, action, system response, recovery, and exit. Inventory the capabilities and owners at every step. Apply the risk-gated user coverage matrix below; do not turn one report or an assumed persona into a universal requirement.
3. **Specify behavior, states, and invariants.** Define semantic results, operating states, failure truth, content, editable-text behavior, accessibility, adaptation, persistence, and privacy boundaries before polishing appearance.
4. **Trace implementation and choose claim-shaped evidence.** Maintain one row per material change: `contract clause or invariant -> acceptance case or criterion -> implementation owner and file -> test -> evidence artifact`. A requirement without an implementation and proof path is incomplete.
5. **Promote capability by capability.** Match each claim to the narrowest evidence that proves it on the actual target. Move simulated work toward production only with new real-target evidence for that capability; a neighboring proven capability does not promote it.

## Proportional artifacts

`UX_CONTRACT.md` is required for an expanded journey and for a new/redesigned/high-consequence surface; a narrow fix uses the compact evidence below.

- **Narrow fix:** record the UX delta, affected journey, adjacent journey regression risk, and behavioral, accessibility, and regression evidence in the existing receipt. For a narrow nonvisual change, record `Design impact: unchanged` and `Visual evidence: not applicable` with reasons; neither a new design-system artifact nor `VISUAL_QA.md` is required. If behavior also does not change, record `UX impact: unchanged` and why.
- **Expanded journey:** write a scoped `UX_CONTRACT.md` with the baseline, journey, user coverage, capabilities, owners, operating states, invariants, traceability rows, risks, and evidence matrix.
- **New/redesigned/high-consequence surface:** write `UX_CONTRACT.md` with fuller discovery, content, accessibility, localization, adaptation, privacy, usability, and promotion evidence.

Do not demand exhaustive personas, every-route screenshots, or a new design-system artifact for a narrow change whose risk does not justify them. Visual artifacts are conditional on visual claims; behavioral and accessibility claims require their own evidence.

## High-impact decisions and genuine alternatives

A high-impact judgment is one that can approve, block, redirect, or materially expand implementation; change information architecture, capability reachability, accessibility, user coverage, dependency, or design authority; or assert that a result is usable, clear, better, premium, or otherwise successful for people. Ordinary descriptive prose and mechanical conformance to an existing contract are not high-impact decisions.

Use a compact record for a narrow judgment: `decision -> affected user/task/target -> authority or criteria -> selected option -> warrant and evidence -> limitation or counterexample`. Add alternatives and tradeoffs only when more than one plausible option was genuinely considered. When the existing authoritative source fixes the result, record `Alternatives: not applicable — existing authoritative contract fixes the result` rather than manufacturing choices.

An approved design source proves intended visual direction and fidelity, not usability, accessibility, performance, privacy, or platform fit. Expert judgment may open `review_required`; it becomes a blocker only when linked to an applicable contract, consequence, or evidence. `review_required` is a decision disposition, not a capability-record Verification value; keep the underlying capability `failed`, `inconclusive`, `blocked`, or `unverified` until its evidence changes. A screenshot proves rendered state, and a validator proves only the rule it executes.

## Task-based usability evidence

For a new, redesigned, or high-consequence journey whose task success or usability is claimed or materially uncertain, record the task, representative context, participant or reviewer, observed result and friction, and evidence limitation. Scale the participant set and protocol to reach, novelty, uncertainty, reversibility, and consequence; a narrow correction does not require a study merely to close its regression.

A cognitive walkthrough or expert inspection is heuristic evidence, not user evidence. It may identify a plausible failure and justify focused validation, but it cannot establish prevalence, user preference, or successful real-world task completion.

## Accepted UX debt

UX debt is a known, consciously accepted gap inside an otherwise bounded delivery. It is not an unknown claim, a `not applicable` capability, an uninvestigated risk, an out-of-scope future feature, or a deferred capability. Debt never changes failed or unverified evidence into a pass.

Record `gap -> affected users/journey/target/capability -> consequence and claim limitation -> known evidence and remaining gap -> mitigation or fallback -> acceptance authority -> accountable owner -> review trigger -> exit condition and required proof`. The acceptance authority must own the affected release or risk boundary; absent that authority, keep the decision `review_required` or blocked according to consequence. Here, accountable owner means the person or qualified role responsible for resolution; it is distinct from the technical `surfaceEvidence.owner` such as `native`, `browser`, or `renderer`. Use the project's existing issue tracker when it already owns follow-up; do not create a shadow backlog.

False success, a blocked core task, a critical accessibility barrier, an active privacy or security violation, or data loss without truthful containment and recovery cannot be accepted as ordinary UX debt. Treat an accessibility gap as critical when it prevents a supported user from completing a core task, escaping a state, perceiving necessary state or feedback, or recovering safely, or when it breaches an applicable release contract; use an established project severity rubric when one exists instead of inventing a universal score. Reduce scope or keep the result blocked or unverified. An unknown owner yields `review_required` for a low-consequence limitation and remains blocked when the consequence requires accountability; never invent a person or use an unqualified `team` placeholder.

## Risk-gated user coverage matrix

For a narrow low-risk fix, include only materially affected and adjacent users and explain why broader rows are not applicable. Expand coverage with reach, novelty, uncertainty, reversibility, and consequence. A new, redesigned, broadly used, accessibility-sensitive, privacy-sensitive, or high-consequence journey records:

| Coverage | Record |
| --- | --- |
| Population | Primary, secondary, affected, not affected, and counterexample users |
| Context | Role, expertise, accessibility needs, locale/direction, device/window, input, connectivity, account state, and entitlement |
| Impact | Job, current evidence, assumption/unknown, frequency, severity, and success measure |

Use representative research or product evidence where the claim requires it. A single issue is valid evidence for that reported failure, not prevalence across all users. Record excluded groups and unknown reach rather than inventing certainty.

## Capability record

Track these dimensions independently and scope every record to the named target, build, and version:

| Dimension | Values | Meaning |
| --- | --- | --- |
| Role | `action`, `navigation`, `input`, `output` | The semantic job. Decoration is not a capability. |
| Applicability | `applicable`, `not applicable` | Whether the capability belongs to this target and delivery scope. |
| Fidelity | `production`, `simulated`, `deferred` | Whether the real owner performs the result, a coherent prototype substitutes for it, or it is intentionally absent. |
| Availability | `available`, `temporarily unavailable`, `unavailable`, `not evaluated` | Whether the real capability owner can currently provide the result. |
| Presentation | `visible`, `hidden`, `omitted`, `passive` | How the current surface exposes or intentionally does not expose it. |
| Invocability | `enabled`, `disabled`, `not invocable` | Whether this affordance can currently initiate the capability. |
| Feedback/result | `idle`, `pending`, `succeeded`, `failed`, `blocked`, `not evaluated` | The observable state of the current attempt, tied to the real owner. |
| Verification | `proven`, `failed`, `inconclusive`, `blocked`, `unverified` | What current evidence establishes on the named target. |

For early design, record semantic intent and intended owner. Before production promotion, name the concrete command or handler, state owner, observable outcome, failure and recovery, lifetime, and evidence. Conditions such as role, entitlement, policy, permission, platform, connectivity, or service health are facts beside Availability, not hidden inside a status label.

Keep the dimensions orthogonal. For a capability that is `not applicable`, set Availability to `not evaluated`, Presentation to `omitted`, Invocability to `not invocable`, and Feedback/result to `not evaluated`. An available capability may have a disabled affordance because a current prerequisite is unmet; disabled does not mean unavailable. A hidden capability is not unavailable merely because policy, role, or context suppresses its presentation. Pending, succeeded, failed, and blocked feedback/result states must follow the durable owner rather than a local animation, handler call, or toast.

## Functional truth

- A visible, enabled production affordance performs its advertised semantic outcome. Calling a handler, showing a toast or spinner, or reaching a mock adapter is not completion.
- A real failed operation is honest only when it avoids false success, reports the resulting state, and offers recovery or a next step.
- Simulated prototype capabilities may be enabled and coherent, but they cannot satisfy production or native acceptance until reclassified and proved against the real owner.
- A deferred future capability is normally omitted and has no operable affordance. For the current delivery its Applicability is `not applicable`, Availability is `not evaluated`, Presentation is `omitted`, Invocability is `not invocable`, Feedback/result is `not evaluated`, and Verification remains `unverified`.
- A stable top-level information architecture may retain an honestly unavailable signpost when product or platform convention makes that location meaningful. Record it as a separate passive output capability with `production` fidelity, `available` availability, `passive` presentation, and `not invocable` invocability, then verify it independently as `proven`, `failed`, `inconclusive`, `blocked`, or `unverified`. It is never the deferred navigation affordance and must not be a button, link, or focus action.
- A temporarily unavailable state requires a real prerequisite, an accessible reason, and a useful next step. `unavailable` represents a durable role, policy, platform, or product constraint and must not masquerade as a temporary outage.
- Decoration has no action, focus stop, interactive role, or misleading hover or pressed treatment.
- An editable-looking control must support edit, validate, commit, and cancel behavior. A permanent read-only value appears as output or is clearly read-only in appearance and semantics.

## Operating-state contract

Select states from real ownership and risk, not a universal screenshot quota. For each applicable state name its trigger, owner, visible and semantic result, allowed actions, preserved data, recovery, and proof:

- initial, loading, empty, partial, stale, offline, degraded, error, retry, and cancel;
- optimistic updates, duplicate submission, conflict, and concurrent edit;
- authentication, session expiry, authorization, permission denial, role, and entitlement changes; and
- privacy, consent, and sensitive-data display, storage, sharing, or redaction.

Do not strand users in indefinite loading, erase recoverable input, expose protected data while permissions settle, or report success before the durable owner confirms it.

## Reduce input burden and support editable text

For a constrained identifier with an authoritative source, prefer a suitable platform, toolkit, provider, or portal picker, then search, detection, suggestion, and recent values as the source permits. There is no universal picker for every path, font, executable, account, or expert identifier. Validated manual entry remains legitimate for arbitrary or expert data and as an explicit fallback.

Name validation timing, format, recovery, privacy, permissions, cancellation, and the resulting stored value. A picker dialog alone does not prove that the chosen value works after packaging or restart.

Editable text defines typing, selection, clipboard, undo/redo, replacement, composition and IME, validation, commit, and cancel. Never validate or submit an incomplete composition; apply validation after composition commit unless the target's documented contract requires otherwise. Test the actual input method and representative scripts when text input is material.

## Undo and reversible work

Undo is a domain command model, not a dump of UI events. Record user-visible intent, coalesce continuous changes, remove no-op commands, show a meaningful label for the next operation, and restore visible state. Passive hover, focus, scroll, and navigation noise is excluded by default; selection, navigation, and resize belong only when one is itself a meaningful mutation users reasonably expect to reverse. State Undo applicability explicitly for editor-like or reversible workflows instead of forcing it onto every form.

Test command boundaries, coalescing, no-op removal, redo invalidation, labels, restored selection/focus where relevant, and the real model result.

## State and persistence

Separate application defaults, user preferences, system-owned preferences, document or model state, scene or window restoration, sensitive values, and ephemeral UI. Name one owner and serialization boundary for each.

Every durability claim names its boundary: same view, revisit, restart, process recreation, supported upgrade, device transfer, or durable account state. Do not turn a toolkit API into a promise about reinstall or cross-device survival. A migration is explicit, idempotent where required, and scoped to supported version, package, and distribution channel. Prove old-to-new behavior with representative stored data and failure recovery.

## Resource identity, lifecycle, and reset provenance

Map lifecycle verbs to distinct semantic transitions in the product model. For each displayed operation such as Save, Save As, Apply, Revert, or Reset, name its source state, destination identity, durable or runtime owner, and resulting dirty or pending state rather than assuming the label fixes the behavior. Keep the canonical resource, editable working copy, last-saved resource, active resource, and dirty or pending state visible and attributable whenever their difference changes the next action, loss risk, or runtime result. A copy or identity change discloses the resulting identity and whether the canonical, saved, or active resource changed.

When the product contract requires portability, preserve a stable logical identifier or an owned-root-relative locator. An absolute locator remains valid when the actual platform, provider, or integration owner requires it; record the explicit reason and resolution boundary, then provide a relink or recovery path when it no longer resolves. A copy-based workflow remains valid when its identity and lifecycle effects are truthful.

For each user intent, prefer the shortest truthful transition. When the current owner can safely update or reload the original, do not require an unnecessary import-modify-apply round trip or its staged copy-edit-apply variant. When a staged copy/edit-and-apply flow is required by the real owner or boundary, expose the reason and name the original identity; preserve or reconcile it, then provide an apply or save-back path or an equivalently explicit commit path.

Revert, current/inherited defaults, and versioned factory defaults are distinct authoritative baselines with named scopes and owners. Reset values are read from the real owner when the operation runs, not from duplicated UI literals; describing a duplicate as authoritative does not transfer ownership. Proof covers non-default values, inherited and changed-default values, dirty state, Undo, save and apply, restart, and relocation only where each case is applicable; record an inapplicable case and reason instead of fabricating a transition.

## Information architecture, content, and recovery

Information architecture (IA) uses stable grouping and terminology, a visible location, clear entry and exit, an evident next step, task-oriented labels, meaningful headings and links, and one clear primary action where the task has one. Remove duplicate commands whose semantic result and context are the same; distinguish commands whose owners or consequences differ.

Within the affected surface or journey, for every task-bearing region or affordance, name a distinct user-recognizable job, outcome, decision, or information gain relative to its parent and siblings. When that purpose is redundant or unsupported, merge it, relabel it, render it as truthful output, or omit it instead of retaining a control merely to make the surface look complete.

Prioritize content by task criticality, frequency, consequence or urgency, and actionability. Keep essential state, blockers or errors, recovery, and the next action in context. Simultaneous dense presentation for comparison, monitoring, or expert work remains valid when the task requires concurrent visibility. Labels such as Advanced and More are not a mechanical ban or permission: their disclosed purpose, content, state, and consequence must remain predictable.

When a product advertises the same job through multiple frontends, shells, skins, or platform clients, maintain a capability reachability matrix across those supported surfaces. Each material capability must be reachable on each surface where it applies, intentionally handed off through a clear transition with return path and preserved context/state, or marked not applicable with a concrete product or platform reason. Visual parity is not required, but a newer or alternate surface must not silently strand settings, recovery, account, or core-task capabilities that users are told it supports.

Use consequence-scaled error handling. Preserve input, identify the specific correction, prevent duplicate submission, and use review, reversal, or confirmation only when the consequence warrants it.

## Internationalization and bidirectionality

Internationalization begins during discovery. When the brief, audience, or distribution intent implies more than one locale, every user-visible string the work introduces or changes ships through the platform's translation mechanism (resource bundles, message catalogs) from the first artifact; hardcoded single-locale copy in new distribution-targeted work is a defect, not a follow-up. Public release, open-source distribution, or store delivery is a signal to resolve locale intent during discovery, not proof of it: a deliberately single-locale surface stays single-locale, and a narrow change on one does not by itself demand retrofitting externalization. When copy ships in a language different from the brief's language, record the locale decision and its reason instead of defaulting silently. Avoid display-string concatenation; use locale-aware formatting, sorting, searching, pluralization, and input. Carry language and direction metadata, and define whether a product language override follows the system, persists locally, syncs, or is unavailable.

Test representative long text, unbroken content, bidirectional content, and taller-script content without assuming one universal expansion percentage. Mirroring is selective: media controls, charts, maps, and user-authored direction may not mirror with surrounding navigation.

## Accessibility, motion, and adaptation

Prove names, roles, states, actions, focus order, visible focus, focus restoration, absence of traps, status announcements, and alternatives for complex pointer gestures. Equivalent semantic outcome and failure truth matter more than identical gestures. Apply keyboard, switch, touch, pointer, stylus, voice, and assistive-technology checks only where the platform or supported input makes them relevant.

Reduced motion follows the system preference while preserving the semantic outcome, state feedback, focus, and spatial comprehension without requiring animation. Never remove essential status or progress information as the reduced-motion treatment.

Adaptive invariants preserve reachability and avoid unintended information or function loss across supported window sizes, orientation, zoom, text scaling, content variation, and input changes. Platform references own exact insets, posture, windowing, breakpoints, and legitimate two-dimensional exceptions.

## Evidence and promotion

- An executable target journey plus the resulting state proves function.
- Automation plus applicable keyboard, assistive-technology, and device checks supports an accessibility claim.
- Observing representative users completing believable tasks supports usability; a reviewer preference does not.
- Telemetry and outcome measures support live quality when their collection and interpretation are valid.
- Static contract tests prove policy packaging and routing, not that downstream applications are usable.

Record the target, build, state, owner, command or procedure, artifact, result, limitation, and reviewer for every material claim. An unavailable proof path is a blocker or explicit unverified claim, never a reason to substitute a prettier artifact.
