# Example: a drink-test sticker reel remixed into a car seat gap filler ad

## The winner (input)

`video_analyze` on a 21.5 s German reel for drink-test nail stickers (5 credits):

| Time | Shot | On screen |
|---|---|---|
| 0.0–4.9 | Club bar: a man distracts a woman and drops something into her drink | "Das Problem 😵‍💫" |
| 4.9–8.8 | Simulated CCTV, black and white: he holds her up in a back corridor | "CAM 04 · 17.10.2026 · SA 02:47:13 · REC · HINTERER FLUR", "Vs..." |
| 8.8–12.3 | Vanity table: hands open the sticker pouch | "Die Lösung 😍" |
| 12.3–15.9 | A sticker goes on a nail | "Drink-Test als Sticker 💕" |
| 15.9–19.4 | Finger in a cocktail, the star turns green | "Süß & kinderleicht 🥰" |
| 19.4–21.5 | The pouch held up at the bar | "Link in der Bio für deine 🔥" |

Tags: angle *safety disguised as cute nail art* · format *problem → Vs → solution, music, sentence-case text with emoji* · proof *colour change* · offer *20 stickers* · awareness *problem-aware* · audio *trending song, no voice*.

Note: the reel sits behind Instagram's "can't be seen by certain audiences" gate. Fear themes (assault, injury) cap reach; the remix keeps the structure and drops the fear.

## The remix (output)

Move: **same format, new angle** (an everyday annoyance with a mild safety beat instead of assault).

| Time | Shot (varg skill / model) | Text |
|---|---|---|
| 0.0–4.6 | Dashcam, interior: the phone slips into the seat gap (kling_v4) | "The problem 🥺" + `CAM 02 · INTERIOR · REC` overlay |
| 4.6–8.9 | Same camera, made from the last frame of shot 1: she reaches into the gap at a green light, cars honk (kling_v4) | "The problem 🥺" |
| 8.9–10.0 | Box on the seat (seedance_2_5, product as @image1) | "Vs..." |
| 10.0–14.9 | Gap fillers out of the box, slid into the gap | "The solution 😍", "Fits every car 🚗" |
| 14.9–20.9 | Coins and a phone land on top and stay there (seedance_2_5) | "Nothing falls through 🙌", "Link in bio for yours 🛒" |

Music bed: `mureka_9_5`, 23 credits. Text and the camera timestamp: transparent PNG overlays (emoji need a browser renderer), laid on with `assemble.mjs` from `varg-dropship-reel`.

Not reused: footage, music, people, copy, brand, storyline beats (no club, no drink, no victim). Reused: the five-beat structure and the text style, which are free.

Video: https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a2aa0853b683.mp4
