---
name: imagera-influencer-studio
description: "Build an AI influencer from 31 kinds of choices, or start from a photo. You get a Character ID sheet that keeps the same face in every image and video. Use when: \"Influencer Studio\", \"Design a person once. Use them in every photo and video.\", \"Make a character sheet from these photos\", \"I need a consistent character for my series\", \"Character reference sheet, 4K\", \"influencer studio\", \"influencer-studio\". Runs the Imagera \"Influencer Studio\" template (one reference sheet and a 4K upscale, about a minute)."
---

# Influencer Studio

Build an AI influencer from 31 kinds of choices, or start from a photo. You get a Character ID sheet that keeps the same face in every image and video.

## When to use

Build an AI influencer from 31 kinds of choices, or start from a photo. You get a Character ID sheet that keeps the same face in every image and video.

## How to run it

- Ask for one clear reference picture of the character, or a description when there is none: Age, build, hair, skin tone, wardrobe and the one detail you would recognise them by. To build from up to 6 pictures, create the ID on /character-id instead.
- The sheet is ONE collage — angles and details at one light and scale. It runs on the sharpest 4K image model on Pro and up; below that plan, or if that model declines, Typeset 3 makes it instead, and the Upscale step finishes it at 4K.
- To reuse it with @handle in Sandbox and the upload picker, save it as an ID on /character-id ("Use an existing sheet"), or create the ID there directly.
- Afterwards, pass the sheet as the first reference image to any edit, reference or image-to-video model (video: Imagera Warlord Pro Reference) and name it in the prompt as "reference image 1".
- Never invent a real person’s likeness from a name, and never make intimate imagery of a real person.
- Collect the guided choices by their offered labels; multiple choices use comma-separated labels. Ask for a name only when saving the ID — never draw it on the sheet.

## Inputs

- `references` (image, optional) — a reference picture of the character
- `charactertype` (one of: Average, Bold, Extreme, Insect, Frog, Cat, Dog, Rodent, Bird, optional) — character type
- `gender` (one of: Female, Male, Trans man, Trans woman, Non-binary, optional) — gender
- `build` (one of: Any, Slim, Athletic, Muscular, Curvy, Heavy, Ultra muscular, Centaur, optional) — build
- `hairstyle` (one of: Any, Bob, Bald, Buzz cut, Bowl cut, Mullet, Braids, Pigtails, Afro, Mohawk, Volume waves, Beehive, Perm, Long hair, Short hair, Hair horns, Soft-serve swirl, Curl sphere, Mouse-ear puffs, Hair wings, Hedgehog spikes, Side tufts, Stair steps, Shelf bob, Corkscrews, Side coil, Mushroom, optional) — hairstyle
- `haircolor` (one of: Any, Jet black, Dark brown, Chestnut, Ginger, Red, Blonde, Platinum, Grey, White, Pastel pink, Lilac, Blue, Green, optional) — hair color
- `style` (one of: Any, Retro, Sporty, Y2K, Theatre, Goth, Suits, Streetstyle, Casual, optional) — style
- `ethnicity` (one of: Any, African, Asian, European, Indian, Middle Eastern, Mixed, optional) — ethnicity
- `age` (one of: Any, Adult, Mature, Senior, optional) — age
- `skin` (one of: Any, Porcelain, Fair, Light, Olive, Tan, Brown, Deep brown, Ebony, optional) — skin color
- `height` (one of: Any, Petite, Short, Average, Tall, Very tall, optional) — height
- `bodyshape` (one of: Any, Hourglass, Pear, Apple, Straight, V-shape, Very curvy, optional) — body shape
- `bust` (one of: Any, Small, Medium, Full, Large, Very large, optional) — bust
- `chest` (one of: Any, Flat, Defined, Broad, Barrel, Huge pecs, optional) — chest
- `waist` (one of: Any, Tiny, Slim, Average, Thick, optional) — waist
- `hips` (one of: Any, Narrow, Average, Wide, Very wide, optional) — hips
- `glutes` (one of: Any, Flat, Round, Full, Athletic, optional) — glutes
- `muscle` (one of: Any, Soft, Toned, Defined, Ripped, Bulky, optional) — muscle
- `bodyfat` (one of: Any, Very lean, Lean, Average, Soft, Plus size, optional) — body fat
- `arms` (one of: Any, Slender, Toned, Muscular, Huge, optional) — arms
- `legs` (one of: Any, Slender, Toned, Muscular, Thick thighs, optional) — legs
- `bodydetails` (text, optional) — body details (comma-separated labels: Six-pack, Sleeve tattoo, Small tattoos, Veiny arms, Body hair, Tan glow, Stretch marks, Birthmark)
- `posture` (one of: Any, Upright, Relaxed, Confident, Slouched, optional) — posture
- `proportions` (text, optional) — proportions (comma-separated labels: Long limbs, Short legs, Broad shoulders, Tiny waist, Egg body)
- `headshape` (one of: Any, Standard, Long, Tiny, High forehead, Caveman, Gigachad, Mega jaw, Round, Square, Heart, optional) — head shape
- `neck` (one of: Any, Standard, Column, Long, Short, optional) — neck
- `eyeshape` (one of: Any, Almond, Round, Monolid, Close-set, Wide-set, Uneven, Large, Huge, Hooded, Upturned, Downturned, optional) — eye shape
- `eyecolor` (one of: Any, Black, Brown, Hazel, Green, Blue, Ice blue, Amber, Grey, optional) — eye color
- `features` (text, optional) — features (comma-separated labels: Freckles, Dimples, Heavy eye bags, Blush, High cheekbones, Full lips, Thick brows, Beauty mark, Potato nose, Button nose, Pointy nose, Tiny nose, Pouty lips, Tiny pursed mouth, Wide mouth, Unibrow, Thin high brows, Brush brows, Jug ears, Uneven ears, Gap teeth, Buck teeth, Pointy chin, Weak chin, Big forehead)
- `facialhair` (one of: Any, Clean, Stubble, Full beard, Goatee, Moustache, Pencil, Push-broom, Braided, optional) — facial hair
- `distinctive` (text, optional) — distinctive features (comma-separated labels: Odd eyes, Face tattoo, Piercing, Ear piercing, Brow slits, Bleached, No brows, Gold grill, Braces, Brow scar, Face gems, Elf ears, Big lashes, Nose tape)
- `accessories` (text, optional) — accessories (comma-separated labels: Glasses, Headphones, Jewelry, Hat, Bag)
- `details` (text, optional) — additional details — Anything the choices above do not cover. Optional.

## Steps

1. Character Sheet
2. Upscale 4K

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "influencer-studio"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/influencer-studio` in Superagent, or open it from https://imagera.ai/skills.
