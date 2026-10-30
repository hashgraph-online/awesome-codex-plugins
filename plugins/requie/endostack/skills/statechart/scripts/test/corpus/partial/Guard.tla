---- MODULE Guard ----
EXTENDS Naturals
VARIABLES v
Init == v = 0
Inc == v < 2 /\ v' = v + 1
Weird == v = 2 /\ v' = "two"
Next == Inc \/ Weird
Ok == v # 1
====
