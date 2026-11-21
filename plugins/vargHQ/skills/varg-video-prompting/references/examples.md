# Examples: prompt, result, lesson

Ten runs from our own productions, anonymized. Prompts are trimmed to the parts that mattered. Credits are what the
runs were billed or quoted; your prices may differ, so estimate before you run.

---

## 1. A master scene from a grey previz (Seedance 2.5, video-to-video)

**Setup.** A 99 s vertical music video in a 1980s anime look. Shots were grouped by location into 13 runs of 4-10 s
at 480p. Each run had its own grey-box previz clip as `@video1`, plus the character sheet and the cockpit master as
image refs.

**Prompt (excerpt).**

```
@video1 is a black-and-white grey-box 3D previz of this sequence. Copy from @video1 ONLY the camera (framing, lens,
camera position and movement), the hard-cut timing and the blocking. Do not copy its look: no flat grey shapes, no
3D render style, no greyscale: redraw every frame as full-colour hand-drawn anime; the result must not look like
@video1.
@image1 is the pilot's character sheet: same face, black hair with violet highlights, amber eyes, white cropped
flight jacket with two orange stripes on each shoulder, black fingerless gloves, headset with a boom mic on his left.
@image2 is the master shot of the cockpit. Every cockpit shot happens in this exact cockpit: round silver console with
cyan and magenta buttons and one round orange button in the middle, flight stick at his right hand, throttle at his
left, a small glowing orange orb above the console, a spiderweb crack in the upper right of the canopy.
Only one person in the cockpit; every visible hand and sleeve belongs to him.
5 shots, hard cuts exactly as in @video1:
1. 0.0-1.8 s. Extreme close-up of his eyes ... At 0.9 s something hits the ship off-screen ...
...
Camera: one move per shot, as in @video1. Full-bleed 9:16 frame, no borders, no letterbox. No text, letters,
numbers, logos or UI anywhere in the frame. No dialogue, no lip-sync.
```

**Result.** Camera, cut points and blocking matched the previz and the style was redrawn. One run came back as the
previz itself, grey and re-encoded, and was billed less; the reviewer saw it as "no texture on the ship". Its re-run
carried only the ship and drone refs, so the giant monster in the background came out without a reference, and the
next round added the monster sheet to that run. The 13 runs billed about 1,565 credits (about 16 per second), well
under the estimate.

**Lesson.** Send the previz in greyscale and say the result must not look like it. Give an image ref for every
character, vehicle and creature in frame. Compare every output with its previz at the same timestamps before cutting.

## 2. A recurring prop that kept changing (Nano Banana stills)

**Setup.** Sixteen cockpit stills on the storyboard. The reviewer asked for the console to be the same in every
shot; it differed from the cockpit master in seven of them (screens on stands, keyboards, rows of toggle switches,
UI drawn on the screens).

**Prompt fix.** Spell the console out by count and position in every cockpit prompt:

```
The console must be exactly the console from @Image2: an oval chrome console; along its top edge one row of small
square buttons glowing cyan and magenta; two dark empty rectangular screens left and right; between them a single
round orange button; below the screens two cyan and two magenta round buttons; nothing else on the console.
```

**Result.** All six regenerated stills matched the master, about 72 credits for the round. The seventh, a fist
slamming the orange button, failed three times: twice a second orange button appeared, once the pilot had three
hands. Asking for "the same shot as @Image1 with only one change: his fist completely covers the orange button" did
not help either. The original take was kept, because its button layout already matched.

**Lesson.** A recurring room needs its key props written out every time. A hand touching a small unique prop is the
hardest still to get; stop after two failures and reframe or fix it locally instead of rerolling.

## 3. A segment the reviewer called AI slop (Seedance 2.5 retake)

**Setup.** A 6 s stretch of the same music video looked noisy and inconsistent with the rest of the film.

**Prompt fix.** One retake of the segment, with frames grabbed from approved shots of the same film as refs (the
monster as it looked in a later shot, the space around it), and a clean-look line:

```
@image2 is a frame from this same film showing <the monster / the cockpit>; copy its drawing style, colours and
design.
Every frame is clean cel animation with crisp ink lines and flat colour: no TV static, no noise, no grain, no
photographic texture, no smeared blur.
```

**Result.** The retake matched the surrounding shots (about 97 credits at 480p). The earlier prompts had asked for
"static" and "noise" as story elements; the model drew them as grey mush across the frame.

**Lesson.** Your own approved frames are the strongest style reference. In stylized looks, leave static, noise,
glitch and grain to post-production.

## 4. Stray hands and props (Seedance 2.5, 4 s retakes)

**Setup.** Two shots had faults: a strange object in the hero's hands, and a helmet that came out wrong while a
character put it on.

**Prompt fix.**

```
His hands are empty: he holds no card, no tablet, no paper and no glowing object at any time.
```

```
She has exactly two arms and two hands in every frame. Her helmet is one round white helmet with a dark visor.
0.0-1.4 s: she walks away from the camera, the helmet in her right hand at her side. 1.4-2.4 s: she turns her head
over her left shoulder and smiles. 2.4-4.0 s: she lifts the helmet with both hands and slides it down over her head
in one clean motion; her hands stay on the sides of the helmet.
```

**Result.** Both retakes were clean, about 65 credits each at 480p. The arm poses were taken off the reference
("Copy from @video1 ONLY the camera ... Do not copy its look or its arm poses"); in an earlier run a large grey wing
from the previz foreground had stayed in the finished shot.

**Lesson.** Name the fault as a positive constraint with counts, time every hand action, and keep retakes to a 4 s
run of the one broken shot. Whatever sits in a reference clip tends to stay: remove it there, or say exactly which
parts of the reference to copy.

## 5. A whisper-to-shout talking hook (Seedance 2.5, then Sync v3)

**Setup.** A 5 s square clip: a woman whispers a teaser, then shouts the payoff, with an ElevenLabs v4 voice.

**First try.** Seedance in reference mode with a distant portrait (her face about 280 px wide) as `@image1` and the
voice line as `@audio1`, 720p, plus "She performs the voice line in @audio1 with precise lip-sync and the exact
timing of @audio1."

**Result.** The face came back soft and drifting, and the line was re-voiced in a similar voice with its own timing.
A digital 1.7x punch-in in the edit made the first second mush. A later version with "hair explodes" and "stadium
lights blast on" looked cheap.

**Fix.** A new sharp close-up portrait as `@image1` ("her face and look: keep exactly"), the approved medium framing
as `@image2` ("the final framing"), the voice as `@audio1` for performance timing only, 1080p, and the camera move in
the prompt ("0-2.2 s: tight close-up, she leans in, whispering with a sly smile. At 2.2 s the camera snaps back to a
medium shot like @image2 as she shouts at full power"), with restrained effects (spray and rim light). The clip was
then retimed syllable by syllable to the real voice, and `sync_v3` put the exact mouth on top. The reviewer approved
it for a site banner.

**Lesson.** Reference mode re-draws the person, so give it a large, sharp face, not a distant portrait (or use one
first frame when the face must be exact). Move the camera inside the generation, never zoom digitally. Seedance
supplies the performance, the lip-sync model supplies the exact mouth.

## 6. A calm luxury film on Kling 4 (stills, recast, start-to-end chaining)

**Setup.** A 28 s 16:9 meditation film: a man meditating in a stone room, a glowing sphere between his hands grows
into a planet, then he floats in space.

**Prompts (excerpt).** Master first, then every other still from it:

```
Same man, same cream cashmere sweater, same room and light as the reference image. New camera: medium close-up from
the front at eye level, 85mm lens, shallow depth of field. ...
```

The sphere-to-planet shot used two files, start still and end still, on `kling_v4`:

```
The small glowing amber sphere between his cupped hands begins to swell slowly like a breath being drawn in ... The
camera pushes in smoothly toward the sphere as it grows until its glowing surface fills the entire frame. Continuous
single move, smooth and organic, no cuts.
```

**Result.** Five 1080p clips, the face consistent across all of them, about 650 credits of Kling for 26 s. The
reviewer then said the hero, a big man of about 58 with flowing silver hair and a white beard, looked like AI slop.

**Fix.** "Replace the man with a different, younger and more real man: around 46, dark brown hair cut short with
natural grey at the temples, a short salt-and-pepper beard, a slightly crooked nose, small natural asymmetries. Real
unretouched skin: visible pores, fine lines, slight redness on the cheeks. Shot on Kodak Portra 400, fine film
grain, no CGI look." One recast still lost the symmetry of the wide shot; "Edit the first image only by swapping the
person's head and face. Do NOT change the camera, framing, crop, symmetry ..." restored it.

**Lesson.** Stock archetypes read as AI; irregular features and real skin read as real. Recast in the stills, never
in the clips. Start and end frames made from one master chain into one continuous move.

## 7. One outdoor set, three cameras (Nano Banana, GPT Image, a 3D blockout)

**Setup.** A storyboard of three shots in one outdoor set: a fork in a road, a signal post, several figures at fixed
spots, a vehicle approaching.

**First tries.** An environment master as the reference of every shot, first on Nano Banana, then on GPT Image 2.5.

**Result.** Each shot invented its own set: the fork vanished in one, a figure stood on the wrong side in another,
gravel turned into wet asphalt, lying figures came out as headless logs. Changing the image model did not help.

**Fix.** A three.js blockout of the set in real metres, rendered from each camera, then a GPT Image edit with the
render as the FIRST file: "Keep EXACTLY its camera position, lens, framing and perspective, and the position, size and
orientation of every object. Do not add, remove or move any object. Mapping: grey ground = dry dark asphalt; ...".
The vehicle was added in a second pass: "Keep the FIRST image pixel-identical in every respect ... Add only one thing".

**Lesson.** Pictures do not remember space; geometry does. When several cameras share a set, block it in 3D and let
the image model only paint it. Give blockout people heads, arms and feet.

## 8. "Silent" clip with a soundtrack (Seedance 2.5 test)

**Setup.** A 5 s 480p square test clip with `audio: false`, meant to get music later.

**Result.** The clip carried a loud track with speech-like phrases in the background. The agent had not listened to
it; the reviewer did. The unified audio flag had not reached the model on the route that ran.

**Fix.** Set the provider's own audio flag as well (listed on the model's spec page), strip audio in the edit for
every clip that gets music or voice-over, and check every clip's audio track during QA.

**Lesson.** Check the sound of every clip, including the ones that should have none.

## 9. A lip-sync pass on three singing shots (Sync v3)

**Setup.** Three shots where the hero sings, each cut exactly as it plays in the edit and paired with only its own
slice of the vocal stem. About 100 credits per shot.

**Result.** A three-quarter close-up whose teeth had been shut the whole time came back opening on the vowels. A
second shot synced cleanly. A profile close-up with clenched teeth barely changed, so the original was kept and that
shot's credits were wasted. Output lengths matched the inputs to the frame.

**Lesson.** Pick lip-sync shots by face angle before paying: frontal or three-quarter, mouth visible.

## 10. Two songs from one lyric sheet (ElevenLabs Music vs Lyria 3.5)

**Setup.** The same lyrics, both prompted as a 50 s, 112 BPM synth-pop song with timestamped sections and "vocals
from 0:00, no intro":

```
50-second punchy 80s synthwave pop, 112 BPM. Loud four-on-the-floor kick, gated snare, analog pads, arpeggiated bass,
sax lick. Bright female vocal, crisp diction. Vocals from 0:00, no intro. [0:00-0:04] "<hook>". [0:04-0:22] Verse:
"<lines>". [0:22-0:30] Build: "<lines>". [0:30-0:46] Chorus: "<lines>". [0:46-0:50] "<tag line>". Song ends.
```

**Result.** ElevenLabs Music measured 112.3 BPM and 50.0 s. Lyria measured about 97 BPM and 54.9 s; the automatic
beat tracker first read it as 129 BPM, a triplet error that a check on the drum stem corrected. The reviewer chose
Lyria by ear, and the edit was cut on its measured grid.

**Lesson.** Choose the song by ear, then measure it; never cut on the BPM you asked for, and sanity-check the beat
tracker against the drums.
