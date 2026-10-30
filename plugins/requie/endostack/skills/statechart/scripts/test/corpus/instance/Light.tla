---- MODULE Light ----
VARIABLES light
Init == light = "red"
Go == light = "red" /\ light' = "green"
Slow == light = "green" /\ light' = "yellow"
Stop == light = "yellow" /\ light' = "red"
Next == Go \/ Slow \/ Stop
Spec == Init /\ [][Next]_light /\ WF_light(Next)
Typed == light \in {"red", "green", "yellow"}
EventuallyBlue == <>(light = "blue")
AlwaysMoves == []<>(light = "green")
StartsRed == light = "red"
====
