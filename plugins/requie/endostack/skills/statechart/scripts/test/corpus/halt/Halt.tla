---- MODULE Halt ----
EXTENDS Naturals
VARIABLES x
Init == x = 0
Next == x < 2 /\ x' = x + 1
Spec == Init /\ [][Next]_x
ReachesFive == <>(x = 5)
====
