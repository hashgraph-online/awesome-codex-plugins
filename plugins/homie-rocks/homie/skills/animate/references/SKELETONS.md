# The skeleton standard

`@homie-rocks/studio`'s `lib/rig.mjs` reads a rig and maps it; `lib/clips.mjs` retargets; `assets/animate.ts` plays.

## Humanoid (VRM 1.0 bone names)

Required (a rig missing more than one is not a humanoid): hips, spine, head, leftUpperArm, leftLowerArm, leftHand,
rightUpperArm, rightLowerArm, rightHand, leftUpperLeg, leftLowerLeg, leftFoot, rightUpperLeg, rightLowerLeg,
rightFoot. Optional: chest, upperChest, neck, jaw, leftEye, rightEye, leftShoulder, rightShoulder, leftToes,
rightToes. Sockets: leftHandSlot, rightHandSlot (a rig's weapon or prop bones), else the hand; head; back (the
upper chest, chest or spine). Fingers and anything unmatched keep their own names.

| Standard | Mixamo | KayKit | Blender / Rigify | Unreal | Meshy (seen 2026-10-03) |
| --- | --- | --- | --- | --- | --- |
| hips | Hips | hips | pelvis / hips | pelvis | Hips |
| spine, chest, upperChest | Spine, Spine1, Spine2 | spine, chest | spine, spine.001… | spine_01… | Spine02, Spine01, Spine (from the hips up) |
| neck, head | Neck, Head | head | neck, head | neck_01, head | neck, Head |
| leftUpperArm | LeftArm | upperarm.l | upper_arm.L | upperarm_l | LeftArm |
| leftLowerArm | LeftForeArm | lowerarm.l | forearm.L | lowerarm_l | LeftForeArm |
| leftHand | LeftHand | wrist.l | hand.L | hand_l | LeftHand |
| leftUpperLeg | LeftUpLeg | upperleg.l | thigh.L | thigh_l | LeftUpLeg |
| leftLowerLeg | LeftLeg | lowerleg.l | shin.L | calf_l | LeftLeg |
| leftFoot, leftToes | LeftFoot, LeftToeBase | foot.l, toes.l | foot.L, toe.L | foot_l, ball_l | LeftFoot, LeftToeBase |

Names match without case or separators; prefixes (`mixamorig:`, `Armature|`, `DEF-`) are dropped. The spine chain is
assigned by the tree, never by its numbers: the joints between the hips and the neck are spine, chest and upper chest
in that order from the hips.

## Mini (one piece a limb)

hips (Kenney's `root`), spine (`torso`), head, leftUpperArm (`arm-left`), rightUpperArm, leftUpperLeg (`leg-left`),
rightUpperLeg. Skinned (Kenney mini characters) or rigid parts (Kenney blocky and graveyard characters). Humanoid
clips retarget onto it: each limb AIMS where the source's whole limb points (shoulder to hand, hip to foot), so a bent
elbow never swings a stiff arm out sideways.

## Quadruped

body, neck, head, tail, frontLeftLeg, frontRightLeg, backLeftLeg, backRightLeg (Kenney cube pets: `leg-front-left`).
Its own clips only: humanoid clips never fit four legs.

## How retargeting works (lib/clips.mjs)

1. Both rigs are read as their node trees with rest poses (nothing is rendered: plain matrix and quaternion math, so
   it runs in Node, a cloud session and CI).
2. Their rest poses are lined up bone by bone: each target bone's rest direction (towards the next bone of its limb)
   is turned onto the source's. A T-pose clip on an A-pose rig keeps its arms down. Bones with no next bone (a head,
   a hand) are not lined up: their own rest stands.
3. Every frame (30 a second), each bone turns in the WORLD the way the source's turned from its rest, applied to the
   target's (lined-up) rest; turned back into each bone's parent's space.
4. The hips move by the source's motion scaled by the two rigs' leg heights (a chibi bobs a chibi's height). A
   looping clip's drift across the ground is removed: the game moves bodies.
5. Tracks that never leave the rest pose are dropped; quaternions are kept on one side (no long-way blends).
6. Two rigs with the same fingerprint (bone names, tree and rest rotations) copy local rotations exactly instead.

A character's skeleton id is `<family>-<fingerprint>`; characters with one id share `public/anims/<id>.glb`.
