# Commit

TLC reached 21 states and 41 steps. The chart draws 21 states and 39 arrows.

2 steps stay inside one chart state and are not drawn.

## Consistent breaks

The shortest path to a state that breaks Consistent takes 3 steps.

0. coordinator init / r1 working, r2 working
1. prepare → coordinator init / r1 prepared, r2 working
2. decide → coordinator committed / r1 prepared, r2 working
3. apply → coordinator committed / r1 committed, r2 working

## Rules that hold

NoDeadlock
