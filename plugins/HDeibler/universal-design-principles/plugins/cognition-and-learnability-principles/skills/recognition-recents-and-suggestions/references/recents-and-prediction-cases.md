# Recents, frequents, and predictive UI: reference

A reference complementing `recognition-recents-and-suggestions` with implementation patterns.

## Recents data sources

Where to compute recents from:

- **User activity logs** — server-side history of user actions.
- **Local storage** — client-side recents for fast access.
- **Browser history** — for navigation recents.
- **Frecency** (a Mozilla coinage) — combined recency + frequency score.

## Frecency algorithms

A frecency score combines recency and frequency. Items used recently *and* often score highest. Used by Firefox URL bar, VSCode quick-open, and similar.

A simple frecency formula:

```js
function frecency(item) {
  const recencyScore = 1 / (1 + daysSince(item.lastAccess));
  const frequencyScore = Math.log(1 + item.accessCount);
  return recencyScore * 10 + frequencyScore;
}
```

Tunable weights let you favor recency or frequency depending on context.

## Predictive suggestion sources

Where suggestions come from:

- **Recently used** — simple, fast, often accurate.
- **Frequency-weighted** — favors items used many times.
- **Time-of-day patterns** — morning vs. evening usage.
- **Context** — the page, the role, the workspace.
- **Similar-user behavior** — collaborative filtering.
- **Content-based** — items similar to what the user just acted on.

## Privacy considerations

- **Per-context recents** — work recents shouldn't leak to personal context.
- **Clearable** — let users clear recents.
- **Opt-out** — let users disable recents tracking entirely.
- **Encryption / scoping** — recents stored in user-controlled stores.

## Resources

- Mozilla "frecency" definition — Firefox URL-bar algorithm.
- Search-bar UX research from NN/g.
- Privacy by design literature (Cavoukian, others).
