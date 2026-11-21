---- MODULE Count ----
EXTENDS Naturals
VARIABLES n
Init == n = 0
Step == n < 6 /\ n' = n + 1
Skip == n < 5 /\ n' = n + 2
Back == n > 0 /\ n' = 0
Next == Step \/ Skip \/ Back
NotFive == n # 5
====
