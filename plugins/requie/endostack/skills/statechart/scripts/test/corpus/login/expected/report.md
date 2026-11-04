# Login

TLC reached 11 states and 14 steps. The chart draws 4 states and 5 arrows.

The config uses VIEW, so TLC treats equivalent states as one; an arrow may point at TLC's representative state instead of the exact state the step reaches.

## NeverLocked breaks

The shortest path to a state that breaks NeverLocked takes 6 steps.

0. Sign-in form
1. submit password → Checking password
2. password wrong [0 earlier failures] → Sign-in form
3. submit password → Checking password
4. password wrong [1 earlier failures] → Sign-in form
5. submit password → Checking password
6. too many failures → Account locked

## Rules that hold

HomeResetsTries
