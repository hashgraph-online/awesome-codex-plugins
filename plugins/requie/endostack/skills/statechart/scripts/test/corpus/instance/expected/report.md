# Wrapped

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

## ReachesBlue breaks

TLC's counterexample for ReachesBlue is in `tlc-ReachesBlue.out`. It takes 2 steps before it repeats forever.

0. "red"
1. L!Next → "green"
2. L!Next → "yellow"

From step 0 the run loops through steps 0 to 2 forever, returning to step 0 by L!Next.

## Rules that hold

NoDeadlock
