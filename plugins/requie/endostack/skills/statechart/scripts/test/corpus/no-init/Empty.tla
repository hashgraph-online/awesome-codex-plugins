---- MODULE Empty ----
VARIABLES x
Init == x = 0 /\ FALSE
Next == x' = x
Fine == TRUE
====
