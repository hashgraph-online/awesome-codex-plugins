# Workflow: projecting an underlying forward

1. `optiondesk simulate SYM --horizon 14`. Raise `--draws` if convergence
   fails; 4000 usually clears the gate where 3000 does not.
2. Read `converged` before anything else.
3. If structures exist on disk, read the realised against implied table.

## Reporting

If converged is false, say so and stop quoting quantiles. Offer the higher
draw count instead.

Give the fan as a range with its horizon attached, never as a single
number. "Between 744 and 822 over fourteen days, with the median near 782"
is the shape of an honest answer.

Value at risk needs its level and horizon every time: "3.3 percent over
fourteen days at the 95 percent level", not "3.3 percent".

The disagreement column is the most useful output and the easiest to
misuse. It says the market and the recent past disagree by that many
points. It does not say who is right.
