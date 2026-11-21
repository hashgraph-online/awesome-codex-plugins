# Example: "I Don't Wanna Pick" (36 shots, 99 s, 9:16, 133.8 BPM)

The previz of the varg music video this skill was built on, kept as reference code. Read it for techniques; it is not
wired to run (its storyboard and stills live in the original project).

- `props.js`: the original props: pilot mannequin with cockpit poses (stick and throttle, sax), a 9 m fighter with
  named canopy/engines/antenna, drones, THE 503 (a monster at true scale: instanced screen tiles, jaw pivots, an eye
  lid), the agent orb, a saxophone, missile helix trails, bursts, rings.
- `sets.js`: five master sets (cockpit with red/orange/calm moods, space battle, carrier deck, the monster's throat
  with a scrolling tunnel, an "odyssey" set of separate islands), blackout spheres, light moods.
- `shots.js`: 36 shots: beat-synced hits, walk cycles, a missile "Itano circus", strikes from five sides, a trench
  run where sound rings kill drones, an engine dying and the power rerouting.
- `pack.json`: the real 13-run Seedance pack (refs with their roles, runs with notes, every shot's action line, reuse
  and lip-sync lists) in the current `pack.json` format. 13 runs billed ≈16 credits/s at 480p.

To run it with the current app: copy these three files over `js/props.js`, `js/sets.js` and `js/shots.js` (the
original props, not the generic ones), point `config.json` at that storyboard with its scenes and
`"scale": {"ship": 9, "monster": 250}`, and give each set `subjects` if you want auto cameras (all 36 shots there
have hand-made cameras; their `framing` field is a note, not an auto-camera subject).
