# Real people, not plastic ones

## What "AI-looking" people are, in 2026

Two failures. A generic prompt ("beautiful woman, 8k") gets the model's **average face**: pleasant, symmetrical, camera-aware and forgettable, the same woman every time. A suggestive prompt ("hot sexy girl … big booty, seductive look") gets the glossy, poreless, same-face "AI girl": tested on Seedream 5 Pro, Soul and Grok Image 2, and blocked on GPT Image 2.5 and FLUX 3. Suggestive wording costs realism as well as moderation.

Other tells: doll eyes and unrequested eyeliner; flat front light that hides pores; HDR and face-enhance upscaling; a generic beauty prompt drifting toward a celebrity's face (which some filters then block as likeness).

## The realism kit

| Layer | Words that work |
|---|---|
| Skin | visible pores, fine peach fuzz on the cheeks, fine lines around the eyes, faint under-eye texture, slight redness around the nose, uneven tone, a few natural blemishes, light forehead shine, natural lip texture |
| Retouch | "unretouched editorial photograph", "no smoothing, no beauty retouch, no airbrushing", "natural skin visible under the makeup" |
| Light | single side window light; overcast daylight; slightly backlit sun; direct on-camera flash with hard shadows |
| Camera | "shot on a 35mm film camera, slight grain", "iPhone front camera at arm's length", "compact point-and-shoot with direct flash", "85mm f/2.8" |
| Moment | laughing at something off-camera, mid-step, adjusting a sleeve, gaze away from the lens, slightly off-centre framing |
| Face | one or two irregular features: a small bump on the nose bridge, one brow higher, a gap between the front teeth, a beauty mark, a faint scar |
| Drop | "flawless", "perfect", "beautiful" as a quality word, "8K masterpiece", "HDR", "professional photo" |

## Very beautiful, and still real

Cast her like a model agency (age as a number, 4–6 striking features: cheekbones, jaw, eyes, lips, hair with a styling verb), keep the skin real (pores, freckles, no plastic smoothing), style her (makeup, one jewellery piece, an exactly named outfit) and light it like a shoot (golden-hour backlight at 85mm, direct flash, red-carpet flash). Tested prompts and results: `varg-character-beautiful-woman`.

- Men: patchy stubble, pores, forehead shine, weathered hands, slight under-eye shadows; "an ordinary real adult man, photographed naturally rather than posed" works for UGC.
- Hair colour, eye colour and freckles alone still give near-identical faces; change the face shape, nose and age too.

## Unusual bodies, done respectfully

Numbers alone are under-rendered. Tested on `seedream_5_pro`: "178 cm and about 160 kg" gave a heavy-set man who reads lighter than that ([v1](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_33b0d3a66e95.jpg)); describing what the camera sees fixed it ([v2](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7715698a084a.jpg)). Height without anything to compare it to is invisible on a plain sheet ([v1](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_da73ccf7aad3.jpg), [v2](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_8252d5cfde30.jpg)): put the scale in the scene (a doorway, a car roof, a normal-height person beside him).

| Body | Phrasing that works |
|---|---|
| Very old | exact age ("84-year-old"), deep natural wrinkles, age spots, visible veins on the hands, thinning hair, slightly stooped posture, "no airbrushed skin, no professional makeup" |
| Very heavy | "a very large heavyweight man of about 160 kg: wide round belly that pushes the apron forward and hangs over the waistband, broad heavy shoulders, thick neck, full cheeks and a double chin, thick arms and legs"; clothes that fit true to size or look a size too small; full-length framing; "realistic weight distribution, not slimmed"; for women "plus-size adult woman, US size 22, 165 cm, full upper arms, soft belly, wide hips" |
| Very tall and thin | "extremely tall and lanky: very long thin legs, arms that hang to mid-thigh, narrow sloping shoulders, a small head for his height, trousers slightly too short"; scale cues in scenes |
| Short | "adult, short stature, 152 cm" (not "petite" or "tiny", which read as minor-adjacent) |
| Muscular | sport context: "competitive bodybuilder in a front double-biceps pose on stage, posing trunks, competition tan, contest number", "powerlifter mid-deadlift in a garage gym, chalk, lifting belt" |

Models default to thin bodies and quietly hide larger ones (loose clothes, tight crops, angled poses). Ask for full-length framing, and keep the comedy in the situation, not in the body.

## Which model for realism

| Model | Notes |
|---|---|
| `seedream_5_pro` | Best skin texture and attitude in our sheets; native 2K; 7 credits |
| `nano_banana_2_1` | Believable even from weak prompts; best for edits that keep identity |
| `gpt_image_2_5` (Flare / Sunburst) | Top of a 25-model realism test (getimg, Oct 2026); strict on swimwear |
| `soul` | Fashion and UGC realism presets; text-to-image only on varg |
| `phota` | An identity layer from a trained profile (`[[profile_id]]`) |
| `flux_3_image` | Strong at keeping a reference face |

## Upscaling without waxing the face

| Tool | Behaviour |
|---|---|
| `seedvr`, `seedvr_video` | Keeps pores and lip structure |
| `recraft_clarity` | Keeps structure and freckles |
| `clarity_upscaler` | Can strengthen freckles; high creativity can drift identity |
| `topaz`, `topaz_video` | Softened freckles and made eyes look synthetic in fal's test; turn face enhancement down or off |

If the upscaled face looks smoother than the source, redo it with face enhancement lower and compare at 100%. Never put a uniform grain overlay on top.
