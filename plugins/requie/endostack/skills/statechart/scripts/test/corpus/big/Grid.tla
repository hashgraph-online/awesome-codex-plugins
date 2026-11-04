---- MODULE Grid ----
EXTENDS Naturals
CONSTANT N
VARIABLES x, y
Init == x = 0 /\ y = 0
Right == x < N /\ x' = x + 1 /\ y' = y
Up == y < N /\ y' = y + 1 /\ x' = x
Next == Right \/ Up
NotCorner == ~(x = 2 /\ y = 1)
FarCorner == ~(x = N /\ y = N)
====
