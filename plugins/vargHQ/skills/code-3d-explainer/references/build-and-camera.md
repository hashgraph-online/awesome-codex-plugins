# Building the subject, the look, and the camera tour

Everything here is in `examples/animal-cell/` (`cell.js` = the subject, `lib/materials.js` = the look,
`lib/explainer.js` = camera, labels, post). Copy the folder and replace `cell.js`, `story.json` and
`factsheet.md`.

## Building parts in code (no downloaded models)

Real units in the scene (1 unit = 1 µm for a cell, 1 Å for a molecule, 1 m for a machine) so the scale bar
and the fact sheet agree. Every part is a `THREE.Group` that `update(t)` poses from t alone.

| Part shape | Recipe (cell.js) |
|---|---|
| Lumpy closed surface (membrane, envelope) | `IcosahedronGeometry(1, 64)`, each vertex pushed to `memR(dir)`, a sum of 3 low sines of the direction. Keep `memR` as a function: the cutaway faces and "is this point inside?" use it |
| Shell with holes in it (nuclear pores) | `InstancedMesh` of tori on Fibonacci-sphere points, oriented to the normal |
| Folded sheets (ER) | a parametric patch in spherical coordinates around an axis (θ, φ ranges per layer), radial waves `0.12·sin(5φ)·sin(3θ)`, ragged edges by discarding near the uv border with noise |
| Stacks (Golgi) | `LatheGeometry` of a flat sac with a swollen rim, squashed to an ellipse, bent `y -= 0.22x²`, stacked 0.3 apart. **Profile bottom → top**, or every face is a back face (it rendered as one flat colour until we reversed it) |
| Beans (mitochondria) | `CapsuleGeometry` bent `x += k·y²`; cristae as thin dark noise-warped stripes in the shader |
| Sacs with contents (lysosomes) | translucent shell + an `InstancedMesh` of granules inside. Opaque orange spheres read as fruit |
| Many tiny things (ribosomes) | one `InstancedMesh`, low-poly icosahedra, matrices set per frame from t |
| A chain (polysome) | 9 ribosomes on a helix + a thin glowing tube for the mRNA through them |
| Filaments (microtubules) | `TubeGeometry` on a quadratic Bézier; draw-on with `geometry.setDrawRange(0, 6·radial·k)` |
| Volume haze | `Points` with a soft-disc shader, additive, sized in world units |

Placement: **heroes first** (the parts the camera visits, at hand-picked positions), then scatter the rest
with seeded rejection sampling (inside the cell, clear of the nucleus, clear of each other). And **reject
anything near the camera path**: sample the camera every 1/30 s and keep scattered parts ≥ 1 µm (plus
their radius) away. A random mitochondrion 0.4 µm from the lens filled half a frame before this rule.

Entrances, each on its own beat: grow with `outBack` (`pop`), slide in with a stagger (Golgi cisternae
0.12 s apart), draw on (filaments), reveal-sweep with a glowing orange front (membrane top→bottom; ER
outward from the nucleus, so it visibly grows from the nuclear envelope it is joined to), pop instanced
items with hashed per-instance delays.

## The look ("science-clear")

- Near-black background `#05080b`, a faint teal backlight in the grade pass where the frame is dark,
  vignette 0.34, deterministic grain 0.022 (seeded by the frame number).
- Two accents: warm orange `#ff5315` (energy, active things, the cut line) and teal (membranes). Colour
  by system: the endomembrane family (ER, Golgi, nuclear envelope) in teals, mitochondria orange,
  nucleolus amber, ribosomes cream. Say "colours invented" on screen.
- Materials are small ShaderMaterials (`lib/materials.js`), no env maps:
  `shell()` translucent fresnel x-ray with half-lambert form, mottling, a soft sheen and a reveal sweep;
  `solid()` wrap light + sky fill + rim + soft spec, optional stripes, **back faces drawn as a flat cut
  cap**; `glow()` additive lines; `bokeh()` soft points.
- Post: MSAA render → BokehPass depth of field (focus = distance to the look-at point) → UnrealBloom
  (threshold 0.72, strength 0.5) → OutputPass (Neutral tone mapping keeps the brand orange) → grade.
  Transparent shells must not write the DOF depth (`userData.noDepth`), or the whole interior takes the
  membrane's focus.
- Bloom traps we hit: a sharp specular on a big sphere became a light bulb (soften: power 36, 0.16);
  cream ribosomes and bright lysosomes bloomed into glowing balls (darker base colours, threshold up).
- X-ray staging: the membrane is milky (opacity 0.16) while the camera is outside, drops to 0.02 as it
  dives in, comes back to 0.38 for the cutaway; the nucleus goes x-ray to reveal the nucleolus and
  chromatin, then half back.

## The cutaway

A wedge (100°) removed from the containers only: membrane, nuclear envelope, pores, chromatin, nucleolus,
ER. Small parts stay whole (a diorama), which reads better than slicing every mitochondrion.

- Two `THREE.Plane`s through the nucleus axis, shared by every clipped material, `clipIntersection: true`:
  only points on the negative side of both are removed. At angle 0 the planes are opposite and clip
  nothing; animate the angle.
- Cut faces are real geometry rebuilt each frame from the planes: a strip from the nucleus radius out to
  the membrane (ray-marched with `insideCell`), alpha 0.82, plus a half-disc for the nucleus. An `aDist`
  attribute (distance from the cut edge) draws two thin lines at the edge: the bilayer (orange) and the
  double nuclear envelope (light teal). The membrane face must **exclude** the nucleus disc, or it covers
  the nucleus face.
- The nucleolus and chromatin are drawn after the faces (`renderOrder 6`): they sit in the cut plane, and
  a translucent face drawn over them hid the nucleolus completely.
- Turn the wedge ~28° from the final camera direction so one cut face turns toward the camera; a wedge
  aimed straight at the camera reads as a slot.

## The camera tour

Keys in `story.json`: `{ t, pos, look, fov, push }`; `pos`/`look` are `[x,y,z]`, an anchor name, or
`{ "at": anchor, "off": [dx,dy,dz] }`. Print the anchors with
`bun scripts/capture.ts <project> --eval "__film.anchors()"`.

- **Scales**: establish (whole cell, 30°, ~55 µm away) → part by part (1.8–20 µm away, fov 30–40°) →
  the closest shot (ribosomes, 1.7 µm away, fov 40°: the scale bar reads "200 nm") → pull out → cutaway of
  the whole (~50 µm, high 3/4 view). Widen the fov in close-ups so a little context stays in frame.
- **Move-hold-move**: two keys per subject, *arrive* and the same pose with `"push": 0.9` 0.7–1.3 s later
  (a slow drift in), then a 0.6–0.9 s move to the next subject. Interpolation is monotone cubic (PCHIP)
  per component, so the camera never overshoots a key. Plain Catmull-Rom tangents overshot the short hold
  segments; ease-in-out per segment stopped dead at every key.
- **Hold length comes from reading time**, not taste: a label of 8 words needs ~2.1 s readable, so the
  subject must stay in frame about that long (`labels.md`).
- The camera may pass through the membrane (x-ray makes it a soft flash). Keep it ≥ 0.5 µm from any
  surface or the near plane clips it.
- The last shot: start the cut while pulling out, hold ≥ 2.5 s on the labelled whole with a slow orbit.

## Timing used for the cell (21 s, 30 fps)

| t (s) | beat | camera |
|---|---|---|
| 0–2.6 | title; membrane sweeps in | 58 → 38 µm, cell right of centre |
| 3.0–6.6 | nucleus, pores; x-ray; nucleolus | arrive 3.9 / push 4.9; nucleolus 5.9 / 6.6 |
| 6.6–8.9 | rough ER grows from the envelope | 7.6 / 8.85, side view so the sheets stack |
| 8.6–10.7 | Golgi stack slides in, vesicles bud | along the stack's local z: plates as curved bars |
| 10.4–12.0 | mitochondria | 4.7 µm, fov 38 |
| 11.9–14.1 | ribosomes, polysome on mRNA | 1.7 µm, fov 40, scale bar hidden |
| 13.9–15.3 | lysosomes | 2.9 µm |
| 15.1–16.8 | microtubules from the centrosome | pull out to 36 µm |
| 17.0–21.0 | wedge cut opens; end card | 50 µm, slow orbit |
