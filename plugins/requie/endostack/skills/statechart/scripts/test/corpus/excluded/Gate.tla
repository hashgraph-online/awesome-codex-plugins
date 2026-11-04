---- MODULE Gate ----
EXTENDS Naturals
VARIABLES pos
Init == pos = 0
Fwd == pos < 3 /\ pos' = pos + 1
Jump == pos = 1 /\ pos' = 3
Back == pos > 0 /\ pos' = pos - 1
Next == Fwd \/ Jump \/ Back
NeverThree == pos # 3
NoJump == ~(pos = 1 /\ pos' = 3)
====
