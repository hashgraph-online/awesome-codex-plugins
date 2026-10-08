---
name: animate
description: Give a game's characters rigs and clips that move well on a phone — the skeleton standard (one humanoid vocabulary, a mini and a quadruped family), free CC0 animated characters from Homie's starter library made phone-sized (one draw call, helper bones gone) with their clips in one shared clip library per skeleton, the library's CC0 humanoid clips retargeted at build time onto any other rig (a generated character, the person's own), the shared runtime @homie-rocks/studio/animate (idle, walk and run blended by speed, actions on the upper body while running, additive hits, hit-stop, jump, fall and land with squash and stretch, lean, look-at, springs, foot planting, crowd mode), the animation card with looping previews, and tuning a move's feel in the Game Lab. Use when someone wants characters that walk, run, jump, attack or die, asks about rigs, skeletons, bones or retargeting, says the animation looks stiff, floaty or slides, or wants a jump or a hit to feel better.
---

# Animate: characters that move, free first

Read the `style` skill first (decisions) and the `models` skill (where models come from). Characters follow the same
routes: the starter library (free, CC0), the person's own files, or generated on their own fal account under a
budget (`models` skill: `character`, about US$1.44, priced and asked first). Clips are free: they come from the
character itself or from the library's CC0 humanoid set, retargeted at build time.

Commands run in the studio: `npx --no-install homie-studio cast|anim|assets …` (in an app with Homie's tools:
`cast_plan`, `anim_plan`, `anim_add`, `anim_preview`, `character_make`, `asset_add`).

## The skeleton standard

| Family | Bones (standard names) | Who | Clips from |
| --- | --- | --- | --- |
| humanoid | VRM 1.0 names: hips, spine, chest, upperChest, neck, head, leftUpperArm, leftLowerArm, leftHand, leftUpperLeg, leftLowerLeg, leftFoot, leftToes (and right) | KayKit adventurers and skeletons, Mixamo-named rigs, Meshy and Tripo auto-rigs, Blender and Unreal rigs | its own, else KayKit's CC0 set retargeted |
| mini | hips, spine, head, leftUpperArm, rightUpperArm, leftUpperLeg, rightUpperLeg (a limb in one piece) | Kenney mini, blocky and graveyard characters | its own, else humanoid clips retargeted (each limb aims where the source's whole limb points) |
| quadruped | body, neck, head, tail, frontLeftLeg, frontRightLeg, backLeftLeg, backRightLeg | Kenney cube pets | its own species only |
| parts | anything else that moves by its nodes | — | its own only |

Names are matched however a rig spells them (`mixamorig:LeftArm`, `upperarm.l`, `thigh_l`, `LeftUpLeg`), the spine
chain by the tree (Mixamo counts up, Meshy counts down). `references/SKELETONS.md` has every table.

## Bring a character in

```sh
npx --no-install homie-studio assets find "knight" --kind character          # free, CC0, rigged or node-animated
npx --no-install homie-studio assets add <id> kaykit-adventurers/knight --as knight --height 1.45 \
    --keep "1H_Sword,Round_Shield,Knight_Helmet,Knight_Cape" --verbs idle,run,jump,attack,hit,die
npx --no-install homie-studio assets add <id> --file rigged.glb --kind character --rigged --license own --as hero
```

What happens, all free, on this computer (lib/characters.mjs):
- joints renamed to the standard; helper bones that move nothing (IK targets, poles) removed;
- every skinned part and every held thing it keeps (`--keep`: a sword, a shield, a hat: part swaps) merged into ONE
  skinned mesh: one draw call; pictures resized (512 px), meshopt; the pivot at the feet, its height in metres;
- its clips go to its skeleton's clip library `public/anims/<skeleton>.glb` (the verbs the game needs, from its
  `anim.clips` decision and `--verbs`), its own where it has them, else retargeted (`--clips-from` another source);
- both recorded in `assets/manifest.json` with every clip's source and licence; the model names its clip library.

Every character with the same skeleton shares one clip library (the adventurers share one, about 85 KB for twelve
clips): shared clips are the biggest saving in a room of 32.

## Clips

```sh
npx --no-install homie-studio anim plan <id>                       # each character's clips against the game's verbs
npx --no-install homie-studio anim add <id> knight --verbs block,dodge,cast   # more verbs, retargeted, free
npx --no-install homie-studio anim preview <id> --asset knight     # looping previews and a sheet; LOOK at the sheet
```

Verbs: idle, walk, run, jump, fall, land, attack, attack2, hit, die, emote, win, interact, pickup, cast, shoot,
block, dodge, crouch, sit, drive, spawn. Clips are baked in place (the game moves bodies; netplay's host moves
them) at 30 fps; a loop's drift is removed. Look at the preview sheet after retargeting onto a new rig: a shoulder
that flips or a foot through the floor shows there first.

## In the game: @homie-rocks/studio/animate

```ts
import { createModels } from '@homie-rocks/studio/assets';
import { crowd, loadCharacter } from '@homie-rocks/studio/animate';
import { lab } from '@homie-rocks/studio/lab';
import tuning from '../tunables.json';

const T = lab.tunables(tuning);                                   // the Motion group: sliders in the Game Lab
const hero = await loadCharacter(models, './models/knight.glb', { tune: T });   // finds ../anims/<skeleton>.glb itself
scene.add(hero.root);
// every frame, after the game moved the body:
hero.root.position.set(x, jumpHeight, z); hero.face(yaw, dt);
hero.move(groundSpeed); hero.air(onGround, verticalSpeed); hero.update(dt);
// events: hero.jump(); hero.act('attack', { from: 0.15 }); hero.hit(dx, dz); hero.die(); hero.hold('win');
crowd(allCharacters, camera);                                      // far and off-screen ones pose less often
```

- Locomotion blends idle, walk and run by the body's ground speed and plays each at the rate its feet need
  (`walkSpeed`, `runSpeed`: tune them until the feet stop sliding). The defaults (1.5 and 4.2 m/s) are not measured
  on your rig: `anim plan` and `anim preview` print the ground speed each character's walk and run cover on its own
  rig (a guide from its foot bones); start `tune: { runSpeed: <that> }` from it, then look at the feet.
- An action while moving plays on the upper body (the legs keep running); standing, on all of it.
- A hit is an additive flinch over whatever plays, with a hit-stop (`hitStopMs`).
- Jump, fall and land are clips plus springy squash and stretch (`jumpStretch`, `landSquash`, `squashHz`).
- Lean into turns (`lean`), look-at (`lookAt`, head and neck within limits), springs on bones named tail, ear,
  cape, hair (`spring`), and two-bone foot planting on slopes (`ground: (x, z) => height`).
- Copy `ANIM_TUNING` (exported) into the game's tunables.json under the "Motion" group; every number is a slider.
- The `hero-rush-3d` starter shows all of it (`homie-studio game new <id> --from hero-rush-3d`).

## Feel: the Game Lab

A move feels right when its timing does. Give the move a take in `lab.json` (a stage that sets it up, the press that
starts it), report its phases (`lab.phase('RISE')`) and a number (`lab.track('height', h)`), then change its
tunables and run `homie-studio lab check <id> --take <take>`: New (the working tree) beside Today (the last commit),
frame by frame. In the app: the animation card's **Feel** opens `game_lab` on the take that plays that verb. The
person keeps a slider in the lab and it is written into tunables.json: a kept change is code. Read the `lab` skill.

## Generated characters (paid)

The `models` skill's `character` command (or `character_make`): one A-pose concept in the locked style (a library
character as the style reference with `--like`), then Meshy 7.1 image-to-3D with its humanoid auto-rig on the
person's own fal account (about US$1.40; the concept about US$0.035), then everything above for free: the library's
clips retargeted onto its rig. Humanoids with clear limbs only; a creature comes from the library or is rigged by
hand. Look at the concept before paying for the mesh, and at the preview sheet after.

## Budgets (phones)

`homie-studio assets check <id>` holds characters to: a hero 8,000 triangles (5,000 in rooms over 8), 48 bones,
one draw call, 1,024 px pictures; an NPC or creature 3,000 and 32 bones; four influences a vertex (three.js reads no
more); a clip library 1 MB a skeleton (3 MB hard), 30 samples a second; and skinning a frame: the room's players
times the heaviest character, 60,000 skinned vertices and 1,200 bones on a phone, beyond which `crowd()` and lighter
characters are needed. The `perf` skill's measured run on a phone is the real gate.

## Licences, plainly (`references/RIGHTS.md`)

- Clips come from CC0 sources only by default: KayKit (161 CC0 clips in its Character Animations pack; the
  adventurers carry 76), Kenney's animated characters. Retargeting a CC0 clip keeps it CC0.
- Quaternius: its site licence (QAL v1.0, updated 2026-08-28) forbids redistributing the assets as a pack or template:
  never in the library or a public game's repository; reference only.
- Mixamo: never in a public repository (raw files may not be redistributed); allowed only in a private studio's
  shipped build.
- Text-to-motion: almost every open model is non-commercial in effect (trained on AMASS/HumanML3D, or SMPL), so this
  skill offers none of them. HY-Motion is territory-limited (not the EU, the UK or South Korea). Paid services with
  commercial terms (Meshy text to motion on the person's own Meshy plan) are a later phase.

## Never

- Never ship a provider's raw file, never commit one (art/<slug>/raw/ is git-ignored).
- Never use a clip or model under non-commercial terms, never Quaternius, Mixamo or a store EULA in a public game.
- Never spend without a budget, past it, or without a receipt; never generate in a loop.
