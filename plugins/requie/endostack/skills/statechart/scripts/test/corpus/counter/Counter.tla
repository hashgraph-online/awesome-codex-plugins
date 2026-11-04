---- MODULE Counter ----
EXTENDS Naturals
VARIABLES n
Init == n = 0
Up == n < 4 /\ n' = n + 1
Reset == n > 0 /\ n' = 0
Next == Up \/ Reset
BelowThree == n < 3
====
