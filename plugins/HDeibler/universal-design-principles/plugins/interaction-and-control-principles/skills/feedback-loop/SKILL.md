---
name: feedback-loop
description: 'Use this skill whenever a user takes an action and the system must communicate that the action was received, is in progress, succeeded, or failed. Trigger when designing button states, form submission, file uploads, payment flows, real-time UI updates, loading states, error states, success confirmations, or any moment when the user is waiting for the system to do something. Trigger when the user mentions "feels broken," "doesn''t seem to work," "users keep clicking again," or any symptom of feedback gaps. Feedback Loop is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) — and one of the principles whose absence most reliably damages a product''s perceived quality.'
---

# Feedback Loop

A feedback loop is the relationship between an action and the visible response that confirms the action happened. Every system in nature is composed of interacting feedback loops; every interface is too. When users press a button, type a character, drag an item, or commit a transaction, the system must respond — promptly, visibly, and unambiguously — to close the loop. Without that response, the user doesn't know whether the action registered, whether the system is working, or whether to try again. The cumulative effect of weak feedback is a product that feels broken even when it isn't.

## Definition (in our own words)

A feedback loop in interaction design is the mechanism by which the system tells the user "I received your action and here's what's happening." Loops can be *positive* (amplifying — repeated actions create accelerating change, like clicking a "+1" button that animates and grows the count) or *negative* (dampening — bringing the system back to a stable state, like a thermostat or a Segway maintaining balance). The most important loops in product UI are usually negative: the user acts; the system confirms; equilibrium is restored. When loops are missing or delayed, users repeat actions, doubt the system, or assume failure.

## Origins and research lineage

- **Cybernetics** (Norbert Wiener, 1948 onward). The mathematical theory of feedback in systems — biological, mechanical, and social. The intellectual foundation for everything that follows in HCI feedback design.
- **Jay W. Forrester**, *Industrial Dynamics* (MIT Press, 1961) and *Urban Dynamics* (1969). Applied feedback-loop thinking to organizational and urban systems. Introduced the diagrams (causal loop diagrams, stock-and-flow diagrams) still used in systems analysis.
- **Donald Norman**, *The Design of Everyday Things* (1988). Made feedback one of the central UI principles. Norman's gulf of evaluation — the gap between the user's intent and the system's perceptible state — is essentially the absence of good feedback.
- **Lidwell, Holden & Butler** (2003) compactly distinguished positive feedback loops (amplifying — useful for change but risky if unmoderated) from negative feedback loops (stabilizing — useful for equilibrium). The book's central case: 1950s football helmets that created a positive feedback loop (more padding → more risk-taking → more injuries → more padding).
- **Modern HCI heuristics** (Nielsen's 10 heuristics, 1994 onward). "Visibility of system status" — the first of Nielsen's 10 — is essentially the feedback principle named for usability practice.
- **Doherty Threshold** (Doherty & Thadani, IBM, 1982). Empirical research showing that response times under 400ms keep users in flow; longer delays break engagement.

## Why feedback matters

Every interaction is a tacit contract: the user gives an input expecting some response. Without the response, the user is left in ambiguity. They may:

- **Repeat the action** (clicking again, typing again, refreshing). Often produces unintended duplicate effects.
- **Doubt their input** ("did I press it hard enough?", "did it register?").
- **Assume system failure** and abandon.
- **Develop ritualistic habits** (always pressing twice, always checking twice).
- **Stop trusting the system**.

The cost compounds: each weak feedback moment is a small tax; thousands of moments across a product become a perception of unreliability that no individual feature can repair.

The reverse is also true: tight, unambiguous feedback creates confidence. The user acts, sees the system respond, and feels in command. This is what well-engineered software feels like — at the perceptual level, before the user evaluates any specific feature.

## Positive vs. negative feedback loops

The book's distinction matters in practice:

### Positive feedback loops (amplifying)

The system's response to an action makes future similar actions more likely or more impactful. Examples:

- **Recommendation engines**: a user clicks a recommendation; the system learns and shows more like it; the user clicks more; the system learns more. Eventually homogeneous content; "filter bubble" risk.
- **Streak counters**: each consecutive day of use makes the user more invested in not missing a day. Engagement amplifies.
- **Viral product growth**: each new user invites others; each invitation creates more new users. Exponential growth — when it works.

Positive loops produce change, sometimes dramatic. Without moderation by a counter-loop, they run away (the football-helmet example: more padding → more risk-taking → more injuries → more padding).

### Negative feedback loops (stabilizing)

The system's response brings things back toward an equilibrium. Examples:

- **Form validation**: the user enters invalid input; the system flags it; the user corrects; equilibrium restored.
- **Auto-save indicator**: "Saving..." → "Saved." Each save resets the system to a known-good state.
- **Undo systems**: the user takes an action; if it's wrong, undo restores prior state.
- **Real-time spell-check**: a typo creates instability; correcting restores it.

Most product UI feedback is negative — the system absorbs user actions and returns to stability. Designs that lean too heavily on positive loops (gamification, streak anxiety, dopamine engineering) cross into manipulation.

## When to apply

- **Always**, on every interactive element. Every button, link, input, drag handle, toggle needs feedback.
- **Especially** on actions whose result isn't immediately visible (background operations, server requests, multi-step flows).
- **Critically** on destructive or irreversible actions where the user must know the action committed.
- **Real-time** on continuous operations (drag, resize, scroll).
- **Asynchronously** when the action's effect is delivered later (notifications, scheduled tasks).

## Latency thresholds

How fast feedback must appear depends on what's responding. The widely-cited thresholds (Miller 1968; Card, Robertson, Mackinlay 1991):

- **< 100ms**: feels instant. No spinner needed; the user perceives immediate response.
- **< 1 second**: feels responsive. No spinner needed unless something visible is taking time. The user maintains flow.
- **1–10 seconds**: needs a visible indicator. Spinner, progress bar, status text. The user notices the wait.
- **> 10 seconds**: needs progress information (estimated time remaining, percentage complete). The user is likely to abandon if the wait isn't justified.

The Doherty threshold (Doherty & Thadani, 1982) refined the < 400ms range as the boundary at which response time stops feeling natural.

## When NOT to over-apply

- **Trivial confirmations.** Don't show "Loading..." for a 50ms response. The flicker is worse than no indicator.
- **Continuous indicators that fight content.** A spinner that animates over the user's reading content is distracting. Place indicators in the periphery.
- **Feedback for actions the user didn't take.** Auto-save indicators that appear without user input clutter the UI.
- **Excessive haptic / sound feedback.** Each tap doesn't need to vibrate. Reserve haptics for moments that matter.

## The four states of action feedback

Most interactive actions have four states the system must communicate:

### 1. Idle (resting)

The element is interactive and ready. Affordance says "you can do this." Static styling.

### 2. Pending (in progress)

The action was triggered; the system is working. Common patterns:

- **Disable the trigger** to prevent double-submission.
- **Spinner or loading indicator** if the wait is > ~500ms.
- **Button text changes** to "Saving...", "Sending...", "Loading..."
- **Skeleton placeholder** for content that will fill in.

```html
<button id="save" type="submit">
  <span class="label">Save</span>
  <span class="spinner" hidden></span>
</button>

<script>
const btn = document.getElementById('save');
btn.addEventListener('click', async () => {
  btn.disabled = true;
  btn.querySelector('.label').textContent = 'Saving...';
  btn.querySelector('.spinner').hidden = false;
  try {
    await save();
    showSuccess();
  } catch (err) {
    showError(err);
  } finally {
    btn.disabled = false;
    btn.querySelector('.label').textContent = 'Save';
    btn.querySelector('.spinner').hidden = true;
  }
});
</script>
```

### 3. Success

The action succeeded. The result should be visible — preferably in-place (the row appears, the value updates) rather than via a generic "Saved!" toast that the user must trust.

When in-place feedback isn't possible (the action's effect is on another page or in a backend), use a toast or banner with specific content ("Invoice #1284 sent to maria@acme.com").

### 4. Error

The action failed. Feedback must be:
- **In-context** with the field or element that caused the error (not a generic top-of-page banner the user might miss).
- **Specific** about what went wrong.
- **Actionable** — what can the user do to recover.

```html
<div class="field" data-state="error">
  <label for="email">Email</label>
  <input id="email" type="email" aria-invalid="true" aria-describedby="email-error" />
  <p id="email-error" class="error-message">
    We couldn't find an account with this email. <a href="/signup">Sign up?</a>
  </p>
</div>
```

## Worked examples

### Example 1: a form-submit button with all four states

```html
<form id="signup-form">
  <input name="email" type="email" required />
  <input name="password" type="password" required />
  <button id="submit">Create account</button>
  <p id="status" aria-live="polite"></p>
</form>

<script>
const form = document.getElementById('signup-form');
const btn = document.getElementById('submit');
const status = document.getElementById('status');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  // Pending state
  btn.disabled = true;
  btn.textContent = 'Creating account...';
  status.textContent = '';
  try {
    await createAccount(new FormData(form));
    // Success state
    status.textContent = 'Account created! Redirecting...';
    setTimeout(() => location.href = '/welcome', 1500);
  } catch (err) {
    // Error state
    btn.disabled = false;
    btn.textContent = 'Create account';
    status.textContent = `Couldn't create account: ${err.message}`;
  }
});
</script>
```

Four states; user is never left wondering what happened.

### Example 2: optimistic UI update with rollback on failure

```js
async function archive(item) {
  // Optimistic: update UI immediately
  const previous = items.slice();
  items = items.filter(i => i.id !== item.id);
  render();

  try {
    await api.archive(item.id);
    // Implicit success — UI already reflects new state
  } catch (err) {
    // Rollback + error feedback
    items = previous;
    render();
    showToast(`Archive failed: ${err.message}`);
  }
}
```

The UI feels instant; failure rolls back visibly with explicit feedback.

### Example 3: long-running task with progress

```html
<div class="upload">
  <p>Uploading <strong>vacation-photos.zip</strong></p>
  <progress max="100" value="0" id="upload-progress">0%</progress>
  <p id="upload-status">Preparing upload...</p>
  <button id="cancel">Cancel</button>
</div>

<script>
async function uploadWithProgress(file) {
  const progress = document.getElementById('upload-progress');
  const status = document.getElementById('upload-status');
  const startTime = Date.now();

  await uploadFile(file, {
    onProgress: ({ loaded, total }) => {
      const pct = Math.round(loaded / total * 100);
      progress.value = pct;
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = loaded / elapsed; // bytes/sec
      const remaining = (total - loaded) / rate;
      status.textContent = `${pct}% — ${formatTime(remaining)} remaining`;
    }
  });
  status.textContent = 'Upload complete.';
}
</script>
```

Long-running task gets full progress feedback, including estimated time.

### Example 4: real-time editing feedback

```html
<textarea id="post-body" oninput="autoSave()"></textarea>
<p id="save-status" aria-live="polite">All changes saved</p>

<script>
let saveTimeout;
let lastSaved = new Date();

function autoSave() {
  const status = document.getElementById('save-status');
  status.textContent = 'Editing...';

  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    status.textContent = 'Saving...';
    await api.savePost({ body: document.getElementById('post-body').value });
    lastSaved = new Date();
    status.textContent = `Saved at ${formatTime(lastSaved)}`;
  }, 800);
}
</script>
```

Three states (editing, saving, saved) all visible. User knows the system is tracking their work.

## Cross-domain examples

### Industrial control: the Segway

Lidwell, Holden, and Butler use the Segway as the example of a tightly-tuned negative feedback loop: the rider leans forward; the gyroscope detects the angle change; the motor adjusts wheel speed to maintain balance. This loop runs ~100 times per second. Coarser loops would produce visible oscillation; finer would be wasteful.

The lesson for software: feedback frequency matches the dynamics of the user's actions. Real-time interactions need real-time feedback; slower actions can have slower feedback.

### Aviation: stall warning systems

A pilot pulling back on the yoke too aggressively gets immediate negative feedback: a stall warning horn, a stick-shaker, a yoke pusher. Each progressively forceful — early warnings let the pilot self-correct; late ones force correction. The graduated feedback gives the pilot agency at every level of urgency.

Software analog: progressive validation. Soft inline hint → warning → block on submit → confirmation dialog for destructive.

### Football helmets (the book's case)

The classic positive-feedback-loop failure: in the 1950s, plastic-with-padding helmets replaced leather. Players felt safer; tackled more aggressively; head/neck injuries rose. Designers responded by adding more padding; players became even more aggressive; injuries rose further. The loop wasn't moderated by rules against helmet-first tackling until decades later.

The lesson for software: positive loops without counter-mechanisms produce unintended consequences. A feature that drives engagement may drive it past the user's actual welfare; metrics that look good at first may create harms over time.

### Thermostats

The canonical example of a negative feedback loop. Too warm → cooling activates → temperature drops → cooling deactivates → temperature drifts up → cycle. The system maintains equilibrium without continuous user input.

UI analog: any system that absorbs user actions and returns to a stable state — auto-save, undo, drift-corrected forms.

## Anti-patterns

- **Silent commits.** A button that submits a form with no visible response. Users click again; double-submission.
- **Blink-and-miss feedback.** A success message that appears for 100ms before vanishing. Users miss it; doubt the action.
- **Generic error messages.** "Something went wrong." User doesn't know what or how to fix.
- **Wrong-channel feedback.** Errors as toasts that vanish; success as banners that linger. Mismatched persistence.
- **No pending state.** Clicking save and seeing nothing for 3 seconds before the page refreshes. User clicks again.
- **Spam confirmations.** Every routine action gets a "Done!" toast. User dismisses everything on autopilot.
- **Decorative spinners.** A spinner that's not actually waiting on anything (purely visual). User loses trust when they realize.
- **Hover-only feedback.** A button that only responds visually on hover. Touch users see no response on tap.

## Heuristics

1. **The "did it work?" test.** After any interaction, ask: can the user tell whether the action succeeded? If they have to guess, feedback is missing.
2. **The double-click audit.** Watch users. Each unintended double-click is feedback that pending state was invisible.
3. **The error-message audit.** Every error message in the app should answer: what happened, why, what to do next.
4. **The latency-threshold check.** For each action, time it. Actions over 1s need a pending indicator; over 10s need progress info.
5. **The accessibility check.** Visual feedback alone fails screen-reader users. Pair with `aria-live` regions for status changes.

## Related principles

- **`affordance`** — feedback completes the loop affordance starts.
- **`forgiveness`** — feedback enables the recovery forgiveness depends on.
- **`errors`** — error feedback is the most consequential feedback type.
- **`mapping`** — feedback should map to the action that caused it.
- **`expectation-effect`** — feedback that violates expectation creates surprise; align it.
- **`accessibility-perceivable`** (process) — feedback must be perceivable across abilities.

## Sub-aspect skills

- **`feedback-loop-states-and-latency`** — designing the four states (idle, pending, success, error) and matching feedback to time thresholds.
- **`feedback-loop-positive-vs-negative`** — choosing between amplifying and stabilizing loop architectures.

## Closing

Feedback is the principle that decides whether your product *feels* responsive. Every interaction that lacks visible response erodes trust at a perceptual level no specific feature can repair. Build feedback into every interactive element from the start; audit every "is this working?" complaint as a feedback gap; treat the four states as non-negotiable for any consequential action.
