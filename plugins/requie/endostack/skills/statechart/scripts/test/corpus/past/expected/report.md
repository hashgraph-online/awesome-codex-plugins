# Tank

TLC reached 4 states and 5 steps. The chart draws 5 states and 6 arrows.

1 state beyond a CONSTRAINT ends a rule's path, and the chart includes it. TLC checks rules in such states but explores no further from them.

## NotOverflow breaks

The shortest path to a state that breaks NotOverflow takes 4 steps.

0. 0
1. Fill → 2
2. Drain → 1
3. Fill → 3
4. Fill → 5

## Rules that hold

NoDeadlock
