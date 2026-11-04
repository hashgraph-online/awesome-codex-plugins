---- MODULE Pool ----
EXTENDS FiniteSets, TLC
CONSTANT Workers
VARIABLES busy
Init == busy = {}
Take(w) == w \notin busy /\ busy' = busy \cup {w}
Free(w) == w \in busy /\ busy' = busy \ {w}
Next == \E w \in Workers : Take(w) \/ Free(w)
Sym == Permutations(Workers)
NotAllBusy == busy # Workers
====
