---- MODULE Finish ----
EXTENDS Naturals
VARIABLES step
Init == step = 0
Next == step < 2 /\ step' = step + 1
NoDeadlock == step < 2
====
