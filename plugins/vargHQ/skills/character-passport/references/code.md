# Building characters and props in code

Build in code when the shape must be exact, reused many times, or posed from angles a model guesses wrong; then let
an image model dress it in the film's look. Everything in `code/` ran headless on a Mac on 2026-11-03 unless marked.
Renders: [blockout](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_2669c59e4146.png) ·
[blockout dressed by Nano Banana 2.1](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_265074df079d.png) ·
[VRM expressions](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_f559ba3dd2ff.png) ·
[SVG face rig](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a71881615326.png) ·
[PBR prop](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_0059e2390392.png) ·
[image to 3D turnaround](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_ff2b21e343fb.png).

## The edit step that turns a blockout into the character (ran: Nano Banana 2.1, $0.05)

Upload the blockout render, pass it as Image 1, and write:

```text
Image 1 is a 3D blockout turnaround made in code: keep its exact layout, four panels, camera angles, proportions,
pose, silhouette and the <prop>'s size and position in every panel. Turn it into a photoreal character turnaround of
a real <person>, same four views (front, side, back, face close-up). Remove the panel labels; no text. <passport>.
<backdrop and light from the moodboard>, film grain, visible skin pores, no retouching.
```

Result: same pose, proportions and lantern placement, a photoreal man, labels removed. For video, keep blockouts grey:
coloured blockouts get copied 1:1 by video models ([@AIWarper](https://x.com/AIWarper/status/2106466748207935789)).
The VRM sample models are not shipped here: get the CC0 VRoid base models from OpenGameArt ("VRoid Studio CC0
models") or make your own in VRoid Studio, put them in `code/models/`, and open `vrm_expressions.html?model=models/<file>.vrm`.


All of these ran here unless marked otherwise. The headless renderer is `code/shoot.ts`: Bun serves the folder, then playwright-core drives Playwright's chrome-headless-shell with `--use-angle=swiftshader --enable-unsafe-swiftshader` and waits for `window.__done`.

```bash
cd code && bun add playwright-core          # once
bun shoot.ts blockout_turnaround.html out.png 1600 600
```

The plain Chrome CLI also works for pages that don't fetch local files:
`chrome-headless-shell --use-angle=swiftshader --enable-unsafe-swiftshader --window-size=1600,600 --virtual-time-budget=10000 --screenshot=out.png file:///…/blockout_turnaround.html`. It took 1.4 s.

### Route 1: a three.js blockout turnaround, used as the first reference for an image edit. **Ran.**

- **Good for:** locking proportions, silhouette, costume layers and where props sit, before any AI image. The figure has a real head, nose, ears, beard, eyes, a hat brim, arms with elbows, hands, legs and boots, because image models turn a bare cylinder into a "log". It renders front, side, back and a face close-up with orthographic cameras.
- **License:** three.js is MIT. The ES module loads from jsdelivr, so there is nothing to install.
- **Files:** `code/blockout_turnaround.html`. Add `?solo=1` to get one clean front view on white (`code/blockout_front_clean.png`, the input for Route 5).
- **Render:** `code/blockout_turnaround.png` (1600×600, four panels, old fisherman in a sou'wester and oilskin, holding a storm lantern).

```js
import * as THREE from 'three';           // importmap -> cdn.jsdelivr.net/npm/three@0.187.0
const cap = (r, len) => new THREE.CapsuleGeometry(r, len, 6, 16);
// limbs with joints: shoulder group -> upper arm -> elbow group (bend) -> forearm -> hand
const shoulder = new THREE.Group(); shoulder.position.set(0.40, 1.80, 0); fig.add(shoulder);
add(cap(0.09, 0.32), COAT, 0, -0.22, 0, shoulder);
const elbow = new THREE.Group(); elbow.position.y = -0.45; elbow.rotation.x = -1.2; shoulder.add(elbow);
// prop: parent it to the hand so it follows every pose
const lantern = new THREE.Group(); rightHand.add(lantern);
// four orthographic views, one renderer, scissor per panel
cams.forEach((cam, i) => { renderer.setViewport(i*W/4, 0, W/4, H); renderer.setScissor(i*W/4, 0, W/4, H); renderer.render(scene, cam); });
```

**Next step (ran later, see the edit step above):** pass the turnaround PNG as image 1 to GPT Image or Nano Banana with an instruction along these lines: "Keep image 1's exact proportions, pose, silhouette, hat-brim shape, boot height and the lantern in the right hand. Keep the four-panel layout and the flat orthographic cameras. Render a real 65-year-old Breton fisherman: yellow PVC oilskin creased at the elbows, salt-stained rubber boots, grey beard…" Approve the stills before any animation. To turn a blockout or previs into video, varg has `minimax_h3_max_3d_to_video` (from $0.90 per run, same layout and camera, reference images set the look).

### Route 2: VRM avatars with @pixiv/three-vrm, rendered as a six-expression sheet. **Ran with two models.**

- **Good for:** an exact, repeatable face and costume in any pose, expression or angle, with a built-in lip-sync viseme set. Use it as a pose and expression reference for image models, or render it directly as a stylised character.
- **Spec check (VRMC_vrm-1.0/expressions.md):** emotions `happy angry sad relaxed surprised` (renamed from 0.x: joy→happy, sorrow→sad, fun→relaxed; surprised is new in 1.0); visemes `aa ih ou ee oh`; `blink blinkLeft blinkRight`; `lookUp lookDown lookLeft lookRight`; `neutral` is kept for backward compatibility. Override rules (`overrideMouth/Blink/LookAt`: none/block/blend) let an emotion suppress blinking or lip-sync.
- **License:** three-vrm is MIT (v3.5.5, three 0.187). Sample models:
  - Seed-san from vrm-c (VRM Public License 1.0, VirtualCast), at `code/models/Seed-san.vrm`.
  - **CC0** VRoid `Base_Male.vrm` from OpenGameArt "VRoid Studio CC0 models", at `code/models/base_male/Base_Male.vrm`. It has neutral, a/i/u/e/o, blink, angry, fun, joy, sorrow, and a custom "Surprised".
  - CC0 100Avatars (`code/models/100avatars_rose.vrm`) only have visemes and blink, so they can't make an emotion sheet.
- **Files:** `code/vrm_expressions.html` (`?model=` picks the model).
- **Renders:** `code/vrm_expressions.png` (Seed-san) and `code/vrm_expressions_cc0_male.png` (CC0 male). Each is a 3×2 sheet: neutral, happy, angry, sad, relaxed, surprised. About 4 s each.

```js
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';   // cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.5.5/lib/three-vrm.module.min.js
loader.register((p) => new VRMLoaderPlugin(p));
const vrm = (await loader.loadAsync(MODEL)).userData.vrm;
VRMUtils.rotateVRM0(vrm);                                         // VRM 0.x faces -Z; this turns it to +Z
const flip = vrm.meta?.metaVersion === '0' ? -1 : 1;              // gotcha: arm rotations mirror on VRM 0.x
vrm.humanoid.getNormalizedBoneNode('leftUpperArm').rotation.z = -1.2 * flip;   // out of the T-pose
for (const [name, w] of sheet) { reset(); vrm.expressionManager.setValue(name, w); vrm.update(0); renderPanel(); }
```

Gotchas: VRM 0.x has no `surprised` preset (VRoid exports it as a custom `Surprised`, so match names case-insensitively). Without `flip`, the arms go up instead of down on 0.x models. You make your own character in **VRoid Studio** (free, pixiv), export VRM, and get the full expression set.

### Route 3: an SVG face rig driven by FACS action units. **Ran.**

- **Good for:** a consistent 2D expression sheet, for a mascot, an explainer character, or a guide drawing for an image model ("match these brow and mouth shapes"). The head never changes; only the action-unit (AU) values do.
- **License:** your own code (standard-library Python only, no dependencies).
- **Mapping:** AU1 inner brow up, AU2 outer brow up, AU4 brows down and together (plus frown lines), AU5 upper lid up, AU6 cheeks up (lower lid rises), AU7 lids tighten, AU9 nose wrinkle, AU10 upper lip up, AU12 lip corners up and wider, AU15 corners down, AU17 chin raise, AU20 lips stretch, AU23 lips tighten, AU25 lips part, AU26 jaw drop.
- **Recipes (EMFACS prototypes):** happy 6+12(+25), sad 1+4+15(+17), angry 4+5+7+23, surprised 1+2+5+26, disgusted 9+10+15(+4+7).
- **Files:** `code/face_rig.py` writes `code/face_sheet.svg`. The PNG comes from the headless shell: `chrome-headless-shell --window-size=960,760 --screenshot=face_sheet.png file:///…/face_sheet.svg`.
- **Render:** `code/face_sheet.png` (six faces, each labelled with its AU recipe).

```python
EXPRESSIONS = {"happy": {"AU6": .8, "AU12": 1, "AU25": .4}, "sad": {"AU1": 1, "AU4": .5, "AU15": .9, "AU17": .4}, ...}
inner_y = by - 24*a("AU1") + 16*a("AU4")          # brow inner end
outer_y = by - 14*a("AU2") + 6*a("AU1")*(1-a("AU2")) - 4*a("AU4")
up      = 16 + 10*a("AU5") - 8*a("AU7") - 5*a("AU6")   # upper-lid opening
corner  = my - 18*a("AU12") + 16*a("AU15")             # mouth corners
open_   = 4*a("AU25") + 28*a("AU26")                    # mouth opening
```

### Route 4: procedural props with real PBR materials. **Ran.**

- **Good for:** props that stay identical from shot to shot and look worn rather than "AI plastic". Poly Haven or ambientCG maps give paint, rust and edge wear. physicallybased.info gives measured base colours and metalness. Increase roughness by hand to age a material: the database lists polished brass at roughness 0, which was raised to 0.42 here.
- **License:** CC0 maps and CC0 values, with three.js (MIT).
- **Files:** `code/prop_pbr.html` fetches `api.polyhaven.com/files/green_metal_rust`, the `studio_small_09` HDRI and `api.physicallybased.info/materials` live (CORS is open on all three).
- **Render:** `code/prop_pbr.png` (a worn tackle box with brass fittings, in 3/4, side and top views).

```js
const tex = await fetch('https://api.polyhaven.com/files/green_metal_rust').then(r => r.json());
const paint = new THREE.MeshStandardMaterial({ map: diff /* tex.Diffuse['1k'].jpg.url */, roughnessMap: rough, normalMap: nor, metalness: 0.3 });
const brass = (await fetch('https://api.physicallybased.info/materials').then(r => r.json())).find(m => m.name === 'Brass');
new THREE.MeshStandardMaterial({ color: new THREE.Color().setRGB(...brass.color, THREE.SRGBColorSpace), metalness: 1, roughness: 0.42 });
scene.environment = await new HDRLoader().loadAsync(hdri.hdri['1k'].hdr.url);  // r187: HDRLoader (RGBELoader still ships)
```

For a ready-made prop, load a Poly Haven glTF such as `Lantern_01` with GLTFLoader. `code/glb_turnaround.html?model=…` renders any GLB as an auto-framed four-view turnaround.

### Route 5: image to 3D (approved front image → mesh → turnaround). **Hunyuan3D-2 ran. TRELLIS.2 was blocked by quota.**

- **Good for:** turning one approved front image into a mesh. You can then render any angle, use it as a pose and geometry reference, or put it into previs.
- **Hunyuan3D-2** (Tencent Hunyuan Community License: **not licensed in the EU, UK or South Korea**; check before commercial use). Through the public Hugging Face Space, with no key, it gave 329,960 faces in 6.8 s of GPU time. **The input must be one clean figure on white.** The first try used a crop from the four-panel sheet (grey background, ground line), and the result split the figure into mirrored pieces. The Space quietly ignores its multi-view inputs (it uses the single-view `hunyuan3d-dit-v2-0`).
  - Files: `code/hunyuan3d_space.py` → `code/fisherman_hunyuan.glb` → `code/hunyuan_mesh_turnaround.png`.
- **TRELLIS.2** (Microsoft, MIT, 4B, PBR output). The `code/trellis2_space.py` script is ready, but the anonymous ZeroGPU quota refused it ("exceeded your ZeroGPU quota… authenticate with a Hugging Face token"). It needs an HF token, a 24 GB+ GPU locally, or a hosted API (fal and others list TRELLIS.2).
- **Meshy, Tripo, Hunyuan3D 3.x (hosted):** paid APIs with keys. Not tested. varg doesn't offer image-to-3D (no model in `varg.ai/models/llms.txt`).

```python
# uvx --from gradio_client python hunyuan3d_space.py front.png out.glb
c = Client("tencent/Hunyuan3D-2")
glb, _html, stats, _seed = c.predict(None, handle_file(src), None, None, None, None,
                                     30, 5.0, 1234, 256, True, 8000, False, api_name="/shape_generation")
```

### Route 6: Blender (MPFB, MCP for Blender, Rigify, BlenderKit). **Not run: Blender isn't installed here.**

- **MPFB 2** (MakeHuman for Blender; code GPL-3, generated humans and assets usable as CC0). Parametric realistic humans (age, weight, ethnicity sliders, clothes, skin, rig). Install it as a Blender extension from extensions.blender.org. Repo: `makehumancommunity/mpfb2`, active October 2026.
- **MCP for Blender** (MIT, formerly `ahujasid/blender-mcp`; **renamed and moved to `ahujasid/mcp-for-blender` in September 2026**). Lets an agent model, light, pull Poly Haven and Sketchfab assets, and render. `uvx mcp-for-blender setup` installs the add-on and adds a `blender` entry to Claude Code, Codex and others. The old command `uvx blender-mcp` still runs.
- **Rigify** (built in) auto-rigs a metarig. **BlenderKit** is a free and paid asset library inside Blender (account needed).
- A minimal agent loop with Blender present: `blender -b -P make_char.py`, where the script calls `bpy.ops.object.armature_human_metarig_add()`, generates the Rigify rig, adds MPFB human presets, places 4 orthographic cameras and runs `bpy.ops.render.render(write_still=True)`.

### Status of avatar platforms (2026)

- **Ready Player Me shut down on 2026-01-31**, after Netflix acquired it in December 2025. The creator, PlayerZero and the APIs are offline. Only GLBs exported earlier still work.
- **Mixamo:** still free with an Adobe ID and royalty-free, but in maintenance mode (it broke for everyone briefly in June 2025). No keyless API.
- **VRoid Studio:** still the fastest free way to make your own VRM with a full expression set (pixiv).
- **Open Source Avatars / 100Avatars:** CC0 VRMs, good bodies for posing, but no emotion expressions.
