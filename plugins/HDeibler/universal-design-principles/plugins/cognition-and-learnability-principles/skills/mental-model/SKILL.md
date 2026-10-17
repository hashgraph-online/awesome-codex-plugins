---
name: mental-model
description: 'Use this skill whenever the design will be used by people who bring prior expectations — which is essentially every design. Trigger when designing onboarding, when picking metaphors (folders, channels, projects), when reviewing why users keep getting confused, when migrating from one product convention to another, or when the user mentions "users don''t understand," "they keep doing X wrong," or "we''re inventing something new." Mental Model is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) and grounds most modern user-experience design.'
---

# Mental Model

A mental model is the user's internal representation of how a system works. When the user's mental model matches the system's actual behavior, interaction is smooth — the user predicts correctly, takes the right actions, and recovers from problems easily. When the mental model diverges from reality, errors and confusion follow. The designer's job is to either build a system that matches the user's existing mental model, or build the system in a way that teaches an accurate model quickly.

## Definition (in our own words)

Every user comes to a design with assumptions about how it will work, drawn from prior experience: how computers behave, how websites navigate, how forms validate, how billing is structured. These assumptions form a mental model — a simplified representation that lets the user predict what will happen if they take a particular action. When the prediction matches reality, the design feels intuitive. When it doesn't, the design feels confusing — or worse, the user proceeds confidently and produces unintended results.

The book distinguishes two complementary mental-model types: **system models** (how the user thinks the system works internally) and **interaction models** (how the user thinks they should interact with the system). Designers tend to have rich system models and weak interaction models; users tend to have weak system models and (with use) increasingly accurate interaction models.

## Origins and research lineage

- **Kenneth Craik**, *The Nature of Explanation* (Cambridge University Press, 1943). The foundational text — Craik proposed that humans build internal models of external reality and run those models to predict consequences. The basis for cognitive psychology's model-based reasoning.
- **Philip Johnson-Laird**, *Mental Models* (Cambridge, 1983). Mental models as the unit of human reasoning.
- **Donald Norman**, *The Design of Everyday Things* (1988, 2013). Brought mental models into mainstream design vocabulary. Norman distinguished the **designer's model** (what the designer intended), the **system image** (what the design actually presents), and the **user's model** (what the user infers from the system image). The designer's job is to make the system image clearly communicate the intended model.
- **Lidwell, Holden & Butler** (2003) compactly distinguish system models from interaction models. The book's central case: anti-lock brakes whose interaction model differed from conventional brakes (don't pump; brake firmly and steer). Drivers using the wrong interaction model didn't get the safety benefit.
- **D. Gentner & A. Stevens (eds.)**, *Mental Models* (Erlbaum, 1983). Collected research on how people form and use mental models.

## The two model types

### System models

How the user thinks the system works — its components, its rules, its causal mechanisms. Examples:

- "The cloud" stores my files; they're available from any device.
- "Email" sends messages from my account to another account; once sent, gone.
- "A folder" contains files; moving a file out of one folder puts it in another.

System models can be wildly inaccurate without affecting the user. Most users don't know how email actually works (SMTP, MX records, queues); their model is "type address, click send, message arrives." That's enough.

### Interaction models

How the user thinks they should interact with the system. Examples:

- To save: click File → Save (or press Cmd-S).
- To unsubscribe from a mailing list: scroll to the bottom of the email and click "unsubscribe."
- To recover a deleted file: open the trash and drag it out.

Interaction models are what designers must align to. A perfectly-conceived system whose interaction model the user can't form is unusable.

## When mental models matter

- **Always**, but especially when:
  - The product is new in its category (no established conventions).
  - The product borrows from a familiar category but does something subtly different.
  - The product's underlying mechanism differs from how the user imagines it ("soft delete" looks like "delete").
  - Users come from a different product (migration: their model is from competitor X).

## Strategies for working with mental models

### Match the user's existing model

If a familiar mental model exists, design to match it. Don't reinvent. Examples:

- **Folder metaphor** for file systems — users from desktop computing transfer their model directly.
- **Email metaphor** for messaging products — users from email transfer expectations about senders, recipients, threads.
- **Shopping-cart metaphor** for e-commerce — users from physical retail transfer expectations.

The trade-off: matching limits you to the existing model's shape. Sometimes the right design needs to break it.

### Teach a new model when needed

If your system genuinely differs, teach the model — through onboarding, through naming, through the system image:

- **Antilock brakes** required teaching: "brake firmly and steer; don't pump." Posters, training, and visceral feel during practice all helped.
- **Spreadsheets** taught a new computing model in the early 1980s; once learned, transferable across applications.
- **Touch interfaces** taught new gestures (pinch-to-zoom, swipe) that users didn't have from prior interfaces.

The investment in teaching pays off if the new model is genuinely better; it fails if the new model is just different.

### Make the system image faithful

Norman's three models (designer / system image / user) align only if the system image — what the user actually sees — clearly communicates the designer's intent. A system image that obscures the model produces user-model drift.

Examples of faithful system images:

- A "soft delete" that explicitly says "Moved to trash. Will be deleted in 30 days." User's model now matches reality.
- An auto-save indicator that says "Saved 2 minutes ago" rather than vanishing once save completes. User knows the state.
- A loading spinner with status text ("Authenticating..." → "Connecting to server..." → "Loading your data..."). User's model of the process is faithful to what's happening.

## When mental models break

The classic break case: a feature whose interaction model differs from a similar-looking feature.

- **Anti-lock brakes** — the book's example. Drivers had the conventional-brakes model (pump on slick surfaces); ABS requires the opposite (brake firmly, steer). Drivers using the wrong model didn't get the safety benefit; sometimes worse, drivers were misled by ABS into believing they could drive faster on slick surfaces.
- **Find-and-replace dialogs** that match across or within documents inconsistently — users expect one behavior, get another.
- **Trash-emptying schedules** — users believe deleted is gone; some systems retain for 30 days; some indefinitely; users don't know.

When the system's behavior departs from the user's model, surface the difference explicitly.

## Worked examples

### Example 1: building on a familiar model

A new project-management tool uses Kanban boards (familiar from Trello, physical sticky-note boards). Users transfer their model: columns are statuses, cards are tasks, dragging changes status. Onboarding is light because the model is mostly already there.

### Example 2: teaching a new model

A code-collaboration tool (Git) introduces concepts (commits, branches, merges, conflicts) that don't exist in the prior file-editing model. Onboarding explicitly teaches:
- "A commit is a snapshot of your code at a point in time."
- "A branch is a parallel line of work."
- "Merging combines two branches; conflicts arise when they touch the same lines."

Without this teaching, users from a Word-document model misunderstand and produce unintended states.

### Example 3: revealing the system model when it diverges

A SaaS product uses soft-delete: users delete an item; it goes to a trash that's purged after 30 days. The user's model from desktop computing is "deleted = gone immediately." The product surfaces the difference:

```
"Project archived. It will be permanently deleted in 30 days. [Restore] [Delete now]"
```

Now the user's model includes the recovery window. They can trust their actions.

### Example 4: aligning the interaction model with the user's stated goal

A user wants to "share a document with my team." The interaction model in many products is: change permissions on the document, then send a link. A simpler interaction model: "Share with team" button that does both at once.

The simpler model maps closer to the user's goal-level thinking; the user doesn't have to think about permissions and links separately.

### Example 5: when the system surprises

A user clicks "Cancel subscription." The system says "subscription canceled — you'll be downgraded at the end of the billing period." The user's model was "canceled = no longer charged." The system's model was "canceled = no future renewals; current period continues."

Either model is defensible; the divergence is the issue. Surface the actual behavior at the moment of action.

## Cross-domain examples

### Technology adoption: ATMs

Early ATMs (1960s–80s) had to teach a new mental model — a bank machine that dispensed cash without a teller. Banks invested heavily in education; users initially distrusted; gradually the model became standard. Now it's invisible.

Modern parallel: contactless payment (NFC). The mental model "tap to pay, no signature, no physical card insertion" took years to spread; now it's standard.

### Anti-lock brakes (the book's case)

ABS provided a measurable safety improvement in controlled tests. In real-world driving, the improvement was much smaller — because drivers used the wrong interaction model (pumping the brakes). Manufacturer campaigns to teach the new model ("brake firmly and steer") closed the gap partly.

The lesson: technical superiority doesn't translate to real-world benefit if the interaction model doesn't transfer.

### Cooking: induction stovetops

Induction cooktops behave differently from gas or resistive electric. They heat the pan, not the air; they don't glow red; turning off "stops" the heat almost instantly. Users from gas/electric models often misjudge — leaving pans on a "hot" surface that's already cooled, or turning up heat further because the pan isn't visibly responding.

Induction-cooktop manufacturers add visible cues (glowing rings, residual-heat indicators) to bridge the model gap.

## Anti-patterns

- **Inventing metaphors no user has ever encountered.** "Wisdom Pods" or "Synergy Spaces" sound clever; they don't transfer.
- **Borrowing a familiar metaphor for behavior that doesn't match it.** A "trash" that empties silently; a "save" that auto-syncs in real-time without the user seeing.
- **System images that obscure system behavior.** Loading screens that don't say what's happening; "Save" buttons that may or may not commit; opaque pricing.
- **Onboarding that's just a tour.** Watching a feature demo doesn't teach a model as well as guided practice.
- **Inconsistency that breaks the learned model.** "Save" works one way in one section; differently elsewhere.

## Heuristics

1. **The "what model are users bringing?" check.** Before designing, name the prior product/category your users are likely coming from. Their model from there transfers — partially.
2. **The mental-model-mismatch audit.** When users report confusion, ask: what model do they have? What model does the system actually have? The gap is the design opportunity.
3. **The first-use walkthrough.** Watch a new user. Where they're confused or surprised is where their model diverged from the system.
4. **The system-image check.** What does the system actually show the user? Does it accurately reflect the underlying behavior? If yes, models stay aligned. If no, mistakes follow.

## Related principles

- **`affordance`** — affordance signals interaction models at a per-element level.
- **`mapping`** — control-effect relationships are part of the interaction model.
- **`expectation-effect`** — expectations come from mental models.
- **`mimicry`** — borrowing recognizable patterns leverages existing models.
- **`consistency`** — consistency lets users transfer one part of the model to another.
- **`recognition-over-recall`** — recognition is faster when it matches a learned model.
- **`errors`** — mistake-type errors flow from wrong models.

## Sub-aspect skills

- **`mental-model-system-vs-interaction`** — distinguishing the two model types and choosing which to optimize for.
- **`mental-model-mismatch-and-onboarding`** — diagnosing model mismatches and designing onboarding that teaches the right model.

## Closing

Mental models are the substrate of intuitive design. Users don't experience the system you built; they experience the model they have of the system. When the two align, your work becomes invisible — users just *use* it. When they diverge, every other design move is fighting an undertow. Building the system image so that users can form a faithful model is the deepest design discipline.
