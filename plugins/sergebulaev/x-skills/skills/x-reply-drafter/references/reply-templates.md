# X Reply and Quote-Tweet Templates

Five shapes. All stay under 280 chars (emoji = 2). Pick by what the counterpart
said and what you want the reply to do. No em dashes in the fill-in lines; use
`..` or a period.

## R1 - Answer-Their-Question

When they asked something. Answer plainly, add one real detail, stop.

```
{Direct answer in one line.}

{One concrete detail or number that proves you actually know.}
```

Example:
> we use 6-minute deploys now. cut it by killing the full image rebuild on every
> push and caching the layer that never changes.

## R2 - Concede-Then-Sharpen

When they pushed back and they are partly right. Concede first, then sharpen.

```
fair on {their valid point}.

where I would push: {the sharper angle or the missing piece}.
```

Example:
> fair, consistency matters more than I said. where I would push: consistency
> without a hook just trains people to scroll past you faster.

## R3 - Extend-Their-Point

When they are right and you can take it one layer deeper.

```
{Restate their point in your words, briefly.} and the part that compounds: {the deeper layer}.
```

Example:
> totally, shipping fast builds momentum. and the part that compounds: every
> fast ship teaches you what to measure next, so you ship smarter, not just more.

## R4 - Share-Lived-Experience

When a real story from your own work adds weight.

```
we hit this {timeframe} ago.

{What broke, the number, what you changed.}
```

Example:
> we hit this last quarter. signups looked flat until we found the email
> confirmation was landing in spam for 30% of users. one DNS fix, signups up 22%.

## R5 - Value-Add Quote (quote tweet, X4 shape)

When your point deserves its own reach. Quote the tweet, add the missing nuance,
land a reframe. Never a cheap dunk.

```
{Concede or restate the quoted take in a few words}, but {the missing nuance}.

{One memorable reframe line.}
```

Example (quoting a "just ship it" take):
> true, but ship it without a way to measure if it worked and you are just
> gambling with extra steps. ship it AND instrument it.

## Rules for all five

- One idea per reply. If you have two, pick the stronger.
- React to what they actually said, not a strawman.
- A specific number or named detail beats a general agreement.
- End on a landing, not "what do you think?".
- If the thread is stale (days old) and the point is strong, a fresh standalone
  tweet or a quote tweet often beats a late reply.
