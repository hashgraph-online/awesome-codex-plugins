# Later

TLC reached 4 states and 3 steps. The chart draws 4 states and 3 arrows.

## Small breaks

The shortest path to a state that breaks Small takes 1 step.

0. 0
1. Next → 1

## Rules not checked

Odd

A later TLC run stopped with exit status 76 before it reached these rules, so each may hold or break. TLC printed:

```
Error: Evaluating invariant Odd failed.
Attempted to apply the operator overridden by the Java method
public static tlc2.value.impl.IntValue tlc2.module.Naturals.Plus(tlc2.value.impl.IntValue,tlc2.value.impl.IntValue),
but it produced the following error:
Cannot cast tlc2.value.impl.StringValue to tlc2.value.impl.IntValue
Error: The behavior up to this point is:
State 1: <Initial predicate>
x = 0
State 2: <Next line 5, col 9 to line 5, col 27 of module Later>
x = 1
State 3: <Next line 5, col 9 to line 5, col 27 of module Later>
x = 2
```
