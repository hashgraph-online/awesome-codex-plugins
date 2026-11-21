# The ending and the "comment GUIDE" funnel

## The shot: night skyline filmed on an iPhone

All four reels studied end on 5-7 s of a night city from a high-floor apartment: through a floor-to-ceiling window with the dark room edge in frame, or from a balcony or marina walkway. The reels are Dubai (Burj Khalifa, Dubai Marina towers). The point is the lifestyle the guide promises, said without words. It must look like the creator's own phone, not stock: handheld, a little noisy, no grade.

Three ways to get it:

| Option | Quality | Notes |
|---|---|---|
| **Your own phone clip** | Most believable | Any night city works; Dubai is a cliché of the niche, not a requirement. iPhone: 1080p 30 fps, lock exposure on the bright towers (long-press), hold still for 6 s, a slow pan at most. |
| **AI, iPhone look** (`wan_3` or `seedance_2_5`) | Good: tested, see below | 6 s 720p: `wan_3` 60 credits, `seedance_2_5` 231. Make 2 variants and keep one; reuse it in every reel. |
| **Stock** | OK | Free clips on Mixkit and Pexels ("Dubai night", "city night window"). Check the license allows ads. Stock is usually too clean and stabilized; add a slight shake in the edit if needed. |

Prompt that worked on both `wan_3` and `seedance_2_5` (text-to-video, 9:16, 720p, 6 s):

```
Shot on iPhone, vertical video, handheld with subtle natural hand micro-shake. Night, filmed from
inside a dark high-floor apartment in Dubai Marina through a floor-to-ceiling window: the glittering
skyline, lit towers, a few cars moving on the road below. Dark interior edge of the window frame and
the reflection of a lamp faintly visible on the glass. The phone slowly pans right a little. iPhone
night mode look: slight noise, lights slightly blooming, auto exposure, no cinematic color grade, no
drone, no stabilizer gimbal. No people, no text.
```

What makes it read as "phone": the words *handheld micro-shake*, *through the window glass*, *reflection*, *noise*, *auto exposure*, and the negatives *no cinematic grade, no drone, no gimbal*. Without them the models make a smooth drone flyover that looks like an ad.

In our test (2026-10-27) both models gave a convincing phone clip through a window with a slow pan, close to the originals. `wan_3` (60 credits) showed the Marina towers, the lamp reflection and the busy road below, with no Burj Khalifa: start there. `seedance_2_5` (231 credits) came out darker and noisier, even more phone-like, but put Burj Khalifa in the middle on its own even though the prompt says Dubai Marina, so for a paid ad add "no Burj Khalifa" (see Landmarks below). Text-to-video on `seedance_2_5` sat in the queue for about an hour that day, while image-to-video jobs finished in 5-10 minutes. If you're in a hurry, or want to approve the frame before paying for video, go still-first: make the frame with `gpt_image_2_5` ("Vertical iPhone night photo taken from inside a dark high-floor apartment through a floor-to-ceiling window … dark window frame and a corner of a sofa at the edges, faint reflection of a warm lamp on the glass, slight sensor noise, no cinematic grade"), then animate it on `seedance_2_5` with only the motion ("handheld, the phone drifts slowly right, cars stream below, lights twinkle, the reflection shifts"). Tested the same day: the frame (22 credits) plus 6 s of `seedance_2_5` (231) gave the Marina at night through the window, with the sofa and the lamp reflection held for the whole shot and a slow handheld drift. It looked brighter and more polished than text-to-video, but you see exactly what you get before paying for the video.

Other endings that work the same way: a balcony at sunset with a coffee, a car interior at night with the city passing, a beach club, an infinity pool. Keep it 5-7 s, no people's faces.

**Landmarks:** Emaar's asset policy asks for approval before Burj Khalifa visuals are used in advertising, CGI included. For a paid ad, keep the tower out of focus or out of frame and use a generic skyline. For organic posts, creators use it freely, but that is a risk, not a license.

## The CTA line and caption

Voiceover over the skyline: *"Comment GUIDE and I will send you a free step-by-step guide on how it's done."* On-screen captions keep running word by word, and the keyword is in quotes: `COMMENT "GUIDE"`.

Post caption used on all four: `Best time to start is here 🤝  #entrepreneur #onlinebusiness #ecommerce`. Keep it that short; the video does the selling.

## The DM automation (ManyChat)

The keyword only works if a DM goes out within seconds.

1. Instagram professional account (Business or Creator), connected to ManyChat (free plan is enough to start).
2. Automation → **Instagram → Comments** trigger → "specific post or reel" (or any post) → keyword `GUIDE` (add `guide`, `Guide`).
3. Public reply to the comment (rotate 3-4 texts so it doesn't look botted): "Sent! Check your DMs 📩".
4. DM: a short message with a button → your guide (Notion page, PDF or landing page with the affiliate or store links). Ask them to follow you to get the next product: a follow-gate raises follows a lot.
5. Meta limits: one private reply per comment, and the comment must be under 7 days old. Follow-ups only while the 24-hour window is open (they replied or clicked).

What goes in the guide: the same steps as the video, with links (research tool, store builder, AI ad tool, supplier), screenshots, and the product of the week. That is where an affiliate earns.
