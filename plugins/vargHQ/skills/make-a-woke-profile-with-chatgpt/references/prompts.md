# Every prompt in the woke profile set

These are verbatim from `scripts/tiles.json`, which `wokify.py` runs. For ChatGPT: attach the selfie (and the base image when a tile has one), paste the prompt, and replace `{NAME}` and `{PRONOUNS}`. "Image 1" is the base and "image 2" is the selfie. Measured on varg with `gpt_image_2_6` on 2026-11-05.

Every tile that uses the selfie ends with the identity line:

```
Image 2 is a real photo of the person: keep their face, facial features, skin tone, hair color and likeness exactly recognizable. No other changes.
```

## ME (`me`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_b1dc3179b234.png

Settings: aspect 16:9.

```
Edit image 1, this exact character reference sheet "THE ALLY". Replace the character with the person from image 2 in every view: the four turnaround views, the hero portrait and the four expression studies. Use their face, facial structure, eyes, smile and body type. Keep the woke look exactly as in image 1: the short messy teal hair, the round pink glasses, the septum ring, the denim jacket covered in pins, the "THE FUTURE IS FEMALE" T-shirt, the wide jeans, the combat boots and the tote bag. Keep the layout, every label, the poses, the expressions (earnest, outraged, crying), the details panels, the color palette, the background and the lighting exactly as they are.
```

<details><summary>The prompt that made the base image</summary>

```
A polished production-ready character reference sheet and turnaround board for a fictional character called "THE ALLY". The character is in their late twenties, androgynous, with a short teal undercut with dark roots, a silver septum ring, large round pink glasses, freckles, a black slogan T-shirt reading "THE FUTURE IS FEMALE" in white Helvetica Bold, a boxy denim jacket covered in enamel pins, wide-leg mom jeans, scuffed black combat boots and a canvas tote bag. Show full-body front view, 3/4 view, side profile and back view in a clean horizontal lineup, plus a large hero portrait, expression studies (earnest, outraged, smug, crying), close-ups of the pins and the tote, and a color palette with swatches. Labels: FRONT, 3/4 VIEW, SIDE VIEW, BACK VIEW, HERO PORTRAIT, EXPRESSIONS, DETAILS, COLOR PALETTE. Warm cream background, soft studio lighting, clean grid, thin brown borders, professional film pre-production character bible.
```

</details>

## MY FRIENDS (`friends`)

No base image: the selfie is the only input.

Settings: image_size 2048x1152, model `fal:openai/gpt-image-2.6/flare/edit`, quality high.

```
Photorealistic candid smartphone group photo of six friends at a sunny downtown street protest, handmade cardboard signs and rainbow flags in the blurred crowd behind them. Center: the person from the reference photo, their exact face, smile, hair and build, grinning, holding up a handmade cardboard sign hand-lettered "WOKE 3.0". Around them, arms over shoulders, five fictional friends: a they/them art student with teal dyed bangs, a septum ring, round wire glasses and a small pronoun pin; a mustached guy with a center part in a beige cardigan, wired earbuds, holding an iced matcha and a plain canvas tote; a blonde wine mom in oversized glasses holding a glass of rosé and a cardboard sign "WE'D RATHER BE AT BRUNCH"; a bearded organizer in a beanie, a KN95 mask and a plain red T-shirt holding a stack of flyers; a gray-haired boomer in a tie-dye shirt and a floppy sun hat. Everyone is in focus with sharp, natural faces, framed from the waist up so the faces are large. Natural daylight, slight phone-camera grain. The only readable text is the two signs. No logos, brands or real slogans.
```

This tile uses its own identity line:

```
The reference photo is a real person: keep their face and likeness exactly recognizable.
```

## MY LINKEDIN (`linkedin`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_120f3de0966b.png

Settings: aspect 16:9.

```
Edit image 1, this exact professional-network profile page. Replace the woman's profile photo with a professional headshot of the person from image 2 (their exact face, smiling, same circular crop and framing), and use the same headshot in the small avatar next to the post and in the top "Me" menu icon. Change the name "Maya Chen (she/they)" to "{NAME} ({PRONOUNS})" in both places. Keep the plain blue square logo with the white briefcase icon in the top-left corner exactly as it is: it is not any real company's logo, so do not draw a letter logo there or anywhere else. Keep the headline, the rainbow banner, the land acknowledgment, the four icons in the banner, About, Skills, the post text, the right column, the layout, the colors and every other text block exactly as they are.
```

## MY COLLEAGUES (`colleagues`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_77d2968212ef.png

Settings: aspect 16:9.

```
Edit image 1, this exact video-call screenshot. In the bottom-middle tile labeled "Alex" (the man eating cereal), replace that man with the person from image 2: their exact face and hair, in the same maroon hoodie, eating cereal from the same bowl with a spoon, same room and webcam lighting. Change that tile's label to "{NAME} ({PRONOUNS})". Keep the other eight tiles, the slide "UNCONSCIOUS BIAS 101", the toolbar, the REC timer and every other detail exactly as they are.
```

## MY SOCIAL LIFE (`social`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_eb91c87ef673.png

Settings: aspect 16:9.

```
Edit image 1, this exact TV news still. Replace the young protester being interviewed with the person from image 2: their exact face, smile and build, but keep the protester's look: messy teal hair, silver septum ring, the same black "CLIMATE JUSTICE NOW" T-shirt and necklace, holding the same blank cardboard sign. Keep the reporter, the CITY 12 microphone, the chyron "WHY ARE YOU PROTESTING?", the caption "Honestly? I'm here for the community. And the vibes.", the crowd, the cameraman and the lighting exactly as they are.
```

Then a GIF of the result (10 frames, 1024x576, 120 ms):

```
Animate this exact TV news still as a looping GIF: the teal-haired person being interviewed talks enthusiastically to the reporter, their head nods and tilts side to side as they speak, their eyebrows rise and their smile widens, then they return to the first pose so it loops. The reporter holds the microphone steady, the rainbow flags in the crowd sway a little. Same person and face, same people, same chyron WHY ARE YOU PROTESTING? and the same caption text, exactly readable in every frame. Fixed camera.
```

<details><summary>The prompt that made the base image</summary>

```
A photorealistic still from a local TV news street interview at a climate march. A reporter in a trench coat holds a microphone with a fictional "CITY 12" logo toward a young protester with teal hair, a silver septum ring, a black slogan T-shirt and a cardboard sign held backwards so only the blank brown back shows. The lower-third chyron reads "WHY ARE YOU PROTESTING?" and the protester's answer appears as a caption: "Honestly? I'm here for the community. And the vibes." A cameraman is visible out of focus in the background; the crowd has rainbow flags and climate signs. Broadcast lighting, shallow depth of field, slightly overexposed.
```

</details>

## MY FIGURE (`figure`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_bad0ba165f2f.png

Settings: aspect 3:4.

```
Edit image 1, this exact action-figure toy box. Replace the figure with an action figure of the person from image 2: their exact face and smile sculpted in the same realistic collectible-toy style, their own build, wearing the same round glasses, beanie, sherpa fleece vest, flannel shirt, jeans and sneakers, holding the same protest sign in the same pose. The fleece vest is plain with no logo patch, the sneakers have no logo or letter, and the kombucha label reads only "KOMBUCHA" with no brand name. Keep the box, the title, the tagline, the AGES badge, every other accessory and label, the lighting and the framing exactly as they are.
```

<details><summary>The prompt that made the base image</summary>

```
Product photo of a collectible action figure in a blister-pack toy box titled "URBAN PROGRESSIVE" with the tagline "NOW WITH EXTRA OPINIONS!" and an "AGES 25-38" corner badge. The figure: a fictional millennial in round glasses, a beanie, a fleece vest over a flannel shirt, holding a protest sign. Accessories in their own plastic slots: an oat milk latte in a plain paper cup, a canvas tote bag that says "PUBLIC RADIO SUPPORTER", a mini "In This House We Believe" lawn sign, a $14 bottle of kombucha, an N95 mask, a smartphone with a sticker reading "capitalism is broken", and a reusable metal straw. Bright retro toy packaging design in teal and coral, studio product lighting, glossy plastic reflections, every label readable.
```

</details>

## MY CARD (`card`)

No base image: the selfie is the only input.

Settings: aspect 1:1.

```
A glossy collectible trading card photographed on a dark background. The card is titled "THE ALLY" with a rainbow foil border. Portrait of the person from the reference photo with teal-tipped hair, a septum ring, a slogan tee and a tote bag, smiling smugly. Stat grid: "MORAL SUPERIORITY 99", "PRONOUNS 3", "TOTE BAGS 14", "UNREAD BOOKS 23", "LATTE SPEND $412/MO", "ACTUAL ACTIVISM 4". Ability box: "VIRTUE SIGNAL: post a black square. No effect." Rarity: "COMMON". Card number "001/2026". Crisp card printing, foil shine. Square 1:1 format. No real brand names or logos anywhere.
```

This tile uses its own identity line:

```
The reference photo is a real person: keep their face, facial features and likeness exactly recognizable.
```

Then a GIF of the result (8 frames, 768x768, 120 ms):

```
Animate this exact trading card as a short looping GIF: the card slowly tilts left and right in 3D on the same dark background while its rainbow holographic foil border shimmers and a bright diagonal light glare sweeps across the card, then it returns to the first pose so it loops. The card itself does not change: same portrait, same title THE ALLY, same stat grid and numbers, same ability box, same COMMON and 001/2026 text, every letter identical and readable in every frame. Fixed camera, card centered.
```

## MY PET (`pet`)

Shared file (used unless `--fresh`): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_9d6b423528bf.gif

Fresh prompt:

```
A looping animated GIF of a super woke house cat: a plump calico rescue cat with a smug, judging expression, sitting on a sunny indoor windowsill of a cozy city apartment. She wears a rainbow-striped bandana and a round brass collar tag engraved "they/them". Beside her on the sill: a canvas tote bag, a glass of white wine, a small potted pothos, and a stack of unread books; a second sleepy cat naps on the armchair in the background. Animation: she turns her head from the window to look straight at the camera, gives a long, very judgmental slow blink, flicks both ears, swishes her tail in a big arc, then turns back to the first pose so it loops. Photorealistic, soft warm window light, fixed camera, the only text is the tag "they/them".
```

Made directly as a GIF: 12 frames, 768x768, 110 ms.

## MY FAV DRINK (`drink`)

Shared file (used unless `--fresh`): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_c9d3355a33e0.png

Fresh prompt:

```
A premium minimalist coffee advertisement, vertical. A single paper cup on a warm beige seamless background, shot in soft studio light with a hard shadow. The cup sleeve is kraft cardboard with a small rainbow stripe. Handwritten marker on the cup: "{NAME}" misspelled the way a busy barista would, and below it: "OAT MILK · EXTRA HOT · NO FOAM · 1 PUMP · EXTRA SHOT". A small line at the bottom: "$7.50 · SMALL". A tiny line in the corner: "the barista will ask you to repeat it". Editorial product photography, crisp typography.
```

## MY HOME (`home`)

Shared file (used unless `--fresh`): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_5a5171544f15.gif

Fresh prompt:

```
Ultra-detailed photorealistic isometric miniature scale-model diorama of a progressive suburban home, floating on a clean light background. A tidy modern farmhouse with solar panels, a white electric hatchback plugged into a wall charger, a compost bin, raised vegetable beds, a tiny rainbow flag by the door, a hand-painted Little Free Library, and on the perfect lawn the famous black yard sign in rainbow letters: "IN THIS HOUSE, WE BELIEVE: SCIENCE IS REAL / LOVE IS LOVE / KINDNESS IS EVERYTHING". Next to the driveway a polite HOA sign reads "PRIVATE ROAD — NO TURNAROUNDS". Tilt-shift macro photography, soft studio light, tiny painted details, a small brass plaque at the front of the base engraved "SUBURBAN PROGRESSIVE · EST. 2020". No car brand logos.
```

Then a GIF of that still (8 frames, 768x768, 250 ms):

```
Animate this exact miniature diorama as a looping GIF at dusk-warm light: the porch lantern, the wall lamp and the warm window lights blink on and off in a gentle rhythm, and the small status light on the EV wall charger blinks green. Everything else stays exactly the same in every frame: the house, the solar panels, the car, the Little Free Library, the PRIVATE ROAD sign, the lawn sign with its exact text, the garden, the brass plaque, the framing. Fixed camera, no motion except the lights.
```

## MY FAVORITE GAME (`game`)

Base image (image 1): https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_247cceee8d65.png

Settings: aspect 1:1.

```
Edit image 1, this exact board-game photo. Two changes only: (1) replace the small dog game token in the center with a small glossy plastic figurine game token of the person from image 2, with their recognizable face and smile, short teal hair and a rainbow scarf, holding a tiny tote bag; (2) the top "WOKEOPOLY 500" bill now carries a small engraved banknote-style portrait of the same person in an oval frame. Keep the board, every space and label, the title WOKEOPOLY, the cards, the other props, the angle and the lighting exactly as they are.
```

<details><summary>The prompt that made the base image</summary>

```
Top-down product photograph of a satirical board game called "WOKEOPOLY", a Monopoly-style board with a rainbow-to-pink gradient. The square board has a continuous track of spaces. Legible spaces around the edge: "GO", "LAND ACKNOWLEDGMENT", "PRONOUN CHECK", "OAT LATTE $7", "SAFE SPACE", "CANCEL CARD", "DIVERSITY TRAINING", "THERAPY SPEAK", "PUBLIC RADIO TOTE", "MARCH", "TRIGGER WARNING", "CHECK YOUR PRIVILEGE", "GO TO CANCELLATION", "PRIDE MONTH (JUNE ONLY)", "ALLYSHIP", "MICROAGGRESSION", "CONTENT WARNING", "PAYMENT REQUEST". Center: the logo "WOKEOPOLY" in bold rounded type with a small rainbow flag, and the tagline "THE GAME OF MORAL CAPITAL". Game pieces: a tiny megaphone, a tote bag, a soy latte, a rescue dog, a pronoun badge. Rainbow play money, a deck of "CANCEL CARDS" and a deck of "ALLY CARDS". Crisp product photography, soft studio lighting.
```

</details>

## Fix prompts

Face-only pass. Inputs: [the tile, the selfie]. Model `fal:openai/gpt-image-2.6/flare/edit`. `{WHO}` is the tile's `face_fix_who`.

```
Edit image 1. Change only the face of the person {WHO}: make it exactly the person in image 2, a real person. Match their face shape and jaw, cheekbones, eyes and the creases around them, eyebrows, nose, ears, smile and teeth, skin tone and hair color. Sharp, natural, photorealistic face. Keep everything else exactly as in image 1: the head angle, hair style, clothes and pose, the other people, every sign and text, colors, light and framing.
```

Logo removal. Input: [the tile].

```
Edit this exact image. Remove the brand logo, letters or badge from {WHERE} so it is plain, with no logo or brand mark. Change nothing else: same people, faces, text, colors, lighting and framing.
```

## Research on X (2026-11-05)

**The #1 woke animal is the cat.**

- JD Vance's "childless cat ladies" clip: https://x.com/RonFilipkowski/status/1815503440983867598 (30.1M views, 29.6k likes).
- "WOKE CAT": https://x.com/Zeroawen/status/1871955966423634194 (110.5k likes); the replies joke "they/them".
- "Leftist cat lady" at Target: https://x.com/TimRunsHisMouth/status/2014646831385366982 (31k likes).
- Runners-up: pit bull (about 2.5k likes at most), French Bulldog ("French Bulldog = Democrat", @WillCainShow, 733 likes), opossum (6.3k), Black Lab (1.4k).

**The woke friend group.**

- They/them art student: @VanityUwU, 2.3k likes, 2026-11-04.
- "Performative male" feminist: https://x.com/shoe0nhead/status/2049972462750667231 (21k likes); @tlbtisitttbm (9.5k).
- Wine-mom ally: @CameronCorduroy (8.3k).
- Masked DSA organizer: @tonyhawktruther (14.8k).
- Tie-dye boomer: @bennyjohnson (9.2k).
- Setting, the street-protest sign: https://x.com/dsonoiki/status/2029843614801809549 (13.9k likes).
- "WOKE 3.0" on election night: https://x.com/thelorebitch/status/2117832504904446017 (50k likes); @MNateShyamalan (45k).
