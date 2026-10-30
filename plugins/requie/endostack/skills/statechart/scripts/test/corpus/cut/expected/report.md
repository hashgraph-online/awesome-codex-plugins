# Wide

TLC reached more than 500 distinct states, over the chart budget of 500. The chart draws only the paths to broken rules: 2 states and 1 arrow.

## Early breaks

The shortest path to a state that breaks Early takes 1 step.

0. x=0 y=0
1. Next → x=1 y=0

## Rules not checked

Late

After the first break, each rerun stops at 100,000 distinct states, and a run hit that bound before it explored everything. These rules may hold or break. To check them, remove the rules that break from the config or shrink the model.
