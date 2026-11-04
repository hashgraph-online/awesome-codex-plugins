# Player

TLC reached 6 states and 16 steps. The chart draws 5 states and 8 arrows.

The step "press stop" sometimes changes Playback and Panel at the same time, and sometimes changes only one region.

## PanelOnlyWhilePlaying breaks

The shortest path to a state that breaks PanelOnlyWhilePlaying takes 1 step.

0. Playback: Stopped; Panel: Queue closed
1. open queue → Playback: Stopped; Panel: Queue open

## StopsForever breaks

TLC's counterexample for StopsForever is in `tlc-StopsForever.out`. It takes 1 step before it repeats forever.

0. Playback: Stopped; Panel: Queue closed
1. press play → Playback: Playing; Panel: Queue closed

From step 0 the run loops through steps 0 to 1 forever, returning to step 0 by press stop.

## Rules that hold

NoDeadlock, EventuallyPlays, ClosedAtStart

TLC checked ClosedAtStart only in initial states, because it is listed under PROPERTY and has no temporal operator. List it under INVARIANT to check it in every state.
