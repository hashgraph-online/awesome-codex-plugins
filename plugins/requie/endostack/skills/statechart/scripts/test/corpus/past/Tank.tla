---- MODULE Tank ----
EXTENDS Naturals
VARIABLES level
Init == level = 0
Fill == level' = level + 2
Drain == level > 0 /\ level' = level - 1
Next == Fill \/ Drain
NotOverflow == level < 5
Bound == level < 4
====
