# Jugs

TLC reached 16 states and 96 steps. The chart draws 16 states and 58 arrows.

38 steps stay inside one chart state and are not drawn.

## NotFour breaks

The shortest path to a state that breaks NotFour takes 6 steps.

0. small=0 big=0
1. FillBig → small=0 big=5
2. BigToSmall → small=3 big=2
3. EmptySmall → small=0 big=2
4. BigToSmall → small=2 big=0
5. FillBig → small=2 big=5
6. BigToSmall → small=3 big=4

## Rules that hold

NoDeadlock
