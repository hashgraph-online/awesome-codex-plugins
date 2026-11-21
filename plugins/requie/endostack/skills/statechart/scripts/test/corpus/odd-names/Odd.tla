---- MODULE Odd ----
VARIABLES s
Init == s = "a<b>"
Next == \/ s = "a<b>" /\ s' = "%%x: #1; [[fork]]"
        \/ s = "%%x: #1; [[fork]]" /\ s' = "line\nbreak \"q\""
        \/ s = "line\nbreak \"q\"" /\ s' = "a<b>"
Inv_1 == s # "line\nbreak \"q\""
====
