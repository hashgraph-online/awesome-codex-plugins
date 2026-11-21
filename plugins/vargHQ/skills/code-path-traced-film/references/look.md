# The night look, in numbers

Values from `src/shots.js` (`base()`), in the renderer's own units. Exposure 3.4 maps radiance 1.0 to white.

| Setting | Value | Why |
|---|---|---|
| Moon irradiance | 0.42 x (0.44, 0.62, 1.0), cone half-angle about 2.6 degrees | Blue key from behind and left: rims on the characters, backlit blades |
| Sky that lights the scene (`sky`) | 0.46 | Enough fill that shadows are about 8x darker than moonlit grass, not black |
| Sky the camera sees (`skyVis`) | 0.16 | Deep indigo. With one shared gain the sky renders as dusk |
| Fog density / colour gain | 0.007 per unit / 0.10 | Depth without a grey veil |
| Firefly light | colour (1.0, 0.95, 0.30); strength 0.3 dim, 3.6 at the meeting, 7.5 as the last star | Light falls off with distance squared; at 2 units 3.6 lights a face fully |
| Lantern surface emission | 0.7 + 1.0 x strength (0.55 + 0.7 x strength in close-up) | Decoupled from the light it casts, so the lantern keeps its shape on screen |
| Glow in the air (`glowFog`) | 0.0035 (0.002 for wide shots) | Above 0.01 the frame washes out |
| Window light | 2.6 x (1.0, 0.56, 0.20), placed 0.55 outside the wall | Warm against the blue; inside the wall it would light nothing |
| Shadowless fill | (0.03, 0.04, 0.07) from the camera side, close-ups only | Lets a dark insect read against a dark sky |
| Bloom | 0.22 above 0.9 | Halo on the lantern and the window only |
| Vignette, saturation, contrast | 0.42, 1.10, 0.25 | |
| Shadow lift | (0.006, 0.009, 0.022) | Keeps blacks blue and above the codec's floor |
| Grain | none in the render; added in the encode after the temporal filter | |

## Stars

Three layers of hashed cells on the sphere (40, 92 and 170 cells per radian, 24%, 17% and 11% filled),
Gaussian points about one pixel wide, brightness `0.02 + 1.45 x r^6`, twinkle 35%. A Milky Way band adds
40% more inside it. The moon is drawn about five times its real size.

## Samples

20 per pixel is the base. Shots get a multiplier: 2.5 for the close-up with out-of-focus stars, 2.0 for the
pond (mirror reflections), 1.5 for the moon shot and the meeting. Everything else is 1.0.
