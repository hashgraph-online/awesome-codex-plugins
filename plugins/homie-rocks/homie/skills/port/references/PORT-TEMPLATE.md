# PORT.md template

Write this in the game's folder (`games/<id>/PORT.md`) before changing code, and
keep it true as the port changes. It is for the next person (or agent) who opens
the game, so write plain sentences.

```markdown
# <Game name> — multiplayer port

**Difficulty: <easy | medium | hard | not a fit>.** <One paragraph: what the game is
(engine, loop, input, state, camera), and why this grade — the one or two things that
make it easy or hard, e.g. "fast physics between many bodies", "the camera turns with
the ship", "the whole world is 40 KB of state".>

Original: <where it came from>, licence <MIT/…> (<file>), <lines> lines, <engine>.

## Multiplayer design
- A round: <length; what wins; what happens on death (respawn, never out)>.
- Room: <max players>; bots from the first frame: <how many>.
- The host owns: <rules, enemies, pickups, hits, the clock, the seed…>.
- Each browser owns: <its own body / its own board>. Movement mode: <owner | host>.
- A late joiner: <takes which bot's place, and what it sees first>.
- Host handoff: <what the checkpoint holds>.
- The big screen: <overview / director camera; what it shows>.

## Controls
- Computer: <keys>.
- Phone: <floating stick where the thumb lands; buttons: …; swipes: …>.
- Camera rule: <fixed / player-owned yaw; input on screen axes>.

## What changed in the code
- <file>: <what and why>.

## Checks
| Row | Result | Notes |
| --- | --- | --- |
| owner-desk | | |
| owner-phone | | |
| owner-iphone | | |
| ui-cover | | |
| round | | |
| host-kill | | |
| late-join | | |
| tv | | |
| audio | | |
| errors | | |

## Still weak
- <plainly>.
```
