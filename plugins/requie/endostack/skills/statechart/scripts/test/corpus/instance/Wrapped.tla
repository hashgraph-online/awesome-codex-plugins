---- MODULE Wrapped ----
VARIABLES light
L == INSTANCE Light
Init == L!Init
Next == L!Next
Spec == Init /\ [][Next]_light /\ WF_light(Next)
ReachesBlue == []<>(light = "blue")
====
