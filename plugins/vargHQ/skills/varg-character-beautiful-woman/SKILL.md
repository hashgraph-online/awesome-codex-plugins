---
name: varg-character-beautiful-woman
description: >-
  Makes very beautiful AI women who look like real models, not plastic dolls, on varg: striking
  features written one by one, real skin, styling (hair, makeup, outfit) and light that make a
  photo look like a fashion, swimwear or red-carpet shoot, plus the wording that gets these
  prompts past false moderation blocks. Adults only, no nudity. Use when someone asks for a
  beautiful, gorgeous, attractive or hot woman, a model, an AI influencer girl, a glamour or
  swimwear shot, or a woman who looks real and stunning. Part of varg-character-design
  (definition, sheet, reuse in video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY (see varg-ai).
allowed-tools: Bash(curl:*) Read Write Edit
---

# Very beautiful women

Two ways this goes wrong. "Beautiful woman, 8k" gets the model's average face: pleasant and forgettable. "Hot sexy girl" gets blocked on strict models, and where it passes it gives the glossy, poreless, same-face "AI girl" that nobody believes. What works is a **model-casting description plus fashion styling plus real skin**, framed as a shoot.

Sheet, crops and video: `varg-character-design`. Scope: adult women (say the age), clothed (fashion, evening wear, swimwear, sportswear), no nudity, no sexualised posing, no real person's likeness.

## The recipe

**1. Cast her like a model agency would.** Age as a number (22–35) and 4–6 striking features:

- Bone structure: "high cheekbones", "a sharp jawline", "a strong straight nose"
- Eyes: "almond-shaped green eyes", "striking ice-blue eyes", "large dark eyes with long lashes", "thick arched brows"
- Lips: "full lips", "full glossy lips"
- Hair, with a styling verb: "long dark glossy hair in soft waves", "sleek platinum-blonde hair", "sun-bleached hair slicked back and wet", "voluminous dark curls"
- Skin tone and origin, specifically: "sun-kissed olive skin", "bronzed skin", "fair skin with a light flush"

**2. Keep the skin real.** "Visible pores, a few freckles, fine peach fuzz, real skin texture, no plastic smoothing." Beauty with real skin is what makes people stop and believe.

**3. Style her.** Makeup ("glowing natural makeup with defined lashes and a nude-pink lip", "a bold red lip", "cat-eye eyeliner, glossy lips"), one piece of jewellery (gold hoops, a thin gold necklace), and an outfit named exactly:

- Evening: a fitted black satin slip dress; an emerald satin gown with a high leg slit
- Swim: a cherry-red one-piece swimsuit with a high leg cut (name the cut; never "skimpy")
- Night out: a fitted black mini dress (not "tight")
- Day: a white linen shirt open at the collar

**4. Light and lens make it a shoot.** Golden hour with warm backlight in the hair, 85mm, shallow depth of field; or a direct-flash compact-camera look for a candid party photo; or editorial flash on a red carpet.

**5. One confident action**: leaning on a balcony railing, glancing back over her shoulder, laughing with a drink, posing at a premiere.

## Ready characters (all tested on 2026-10-27)

| Look | Model | Prompt (shortened) | Result |
|---|---|---|---|
| Positano editorial | `seedream_5_pro` (7) | strikingly beautiful 26-year-old woman with model looks: high cheekbones, full lips, almond-shaped green eyes, sharp jawline, long dark glossy hair in soft waves, sun-kissed olive skin with visible pores and a few freckles, glowing natural makeup; fitted black satin slip dress, thin gold necklace, leaning on a balcony above the sea at golden hour, confident half-smile, 85mm, warm backlight, no plastic smoothing | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_031f7b085fc9.jpg) |
| Red carpet | `gpt_image_2_5` (24) | strikingly beautiful 29-year-old woman, sleek platinum-blonde hair, sharp cheekbones, ice-blue eyes, bold red lip, real skin texture; fitted emerald satin evening gown with a high leg slit, long gold earrings, film premiere, photographers' flashes, full length, editorial flash | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_9756bc2afefa.png) |
| Beauty close-up | `nano_banana_2_1` (6) | gorgeous 25-year-old Brazilian woman, high cheekbones, full glossy lips, large dark eyes, thick arched brows, bronzed skin with visible pores, voluminous dark curls, gold hoops, white linen shirt, golden-hour sun, 85mm f/2, magazine cover quality | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_eecd41db2878.png) |
| Party, direct flash | `soul` (6) | very attractive 24-year-old woman at a rooftop party at night, long straight black hair, cat-eye eyeliner, glossy lips, small nose ring, fair skin with visible pores; fitted black mini dress, silver hoops, laughing with a drink, city lights, compact-camera flash, slight grain | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_c3c8cd36b9c9.png) |
| Swimwear campaign | `seedream_5_pro` (7) | swimwear brand campaign photo, stunningly beautiful 27-year-old adult woman, athletic figure, wet slicked-back sun-bleached hair, golden tanned skin with pores and water droplets, blue eyes; cherry-red one-piece swimsuit with a high leg cut, knee-deep in turquoise water at sunset, glancing back with a confident smile, Kodak Portra look | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a6ec580e7339.jpg) |

Best for striking glamour with real skin: `seedream_5_pro`. Best for a believable candid: `soul` or `nano_banana_2_1`.

## Getting past false blocks

| Instead of | Write | Why (tested) |
|---|---|---|
| girl, young girl | woman, 26 / adult woman, 26 | "Beautiful girl in a sports bra" was blocked on GPT Image 2.5 |
| sexy, hot, seductive | strikingly beautiful, confident, model looks | crude words get blocked or give the plastic look |
| tight dress | fitted black mini dress | same picture, no trigger |
| bikini | the cut + "swimwear brand campaign" | "bikini" was blocked on GPT Image 2.5, FLUX 3 and Grok |
| booty, cleavage | the pose and the neckline: "glancing back", "square neckline" | describe the photo, not body parts |

Route swimwear to `seedream_5_pro`, `soul` or `nano_banana_2_1`; GPT Image 2.5 and Grok Image 2 block most swimwear. Retry a block once (they are random), then rephrase. Full log: `varg-character-design` → `references/moderation.md`.

## Keep her the same

Make her model sheet with `seedream_5_pro` from the same casting description (the sheet prompt is in `varg-character-design`), then every post from the face and body crops. For an AI influencer, fix one signature: a nose ring, a beauty mark, one hair colour, one jewellery piece.

## Watch out

- The more generic the description, the more the face drifts toward a celebrity; some filters then block it as likeness. Specific features prevent both.
- Label AI models and influencers as AI on Instagram and TikTok; never present her as a real customer in an ad.
