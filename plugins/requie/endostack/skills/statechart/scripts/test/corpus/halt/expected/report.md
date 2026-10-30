# Halt

TLC reached 3 states and 2 steps. The chart draws 3 states and 2 arrows.

## ReachesFive breaks

TLC's counterexample for ReachesFive is in `tlc-ReachesFive.out`. It takes 2 steps before it repeats forever.

0. 0
1. Next → 1
2. Next → 2

From step 2 the run stops in 2 forever, so ReachesFive never holds.
