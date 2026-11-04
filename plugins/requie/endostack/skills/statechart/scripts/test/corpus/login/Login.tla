---- MODULE Login ----
EXTENDS Naturals
VARIABLES screen, tries
vars == <<screen, tries>>
Init == screen = "form" /\ tries = 0
Submit == screen = "form" /\ screen' = "checking" /\ UNCHANGED tries
Accept == screen = "checking" /\ screen' = "home" /\ tries' = 0
Reject == screen = "checking" /\ tries < 3 /\ screen' = "form" /\ tries' = tries + 1
Lock == screen = "checking" /\ tries >= 2 /\ screen' = "locked" /\ UNCHANGED tries
Logout == screen = "home" /\ screen' = "form" /\ UNCHANGED tries
Next == Submit \/ Accept \/ Reject \/ Lock \/ Logout
NeverLocked == screen # "locked"
HomeResetsTries == screen = "home" => tries = 0
====
