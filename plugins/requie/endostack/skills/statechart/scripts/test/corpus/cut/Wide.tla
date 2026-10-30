---- MODULE Wide ----
EXTENDS Naturals
VARIABLES x, y
Init == x = 0 /\ y = 0
Next == \/ x < 400 /\ x' = x + 1 /\ y' = y
        \/ y < 400 /\ y' = y + 1 /\ x' = x
Early == x < 1
Late == ~(x = 400 /\ y = 400)
====
