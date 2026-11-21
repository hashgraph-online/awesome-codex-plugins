---- MODULE Session ----
VARIABLES auth, net
Init == auth = "out" /\ net = "online"
SignIn == auth = "out" /\ net = "online" /\ auth' = "in" /\ UNCHANGED net
SignOut == auth = "in" /\ auth' = "out" /\ UNCHANGED net
Drop == net = "online" /\ net' = "offline" /\ UNCHANGED auth
Reconnect == net = "offline" /\ net' = "online" /\ UNCHANGED auth
Next == SignIn \/ SignOut \/ Drop \/ Reconnect
NoOfflineSignIn == TRUE
====
