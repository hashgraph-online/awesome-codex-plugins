---- MODULE Later ----
EXTENDS Naturals
VARIABLES x
Init == x = 0
Next == x < 3 /\ x' = x + 1
Small == x < 1
Odd == IF x = 2 THEN x + "a" = 1 ELSE TRUE
====
