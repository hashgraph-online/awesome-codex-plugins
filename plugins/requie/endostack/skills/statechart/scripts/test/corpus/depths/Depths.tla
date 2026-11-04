---- MODULE Depths ----
EXTENDS Naturals
VARIABLES a, b
Init == a = 0 /\ b = 0
IncA == a < 3 /\ a' = a + 1 /\ b' = b
IncB == b < 3 /\ b' = b + 1 /\ a' = a
Next == IncA \/ IncB
NotBothOne == ~(a = 1 /\ b = 1)
AUnderTwo == a < 2
BUnderTwo == b < 2
SumUnderFive == a + b < 5
StartsZero == a + b > 0
====
