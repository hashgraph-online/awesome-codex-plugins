---- MODULE Typo ----
EXTENDS Naturals
VARIABLES x
Init == x = 0
Next == x' = x + 1 /\ x < 3
Bad == x + "a" = 1
====
