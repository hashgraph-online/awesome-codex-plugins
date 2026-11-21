---- MODULE Stack ----
EXTENDS Naturals
VARIABLES depth
Init == depth = 0
Push == depth < 2 /\ depth' = depth + 1
Pop == depth > 0 /\ depth < 2 /\ depth' = depth - 1
Next == Push \/ Pop
Small == depth < 3
Bound == depth < 5
====
