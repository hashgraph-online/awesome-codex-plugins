---- MODULE Commit ----
CONSTANT RM
VARIABLES rm, tm
Init == rm = [r \in RM |-> "working"] /\ tm = "init"
Prepare(r) == rm[r] = "working" /\ rm' = [rm EXCEPT ![r] = "prepared"] /\ UNCHANGED tm
Decide == tm = "init" /\ \E r \in RM : rm[r] = "prepared" /\ tm' = "committed" /\ UNCHANGED rm
Abort == tm = "init" /\ tm' = "aborted" /\ UNCHANGED rm
Apply(r) == tm = "committed" /\ rm[r] = "prepared" /\ rm' = [rm EXCEPT ![r] = "committed"] /\ UNCHANGED tm
Cancel(r) == tm = "aborted" /\ rm[r] # "aborted" /\ rm' = [rm EXCEPT ![r] = "aborted"] /\ UNCHANGED tm
Done == \A r \in RM : rm[r] \in {"committed", "aborted"} /\ UNCHANGED <<rm, tm>>
Next == Decide \/ Abort \/ Done \/ \E r \in RM : Prepare(r) \/ Apply(r) \/ Cancel(r)
Consistent == ~(\E r, s \in RM : rm[r] = "committed" /\ rm[s] = "working")
====
