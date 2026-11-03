# Master sets and blocking

## One location = one master set

Every shot in a location is framed inside the same three.js set, so wides and close-ups share one geography:
who sits where, where the window is, which way the light comes from. Independently generated shots drift (a
road that is straight in one shot and forks in the next, a door on the wrong side); a shared set does not.

A set builder returns `{ id, title, scene, o, mapView, reset() }` (`starter/js/sets.js`):

- `scene`: its own `THREE.Scene` with background, fog and lights.
- `o`: every object the story touches, by name (`S.o.a`, `S.o.drone`, `S.o.table`). Blocking stays one-liners.
- `mapView`: centre and half-size of the top-down map in metres.
- `reset()`: the neutral state (seated poses, props home, drone hidden). Called before every frame's blocking.

Several locations = several builders, and each shot names its set. Interiors with a ceiling or a closed tunnel:
hide the ceiling for the map, or the map camera looks at a roof (one previz started its map view outside a tunnel
set and showed nothing).

## Build it from the master plate, in real metres

1. Get or make one master image per location (a wide establishing plate, no hero action). Describe its layout as
   numbered elements: "1 round table at the centre, 2 tall window behind, 3 counter on the right wall…".
2. Rebuild those elements as boxes, cylinders and cones in metres, positioned as in the plate. Use real sizes: a
   door is 2.1 m, a table 0.75 m, a chair seat 0.45 m, a ceiling 2.7–3 m.
3. Add depth cues (a pillar, plants, a background block) and something on every wall a camera will face. An
   over-the-shoulder that looks at an empty void has nothing for the video model to redraw consistently.
4. Light for readability: a `HemisphereLight` fill so no side goes black, plus one key light from the plate's
   light direction. A lit mesh with one light and no fill renders as a black cutout when the camera faces the
   light. A dark subject on a dark background disappears: one previz lost its antagonist outside a window
   against black space until it got a rim light.
5. Colour code like the film (our side, enemy, the brand colour) but keep the luminance contrast too.

Making the plate from the set works better than the other way round once the set exists: render the blockout from
each camera (`bun tools/capture.ts --stills --size 1536x864`) and image-edit it (`gpt_image_2_5` or
`nano_banana_2_1` on varg) with the render as the **first** file and "keep the camera and the geometry exactly;
grey blocks = …" plus a mapping of every block. An environment image alone as the reference still drifted:
both models re-invented the layout per camera. The render as the first file held it.

## Blocking: once, in world time

```js
export function BLOCKING(S, T) {          // T = seconds from the start of the film
  const look = smooth(ramp(T, 4.4, 4.9));
  pose(S.o.b, [['sit', 1], ['handsOnTable', 1], ['lookUp', look]]);
  S.o.drone.position.copy(FLIGHT.getPointAt(smooth(ramp(T, 3.0, 8.6))));
}
```

The action runs on one clock; each shot is only a camera on it. When shot 2 cuts to a closer angle at 4.0 s, the
person is in exactly the pose they had at 4.0 s in the wide: match cuts and continuity come free.

- Time helpers: `ramp(x, a, b)` (0→1 between a and b, clamped), `smooth` (smoothstep), `win(x, a, b)` (up, hold,
  down), `pulse(T, every, len)` (a nod on every bar).
- Put events on beats: `const HIT = 7 * BEAT;`, never a literal near a cut. Cut times live in the shot list only.
- A per-shot cheat (move a prop out of a close-up, hide the far wall for a reverse) goes in
  `shot.cheat(S, { lt, k, T })`, which runs after `BLOCKING` for that shot only. Use cheats sparingly: a cheat the
  wide does not show is fine, a cheat that breaks the geography is the drift you built the set to avoid.
- Moving objects follow curves (`CatmullRomCurve3.getPointAt(u)`, arc-length for even speed) and face their
  direction with yaw from a fixed function of T, not from the previous frame.
- A speed that changes is integrated in closed form. `angle = T * speed * k` runs backwards while k falls;
  `angle = speed * ∫k dT` does not (the starter's rotor spin-down).
- Speed without moving the hero (a corridor rushing past): scroll the environment by `(T * speed) % repeatLength`.
- Flashes and blackouts: a sphere around the camera with `depthTest: false` and a high `renderOrder`.
- Many repeated objects: `InstancedMesh`; scatter with the seeded `rng(seed)`, never `Math.random`.

## Labels and text

Name tags, sign text and UI cards help the review ("A", "B", "DRONE"). Make them sprites or planes flagged
`userData.label = true`; the export hides them. Text inside a video-to-video reference comes back as garbled
letters, so all real text (titles, captions, UI, logos) is drawn later in the edit (HyperFrames or the varg
render), never generated.

## The set map is the review tool

The top-down map with every shot's START/END frustum answers the questions a single frame cannot: is every camera
on the same side of the 180° line, does the close-up sit where the wide says it does, is a camera inside a wall
or behind a headrest, does a subject walk into the lens. The automatic warnings (`checkShot`: out of frame, on the
edge, blocked by an object, camera inside geometry) catch most of these; the map catches the rest.
