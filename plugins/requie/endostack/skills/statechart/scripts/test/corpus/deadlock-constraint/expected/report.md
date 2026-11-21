# Stack

TLC reached 3 states and 3 steps. The chart draws 3 states and 3 arrows.

The config has a constraint, so only the deadlock TLC reported is marked. A state with no drawn step may have steps the constraint removed, and TLC does not count that as a deadlock.

## NoDeadlock breaks

The shortest path to a state that breaks NoDeadlock takes 2 steps.

0. 0
1. Push → 1
2. Push → 2

## Rules that hold

Small
