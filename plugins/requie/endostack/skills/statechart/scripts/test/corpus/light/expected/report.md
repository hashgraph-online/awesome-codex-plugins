# Light

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

## EventuallyBlue breaks

TLC's counterexample for EventuallyBlue is in `tlc-EventuallyBlue.out`. It takes 2 steps before it repeats forever.

0. "red"
1. Go → "green"
2. Slow → "yellow"

From step 0 the run loops through steps 0 to 2 forever, returning to step 0 by Stop.

## Rules that hold

Typed, NoDeadlock, AlwaysMoves, StartsRed

TLC checked StartsRed only in initial states, because it is listed under PROPERTY and has no temporal operator. List it under INVARIANT to check it in every state.
