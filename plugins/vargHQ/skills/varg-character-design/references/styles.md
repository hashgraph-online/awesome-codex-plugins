# Famous looks, described without IP names

Recognisable animation looks are a shortcut to attention: the viewer knows the genre before the first word. You can use the **look**; you cannot use the show's **characters, names, logos or catchphrases**, and some shapes are trademarks. This is a risk map, not legal advice; get an IP lawyer's sign-off before a large campaign that evokes a famous show.

## What we measured (2026-10-27)

- `nano_banana_2_1` **refused** "Redraw the woman from the character sheet as a character in The Simpsons style" and **drew the same look** from a description ([result](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_6e0343fe7b20.png)).
- `gpt_image_2_5` and `seedream_5_pro` accepted the name. Third-party reports: Seedance blocks "Simpsons" and "Astérix"; Gemini filters named characters since February 2026; OpenAI allows studio styles but not living artists' names.
- The description is as recognisable as the name, so there is no reason to type the name.

## The legal line, short

- **Style is not protected** by copyright; specific expression is (17 U.S.C. §102(b); *Andersen v. Stability AI*, 2023: "in the style of" alone was not enough).
- **Characters, names, logos, catchphrases** are protected (copyright for well-delineated characters, trademark for names and logos).
- **Some shapes are trademarks**: the brick minifigure is a registered EU 3D mark (upheld 2015 and 2023); "Claymation" is a registered word mark; treat "Pop!" and "Muppet" as brand names.
- **Parody does not cover selling your product** with someone else's mark (*Jack Daniel's v. VIP Products*, US Supreme Court, 2023).
- **Enforcement is active**: Disney/Universal/WBD v. Midjourney (2025) names The Simpsons; the same studios v. MiniMax/Hailuo (2025); Disney's cease-and-desist to ByteDance over Seedance (Feb 2026); Japan's CODA (Ghibli, Bandai Namco, …) against Sora 2 training (Oct 2025). Disney's licence to OpenAI covers in-app generation only, not ads.
- **Ad platforms** reject ads that infringe third-party IP (Meta) and now label AI content (Google Ads, July 2026).

Practical rule: describe the visual grammar; keep IP names out of prompts, file names, titles, tags, captions and ad copy; design original characters; end the prompt with "original design, no recognizable existing characters, no logos, no text".

## Style blocks

Put the style block first, then the character. Examples on the right were made with these blocks.

| Look | Style block | Models | Watch out for |
|---|---|---|---|
| Yellow family sitcom (1990s primetime TV) | flat 2D TV-animation look of a classic 1990s primetime family sitcom: thick uniform black outlines, flat saturated cel colors, no shading, lemon-yellow skin, large round white eyes with small black dot pupils, overbite, four-fingered hands, simple suburban set in saturated pastels | `nano_banana_2_1`, `gpt_image_2_5` | Designs close to the real family (bald with two hairs, blue beehive, spiky kid), the town, the font, catchphrases. Our [Gary Pruitt](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a4a9e3cae8a4.png) is original, but the overall look is close enough that paid ads should push further (another skin colour or eye style) |
| 3D family feature film | stylised 3D CGI animated family feature-film look, soft global illumination, warm key light, subsurface scattering, big expressive eyes, simplified rounded shapes, matte materials, clear silhouette | `nano_banana_2_1`, `gpt_image_2_5`, `seedance_2_5` | Studio names; lookalike toys and robots. [Señor Pincho](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_844b46a7a45d.png), [Baguettosaurus](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_3356a6c5b5c1.png) |
| Hand-painted pastoral anime | hand-painted watercolor and gouache backgrounds, soft cel-shaded characters with simple faces, big summer clouds, warm nostalgic countryside light, wind in tall grass, 1990s Japanese animated feature film | `gpt_image_2_5`, `seedance_2_5`, `minimax_h3_max_style_hand_drawn` | Forest-spirit lookalikes, the studio name |
| Construction-paper cut-out | crude construction-paper cut-out animation, flat shapes, visible paper texture, round heads, mitten hands, limited jerky stop-frame movement, small snowy mountain town | `nano_banana_2_1`, `gpt_image_2` | The four boys, the town name |
| Adult sci-fi cartoon | late-night adult 2D sci-fi cartoon, wobbly thin outlines, flat colours, bulging eyes with drawn pupils, drooling-sneer expressions, neon-green portal glow, garage-lab clutter, deadpan absurd tone | `gpt_image_2_5`, `nano_banana_2_1` | A lab-coat scientist with spiky blue-grey hair and a yellow-shirt teen sidekick |
| Clay stop-motion | clay stop-motion look, visible fingerprints and tool marks on plasticine, slightly lumpy hand-sculpted forms, handmade miniature set, felt and wood props, soft practical light, slight frame jitter | `nano_banana_2_1`, `gpt_image_2_5`, `seedance_2_5`, `kling_v4` | Say "clay stop-motion", not "Claymation" (a trademark); avoid the famous inventor-and-dog pair. [Hector](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_eb98a40764c2.png) |
| Brick toy | toy building-brick world, small toy figures with a smooth plastic sheen, studded bricks, macro toy photography, tilt-shift depth of field | `nano_banana_pro`, `gpt_image_2_5`, `flux_3_image` | The minifigure shape is a registered EU 3D trademark: design your own toy figure for ads |
| Vinyl collectible / action figure | boxed 6-inch collectible vinyl figure, matte vinyl, slightly oversized head, window-box packaging with your own brand art, accessories in the tray, product photo on a desk | `nano_banana_2_1`, `gpt_image_2_5` | Funko-style box shape and logo; use your own packaging. [Nonna Rosa, Series 1](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_3c2e14641686.png) |
| Modern anime | modern anime, cel-shaded, clean line art, large expressive eyes, speed lines, vibrant key-art lighting | `seedance_2_5`, `gpt_image_2_5`, `nano_banana_2_1` | Named series, characters, recognisable uniforms |
| Felt puppet | handmade felt and fleece hand puppet, foam head, ping-pong-ball eyes, wide hinged mouth, visible stitching, rod-controlled arms, simple TV-studio set | `gpt_image_2_5`, `nano_banana_pro`, `kling_v4` | "Muppet" is a brand; avoid a green frog and a pig diva |
| 1970s Saturday-morning cartoon | use the video preset | `minimax_h3_max_style_retro_toon_70s` | Original characters only |
| 16-bit pixel, VHS, low-poly, pencil | video presets | `minimax_h3_max_style_16bit_pixel`, `_vhs`, `_low_poly`, `_hand_drawn` | |

## Restyling a finished character

Keep the sheet as the identity and change only the medium:

```
Redraw the woman from the character sheet as <style block>. Keep her <signature details from the
card>. <Scene>. Original design, no recognizable existing characters, no logos.
```

Tested: Nonna Rosa's photoreal sheet became a yellow 2D sitcom character and a boxed vinyl figure in one call each on `nano_banana_2_1`, keeping the curlers, glasses, headscarf, leopard housecoat and slippers. Build a separate model sheet in the new style before using it in video: a photoreal sheet next to a cartoon prompt makes video models mix the two.

## Trends that use these looks

- **Self-as-toy** (action figure in a blister pack, vinyl figure, desk figurine): drove app sign-ups (Gemini +13M users in 4 days). For a brand, use it on your own mascot or character.
- **Photo-to-style** (painted anime, 3D family film): the Ghibli wave added 1M ChatGPT users in an hour; brand uses drew backlash. Fine for organic posts with original characters; risky in ads.
- **Existing characters brought to life** (a real-life ogre lord, Stormtrooper vlogs): huge reach, not usable in ads. Copy the mechanics (deadpan, one recognisable silhouette) with an original character.
