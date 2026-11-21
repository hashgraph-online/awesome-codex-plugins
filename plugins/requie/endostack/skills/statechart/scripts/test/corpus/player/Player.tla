---- MODULE Player ----
VARIABLES playback, panel
Init == playback = "stopped" /\ panel = "closed"
Play == playback # "playing" /\ playback' = "playing" /\ UNCHANGED panel
Pause == playback = "playing" /\ playback' = "paused" /\ UNCHANGED panel
Stop == playback # "stopped" /\ playback' = "stopped" /\ panel' = "closed"
OpenPanel == panel = "closed" /\ panel' = "open" /\ UNCHANGED playback
ClosePanel == panel = "open" /\ panel' = "closed" /\ UNCHANGED playback
Next == Play \/ Pause \/ Stop \/ OpenPanel \/ ClosePanel
Spec == Init /\ [][Next]_<<playback, panel>> /\ WF_<<playback, panel>>(Play)
PanelOnlyWhilePlaying == panel = "open" => playback # "stopped"
EventuallyPlays == <>(playback = "playing")
StopsForever == <>[](playback = "stopped")
ClosedAtStart == panel = "closed"
====
