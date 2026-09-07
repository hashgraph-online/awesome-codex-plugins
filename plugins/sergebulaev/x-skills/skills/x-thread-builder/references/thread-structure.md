# Thread Structure: Pacing and the Closer

A thread is a funnel. Each tweet's only job is to earn the tap to the next one.
Design for the drop-off, not the ideal reader who reads every word.

## Per-position roles

| Position | Role | Rule |
|---|---|---|
| Tweet 1 | The hook. Promise + open loop. | Carries 80% of the outcome. Must stop the scroll alone, under 280 chars. |
| Tweet 2 | The strongest payoff or first beat. | Front-load value here; do not save it. Tap-through is highest at 2. |
| Tweets 3 to N-1 | The body. One item or beat each. | Each stands alone. Concrete examples, real numbers. |
| Tweet N | The closer. | Most quotable line + one clear ask. Earns the repost and follow. |

## Tap-through decay

Readers leak out at every tweet. Reported pattern: a meaningful share of readers
drop by tweet 3, and again by tweet 6. Consequences:

- Put the best item at position 1 or 2, never the finale.
- 5-9 tweets is the sweet spot for teaching and list threads.
- A story thread can run longer if every beat raises the stakes, but tap-through
  still falls, so the turn should not be buried at tweet 15.

## Opening a loop (tweet 1 patterns)

- A count with a catch: "7 X that Y. Most people get 3 wrong."
- A withheld mechanism: "{result}. I did not expect why."
- A first-person result: "How I {number result} in {timeframe}. The exact steps."
- A story tension: "{the moment it nearly broke}. Here is what happened."

The loop must stay open. If tweet 1 answers itself, nobody expands.

## The closer playbook

The last tweet does two things and stops:

1. The single most quotable line of the whole thread (this is what gets
   screenshotted and reposted).
2. One ask, not three. Pick one:
   - "If this was useful, bookmark it and follow for more like this."
   - "Reply with the one you would add."
   - "Repost the first tweet if it helped someone."

Never stack all three asks. Never end on "that's it" or "hope this helps".

## Per-tweet scrub (apply to every tweet)

- [ ] Under 280 chars on a standard account (emoji = 2 chars each).
- [ ] No em dashes, en dashes, or double dashes. Use `..`.
- [ ] No AI vocab (leverage, fundamentally, delve, harness, etc.).
- [ ] Stands alone if read in isolation.
- [ ] At least one concrete detail (number, name, example) in the body tweets.

## Length variation

A thread where every tweet is the same length reads as machine-made. Mix it:
a 3-word punch tweet next to a fuller 240-char teaching tweet. The variation is
itself a human signal.

## Hand-splitting with `---`

Default to hand-splitting so the user approves the exact breaks:

```
Tweet 1 text here, the hook.

---

Tweet 2 text, the strongest payoff.

---

Tweet 3 text, the next beat.
```

Publora treats each `---`-delimited block as one tweet and numbers them `(1/N)`.
If you instead pass flowing prose with no separators, Publora auto-splits at
paragraph then sentence boundaries.
