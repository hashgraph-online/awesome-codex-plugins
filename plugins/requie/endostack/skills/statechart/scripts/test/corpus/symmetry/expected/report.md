# Pool

TLC reached 3 states and 4 steps. The chart draws 3 states and 4 arrows.

The config uses SYMMETRY, so TLC treats equivalent states as one; an arrow may point at TLC's representative state instead of the exact state the step reaches.

## NotAllBusy breaks

The shortest path to a state that breaks NotAllBusy takes 2 steps.

0. {}
1. Take → {w1}
2. Take → {w1, w2}

## Rules that hold

NoDeadlock
