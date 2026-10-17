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
- [ ] At most one em dash per tweet (replace the excess with a comma, colon
      or `..`, never a period). No en dashes between clauses, no double dashes.
- [ ] No cluster of 2026 AI vocab (3+ markers in one tweet = rewrite it; one
      is fine): significant, crucial, notably, comprehensive, insights,
      robust, leverage, foster, landscape, nuanced, streamline, elevate,
      fundamentally, essentially; "-ing" clause openers; nominalisations.
- [ ] No reveal bridge ("The result?", "Here's what"), no "It's not X, it's
      Y", no sincerity opener ("not gonna lie", "let me be honest").
- [ ] Stands alone if read in isolation.
- [ ] At least one concrete detail (a number with a referent, a name, an
      example) in the body tweets.

## Rhythm across the thread

Let tweet length follow the material. A teaching tweet runs long because it
teaches; a transition runs short because it transitions. That natural variance
is fine on a long thread (our X corpus: variance helps at about 430 words and
is neutral at 200). What reads as machine-made is the opposite in both
directions: every tweet the same length with no clause doing work, or a
manufactured seesaw with a 3-word "punch tweet" dropped in for rhythm. The
inserted punch is the humanizer fingerprint; do not add one. If the thread
reads flat, let the tweet carrying the most content take one real clause, and
stop there.

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
