# Workflow: reading a chain's positioning

1. `optiondesk chain SYM --expiry YYYY-MM-DD`
2. `optiondesk exposure`
3. Read in this order: regime, then the walls, then the flip, then max
   pain, then the ratios.

## What each answer is worth

Regime is the headline: dampening means hedging leans against moves,
amplifying means it leans with them. Say which, and say it rests on the
dealer assumption.

The walls are where hedging concentrates, which is why they act as
reference levels. They are not support and resistance and should not be
described as such.

The put to call ratios are open interest and volume. Open interest says
where positions sit, volume says where they moved today. A high ratio on
open interest with a low one on volume is a stale book, not fresh fear.

## Never

Do not quote a wall without the assumption. Do not present max pain as a
target. Do not report a flip level as if it were the only one when the
profile crosses several times.
