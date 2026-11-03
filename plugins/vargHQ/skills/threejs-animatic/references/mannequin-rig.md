# The jointed mannequin

A previz person is not a capsule. It is a small hierarchy of pivots you can pose by joint angles, built from
primitives so it costs nothing and reads at any size. Code: `makeMannequin`, `POSE` and `pose()` in
`starter/js/props.js`.

## Hierarchy and sizes (metres, adult ≈ 1.8 m)

```
root (pelvis, origin)              standing: root.y = 0.95 · seated: seat top + 0.05
├─ spine (0, 0.05, 0)              torso capsule r 0.15
│  ├─ neck (0, 0.52, 0)
│  │  └─ head (0, 0.13, 0)         sphere r 0.11 + nose cone + hair cap + two eye dots
│  ├─ shoulderL/R (∓0.21, 0.45, 0) upper arm 0.30
│  │  └─ elbowL/R (0, −0.30, 0)    forearm 0.28
│  │     └─ handL/R (0, −0.29, 0)  hand box: parent props here
├─ hipL/R (∓0.10, 0, 0)            thigh 0.46
│  └─ kneeL/R (0, −0.46, 0)        shin 0.44 + shoe box pointing forward
```

The character faces −Z in its own space and its right hand is +X. Write that convention at the top of
`props.js` and never mix it: half the pose bugs in a previz are a left/right or forward/back sign flip.

## Signs (the starter's convention)

- Hanging limbs (arms, legs) hang along −Y from their pivot. **x > 0 swings them forward/up**: `shoulder.x = 1.5`
  points the arm straight ahead, `hip.x = 1.5` lifts the thigh level (seated).
- `knee.x < 0` bends the shin back; `elbow.x > 0` bends the forearm up.
- Upright joints (spine, neck): **x > 0 leans back / looks up, x < 0 leans forward / looks down.**
- `head.y > 0` turns the face to the character's own left, `< 0` to the right.
- Shoulder z: the right arm (+X) lifts outward with z > 0, the left arm with z < 0.
- Rotations are Euler XYZ. For a vehicle or drone that yaws and then pitches, set `rotation.order = 'YXZ'`, so
  pitch is about its own axis (the starter's drone).

When in doubt, pose one joint, render a still, look at it. Do not reason about signs for more than a minute.

## Poses are data, blended in layers

```js
export const POSE = {
  sit:          { hipL: [1.5, 0, 0.06], hipR: [1.5, 0, -0.06], kneeL: [-1.5, 0, 0], kneeR: [-1.5, 0, 0], ... },
  handsOnTable: { shoulderL: [0.75, 0, -0.12], elbowL: [0.65, 0, 0], ... },
  lookUp:       { neck: [0.5, 0, 0], spine: [0.1, 0, 0] },
};
pose(m, [['sit', 1], ['handsOnTable', 1 - k], ['gestureR', k], ['lookUp', look]]);
```

Each layer lerps only the joints it names toward its values by its weight; later layers win. Weights come from
time ramps (`smooth(ramp(T, 4.4, 4.9))`), so a pose change is a blend over a few frames, never a pop. After
`pose()`, add small extras directly (`j.head.rotation.y = -0.6 * look`).

Useful library to start from: `stand`, `sit`, `handsOnTable`, `gestureR`, `cupR`, `lookUp`, `nod`, `leanBack`,
`handsUp`, `point`. Add `walk` as a function of time, not a pose:

```js
function walk(m, T, stride = 1) {         // one cycle per two beats, seek-safe
  const ph = (T / (2 * BEAT)) * Math.PI * 2, j = m.userData.j;
  j.hipL.rotation.x = Math.sin(ph) * 0.42 * stride;  j.hipR.rotation.x = -Math.sin(ph) * 0.42 * stride;
  j.kneeL.rotation.x = -Math.max(0, -Math.sin(ph + 0.6)) * 0.7 * stride;
  j.kneeR.rotation.x = -Math.max(0, Math.sin(ph + 0.6)) * 0.7 * stride;
  j.shoulderL.rotation.x = -Math.sin(ph) * 0.3; j.shoulderR.rotation.x = Math.sin(ph) * 0.3;
  m.position.y = 0.95 + Math.abs(Math.cos(ph)) * 0.03;
}
```

Position along a path comes from the same T (`curve.getPointAt(u)`, arc-length, so the speed is even).

## Props in hands

Parent the prop to the hand joint (`j.handR.add(cup)`) for a shot where it is held, or copy the hand's world
position each frame (`j.handR.getWorldPosition(v)`) when it is put down. Keep held props simple and few.

## Make it readable, for people and for the video model

The animatic is read twice: by the director, and later by Seedance as `@video1`. What we learned:

- **Real limbs, head, nose and feet.** Featureless capsules come back from image and video models as logs,
  bollards or rope-wrapped bundles. A nose gives the head a readable direction; shoes show where the body faces.
- **Separate characters by luminance, not only hue.** The reference clip is sent greyscale (see
  seedance-v2v-pack.md), so a light top against a dark top survives, red against green does not.
- **Clean poses.** Seedance copies the previz pose literally. Arms crossed behind a helmet came back as tangled
  extra arms; a hand holding a glowing card came back as a glowing artefact through the fist. If a pose or a held
  prop is ambiguous, simplify it in the previz and say the detail in the prompt ("he puts the helmet on with both
  hands, exactly two hands").
- **Scale is explicit.** Put a 1.8 m mannequin next to every vehicle, product or creature in the set, and keep
  real sizes (a chair seat at 0.45 m, a table at 0.75 m, a car about 1.5 m tall). A model draws a man as big as
  his ship unless the reference shows the ratio.
- **Faces stay schematic.** Two eye dots and a nose are enough for direction and eyeline. Identity comes from the
  character sheet image, never from the mannequin.
- **Ink outlines** (`EdgesGeometry` lines on every mesh, skipped for eyes and glows) make the grey-box read like
  storyboard line art and help the model find silhouettes. Skip ink on `InstancedMesh`.
