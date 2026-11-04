---- MODULE Jugs ----
EXTENDS Naturals
VARIABLES small, big
Min(m, n) == IF m < n THEN m ELSE n
Init == small = 0 /\ big = 0
FillSmall == small' = 3 /\ big' = big
FillBig == big' = 5 /\ small' = small
EmptySmall == small' = 0 /\ big' = big
EmptyBig == big' = 0 /\ small' = small
SmallToBig == LET p == Min(small, 5 - big) IN small' = small - p /\ big' = big + p
BigToSmall == LET p == Min(big, 3 - small) IN big' = big - p /\ small' = small + p
Next == FillSmall \/ FillBig \/ EmptySmall \/ EmptyBig \/ SmallToBig \/ BigToSmall
NotFour == big # 4
====
