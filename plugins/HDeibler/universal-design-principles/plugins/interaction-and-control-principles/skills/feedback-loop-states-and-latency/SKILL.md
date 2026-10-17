---
name: feedback-loop-states-and-latency
description: 'Use this skill when designing the visible states an interactive element passes through (idle / pending / success / error) and matching feedback timing to the user''s perceptual thresholds. Trigger when designing button states, form-submit flows, file-upload progress, loading screens, or any interaction whose response time is variable. Sub-aspect of `feedback-loop`; read that first.'
---

# Feedback states and latency thresholds

Most interactive actions pass through a small set of visible states; the system must communicate each. The latency of each state determines what feedback is appropriate — a 50ms response needs no spinner, a 5s response needs progress info, a 50s response needs estimated time remaining.

## The four states

### Idle
The element is interactive and waiting. Affordance signals "you can do this." Static styling.

### Pending
Action triggered; system working. Disable trigger to prevent re-submit; show indicator if wait > ~500ms.

### Success
Action succeeded. Show the result in-place where possible; toast/banner if the result is on another surface.

### Error
Action failed. In-context, specific, actionable error message.

```html
<button id="action" data-state="idle">
  <span class="label">Save</span>
  <span class="spinner" hidden></span>
</button>

<style>
  button[data-state="pending"] { cursor: wait; opacity: 0.7; }
  button[data-state="pending"] .spinner { display: inline-block; }
  button[data-state="success"] { background: var(--success); }
  button[data-state="error"] { background: var(--destructive); }
</style>
```

## Latency thresholds (Miller, Card et al., Doherty)

| Latency | Threshold | Pattern |
|---|---|---|
| < 100ms | "Instant" | No indicator. Just respond. |
| 100–400ms | "Responsive" | Light state change (button briefly disabled). |
| 400ms–1s | "Noticeable" | Spinner or progress micro-animation. |
| 1–10s | "Waiting" | Spinner with status text. |
| > 10s | "Long" | Progress bar with estimated time remaining; cancel option. |

**Doherty Threshold (~400ms)**: response times under this keep users in flow. Above this, attention drifts and engagement drops.

## Optimistic UI

For actions where the success rate is high and the action is reversible, update the UI as if the action succeeded immediately, then commit in the background. If the action fails, roll back visibly with an error message.

```js
async function toggleStar(item) {
  // Optimistic
  item.starred = !item.starred;
  render();

  try {
    await api.updateStar(item.id, item.starred);
  } catch (err) {
    // Rollback with feedback
    item.starred = !item.starred;
    render();
    showToast(`Couldn't update: ${err.message}`);
  }
}
```

The user gets instant feedback; failure is the exception, handled with explicit feedback.

## Skeleton screens vs. spinners

For loading content (not actions), prefer **skeleton screens** to spinners:

```html
<!-- While data loads -->
<article class="post-skeleton">
  <div class="title-skel"></div>
  <div class="meta-skel"></div>
  <div class="body-skel"></div>
  <div class="body-skel"></div>
</article>
```

Skeletons:
- Show the page's structure immediately.
- Reduce perceived load time.
- Reduce visual disruption when real content arrives.

Spinners are better when the wait isn't structural (a single action's pending state) or when the location of the result isn't predictable.

## Progress indicators for long operations

For operations > 10s:
- **Determinate progress bar** (when % complete is known) with status text.
- **Time-remaining estimate** (after enough data to estimate accurately).
- **Cancel option** (don't trap the user in a stuck operation).
- **Background continuation** option for very long ops (let them work elsewhere).

```html
<div class="upload">
  <p>Uploading <strong>file.zip</strong></p>
  <progress max="100" value="42">42%</progress>
  <p class="status">42% — about 2 minutes remaining</p>
  <button>Cancel</button>
</div>
```

## Error feedback: in-context

Errors should appear with the element that caused them, not in a generic page banner.

```html
<div class="field" data-state="error">
  <label for="email">Email</label>
  <input id="email" type="email" aria-invalid="true" aria-describedby="email-error" />
  <p id="email-error" class="error">
    We couldn't find an account with this email.
    <a href="/signup">Sign up?</a>
  </p>
</div>
```

`aria-invalid` and `aria-describedby` make the error programmatically associated; screen readers announce both together.

## Anti-patterns

- **Silent commits.** Button submits with no visible response.
- **Blink-and-miss success.** Confirmation appears for 100ms.
- **Generic errors.** "Something went wrong" with no specific or actionable info.
- **Spam confirmations.** Every save shows a "Saved!" toast users dismiss on autopilot.
- **Wrong state colors.** Pending state same color as success.
- **Spinners over content the user is reading.** Distracting; use skeleton or peripheral indicator.

## Heuristics

1. **The "what state am I in?" check.** At any moment during an action, can the user tell which of the four states they're in? If not, feedback is missing.
2. **The latency-stopwatch.** Time each major action. Match feedback to the threshold the action falls into.
3. **The error-recovery audit.** For each error feedback, can the user tell what to do next? If "no idea," rewrite the message.

## Related sub-skills

- **`feedback-loop`** (parent).
- **`feedback-loop-positive-vs-negative`** — loop architecture; this skill is loop *implementation*.
- **`accessibility-operable`** — `aria-live` regions communicate states to screen readers.
- **`forgiveness`** — error feedback is recovery's first step.
