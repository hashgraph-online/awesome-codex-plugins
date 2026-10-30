# Gate

TLC reached 4 states and 6 steps. The chart draws 5 states and 7 arrows.

1 step that an ACTION_CONSTRAINT excludes ends a rule's path, and the chart includes it as separate states. TLC checks rules after such steps but explores no further.

## NeverThree breaks

The shortest path to a state that breaks NeverThree takes 2 steps.

0. 0
1. Fwd → 1
2. Jump → 3 (excluded step)
