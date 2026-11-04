---- MODULE Clock ----
EXTENDS Naturals
VARIABLES mode, ticks
Init == mode = "idle" /\ ticks = 0
Tick == ticks' = (ticks + 1) % 3 /\ UNCHANGED mode
Start == mode = "idle" /\ mode' = "running" /\ UNCHANGED ticks
Halt == mode = "running" /\ mode' = "idle" /\ UNCHANGED ticks
Next == Tick \/ Start \/ Halt
Shown == mode
Fine == TRUE
====
