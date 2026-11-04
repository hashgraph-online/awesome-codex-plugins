# Cuts & pacing

J-cuts, L-cuts, match cuts, jump cuts, smash cuts, speed ramps and beat cuts, each with the FFmpeg, Remotion, HyperFrames and CapCut way to make it. 26 takes. Browse them with previews at https://skills.varg.ai/browse/skills/cuts/.

## Hard Cut

<a id="hard-cut"></a>One shot ends, the next begins on the very next frame. The default join: invisible when the content flows.

Frame N is shot A, frame N+1 is shot B. No overlap, no effect.

- **When:** Most joins in any edit. Use it whenever the change of shot is motivated by story, speech or rhythm.
- **Watch out:** Two near-identical framings of the same subject cut together read as a mistake (a jump cut) unless you mean it.
- **Timing:** 0 frames
- **Also called:** straight cut, cut, butt cut
- **Card:** https://skills.varg.ai/skills/hard-cut/

### FFmpeg

Re-encode with the concat filter (any sources) or losslessly with the concat demuxer (identical codecs).
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=2:5,setpts=PTS-STARTPTS[v0];[0:a]atrim=2:5,asetpts=PTS-STARTPTS[a0];\
 [1:v]trim=0:3,setpts=PTS-STARTPTS[v1];[1:a]atrim=0:3,asetpts=PTS-STARTPTS[a1];\
 [v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

```html
<video id="a" src="a.mp4" data-start="0" data-duration="3" data-media-start="2" data-track-index="0" data-has-audio="true"></video>
<video id="b" src="b.mp4" data-start="a" data-duration="3" data-track-index="0" data-has-audio="true"></video>
```
`data-start="a"` means "start when clip a ends".

### Remotion

```tsx
import {Series} from 'remotion';
import {Video} from '@remotion/media';

<Series>
  <Series.Sequence durationInFrames={90}><Video src={staticFile('a.mp4')} trimBefore={60} /></Series.Sequence>
  <Series.Sequence durationInFrames={90}><Video src={staticFile('b.mp4')} /></Series.Sequence>
</Series>
```
`trimBefore` replaced `startFrom` in v4.0.319.

### CapCut

Put the playhead on the cut point and Split (Ctrl/Cmd+B on desktop, Split in the bottom toolbar on mobile), delete the unwanted part; clips on the main track snap together.

### MoviePy

```python
from moviepy import VideoFileClip, concatenate_videoclips
a = VideoFileClip('a.mp4').subclipped(2, 5)
b = VideoFileClip('b.mp4').subclipped(0, 3)
concatenate_videoclips([a, b]).write_videofile('out.mp4')
```

Sources: [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter) · [FFmpeg formats: concat demuxer](https://ffmpeg.org/ffmpeg-formats.html#concat) · [Remotion: <Series>](https://www.remotion.dev/docs/series) · [HyperFrames: data attributes](https://hyperframes.heygen.com/concepts/data-attributes) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut)

## Jump Cut

<a id="jump-cut"></a>Cut out a stretch inside one continuous shot, so the subject visibly jumps. Removes pauses, adds pace.

Same camera, same framing; the subject pops to a new position or expression and time skips forward.

- **When:** Talking heads, vlogs, tutorials and shorts where dead air or filler words must go and speed matters more than polish.
- **Watch out:** Tiny jumps (a few pixels of head movement) look like glitches; either jump far enough or hide the cut with a punch-in or B-roll.
- **Timing:** Cut on the gap: leave 2–4 frames of silence before the next word
- **Also called:** jumpcut, talking-head trim, pause removal
- **Card:** https://skills.varg.ai/skills/jump-cut/

### FFmpeg

Keep segments [0–3.2 s] and [4.1–8 s] of one take (times from silencedetect or a transcript):
```bash
ffmpeg -i take.mp4 -af silencedetect=noise=-35dB:d=0.4 -f null - 2>&1 | grep silence_
ffmpeg -i take.mp4 -filter_complex \
"[0:v]split[s1][s2];[0:a]asplit[t1][t2];\
 [s1]trim=0:3.2,setpts=PTS-STARTPTS[v1];[t1]atrim=0:3.2,asetpts=PTS-STARTPTS[a1];\
 [s2]trim=4.1:8,setpts=PTS-STARTPTS[v2];[t2]atrim=4.1:8,asetpts=PTS-STARTPTS[a2];\
 [v1][a1][v2][a2]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Same source, two clips, independent `data-media-start`:
```html
<video id="p1" src="take.mp4" data-start="0" data-duration="3.2" data-media-start="0" data-track-index="0" data-has-audio="true"></video>
<video id="p2" src="take.mp4" data-start="p1" data-duration="3.9" data-media-start="4.1" data-track-index="0" data-has-audio="true"></video>
```

### Remotion

Two `<Series.Sequence>` of the same file with different `trimBefore` values (in frames).
```tsx
<Series>
  <Series.Sequence durationInFrames={96}><Video src={take} /></Series.Sequence>
  <Series.Sequence durationInFrames={117}><Video src={take} trimBefore={123} /></Series.Sequence>
</Series>
```

### CapCut

Split around each pause and delete it; on desktop the transcript-based editing tools can mark pauses and filler words for removal (names vary by version).

Sources: [Wikipedia: jump cut](https://en.wikipedia.org/wiki/Jump_cut) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema) · [Remotion: <OffthreadVideo> (trimBefore)](https://www.remotion.dev/docs/offthreadvideo)

## Jump-Zoom Punch-In

<a id="jump-zoom-punch-in"></a>Hide a jump cut by scaling the next segment 110–130%. Reads as a second camera angle in talking heads.

Built on [Camera Punch-In](https://github.com/heygen-com/hyperframes/tree/main/registry/components/yt-camera-move) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

After the cut the same shot is suddenly tighter (or wider), so the jump feels like a deliberate camera change.

- **When:** Every 2–3 jump cuts in a talking head, on emphasis words, punchlines or a change of point.
- **Watch out:** Punching past ~130% on 1080p footage shows softness; alternate in and out rather than zooming tighter every time.
- **Timing:** Instant (0 frames) or a 3–6 frame ease into the new scale
- **Also called:** punch-in, zoom cut, digital zoom cut, punch in on a jump cut
- **Card:** https://skills.varg.ai/skills/jump-zoom-punch-in/

### FFmpeg

Static 125% punch-in on the second segment (crop keeps the centre, scale restores the size):
```bash
ffmpeg -i take.mp4 -filter_complex \
"[0:v]split[p][q];\
 [p]trim=0:2.5,setpts=PTS-STARTPTS[w];\
 [q]trim=2.5,setpts=PTS-STARTPTS,crop=iw/1.25:ih/1.25,scale=1920:1080,setsar=1[t];\
 [w][t]concat=n=2:v=1:a=0[v]" -map "[v]" -map 0:a out.mp4
```
`crop` evaluates w/h only once, so for an animated push use `scale=w='...t...':h=-2:eval=frame,crop=1920:1080` or `zoompan=...:d=1`.

### HyperFrames

Tween the inner wrapper, never the timed clip:
```js
tl.set("#seg2 .inner", { scale: 1.25 }, 2.5);           // instant punch
// or eased: tl.fromTo("#seg2 .inner", {scale:1.1}, {scale:1.25, duration:0.15, ease:"power2.out"}, 2.5);
```

### Remotion

```tsx
<Series.Sequence durationInFrames={75}>
  <AbsoluteFill style={{transform: 'scale(1.25)'}}><Video src={take} trimBefore={75} /></AbsoluteFill>
</Series.Sequence>
```
`pushCut()` from `@remotion/transitions/push-cut` (v4.0.500+) is a ready hard cut with a short punch-in and a 2-frame flash.

### CapCut

Select the segment after the split → Basic → Scale (e.g. 125%), or add Position/Scale keyframes for an eased push.

### Components

- Camera Punch-In (hyperframes): `npx hyperframes add yt-camera-move` · https://skills.varg.ai/component/hf.yt-camera-move/
- Push In (hyperframes): `npx hyperframes add push-in` · https://skills.varg.ai/component/hf.push-in/
- Lens Zoom (remocn): `npx shadcn@latest add @remocn/lens-zoom` · https://skills.varg.ai/component/remocn.lens-zoom/
- Drift (remocn): `npx shadcn@latest add @remocn/drift` · https://skills.varg.ai/component/remocn.drift/

Sources: [FFmpeg filters: crop](https://ffmpeg.org/ffmpeg-filters.html#crop) · [FFmpeg filters: zoompan](https://ffmpeg.org/ffmpeg-filters.html#zoompan) · [Remotion: pushCut](https://www.remotion.dev/docs/transitions/presentations/push-cut) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema)

## J-Cut

<a id="j-cut"></a>Shot B's sound starts before its picture. The ear arrives first and pulls the viewer into the next scene.

We still see A while B's voice or ambience fades in; then the picture cuts to B. On a timeline the audio forms a J.

- **When:** Scene changes, interview answers (hear the reply, then see the speaker), and pulling into a location by its sound.
- **Watch out:** A lead longer than 1–2 s without a visual cue confuses who is speaking.
- **Timing:** Audio leads by 0.3–2 s; short fade-in on B's audio
- **Also called:** J cut, audio lead, sound advance, split edit
- **Card:** https://skills.varg.ai/skills/j-cut/

### FFmpeg

Video cuts at 4 s; B's audio starts 1 s earlier. B's picture uses source 1–4 s, its audio source 0–4 s placed at 3 s:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:4,setpts=PTS-STARTPTS[va];[1:v]trim=1:4,setpts=PTS-STARTPTS[vb];\
 [va][vb]concat=n=2:v=1:a=0[v];\
 [0:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=out:st=3.4:d=0.6[aa];\
 [1:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,adelay=3000:all=1[ab];\
 [aa][ab]amix=inputs=2:normalize=0:duration=longest[a]" -map "[v]" -map "[a]" out.mp4
```
`normalize=0` stops amix from halving the level.

### HyperFrames

Mute B's video and add its sound as an `<audio>` clip that starts earlier, with the matching source offset:
```html
<video id="b" src="b.mp4" data-start="4" data-duration="3" data-media-start="1" muted data-track-index="0"></video>
<audio id="b-snd" src="b.mp4" data-start="3" data-duration="4" data-media-start="0" data-fade-in="0.3" data-track-index="2"></audio>
```

### Remotion

Picture and sound in separate sequences: B's `<Audio>` starts 30 frames before B's picture.
```tsx
<Sequence durationInFrames={120}><Video src={a} /></Sequence>
<Sequence from={120}><Video src={b} trimBefore={30} muted /></Sequence>
<Sequence from={90}><Audio src={b} /></Sequence>
```

### CapCut

Right-click the clip → Separate audio (mobile: Extract audio), then drag B's audio clip left under the end of A and add a fade-in.

Sources: [Wikipedia: J cut / L cut](https://en.wikipedia.org/wiki/J_cut) · [FFmpeg filters: adelay](https://ffmpeg.org/ffmpeg-filters.html#adelay) · [FFmpeg filters: amix](https://ffmpeg.org/ffmpeg-filters.html#amix) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema)

## L-Cut

<a id="l-cut"></a>Shot A's sound keeps playing after the picture cuts to B. Carries a line or a mood across the edit.

Picture changes to B (a reaction, B-roll, the next place) while A's voice or music continues underneath. On a timeline the audio forms an L.

- **When:** Reactions during dialogue, narration over B-roll, letting a moment breathe as you leave a scene.
- **Watch out:** Carrying speech too long over unrelated images makes the speaker feel disembodied.
- **Timing:** Audio tail 0.5–2 s past the cut; fade the tail out
- **Also called:** L cut, audio overlap, sound carry-over, split edit
- **Card:** https://skills.varg.ai/skills/l-cut/

### FFmpeg

Picture cuts at 3 s; A's audio runs to 4 s; B's audio joins at 4 s in sync (source 1 s):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:3,setpts=PTS-STARTPTS[va];[1:v]trim=0:3,setpts=PTS-STARTPTS[vb];\
 [va][vb]concat=n=2:v=1:a=0[v];\
 [0:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=out:st=3.4:d=0.6[aa];\
 [1:a]atrim=1:3,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,adelay=4000:all=1[ab];\
 [aa][ab]amix=inputs=2:normalize=0:duration=longest[a]" -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Keep A's sound as its own `<audio>` clip longer than A's muted picture; use `data-fade-out` for the tail:
```html
<video id="a" src="a.mp4" data-start="0" data-duration="3" muted data-track-index="0"></video>
<audio id="a-snd" src="a.mp4" data-start="0" data-duration="4" data-fade-out="0.6" data-track-index="2"></audio>
<video id="b" src="b.mp4" data-start="3" data-duration="3" data-track-index="1" data-has-audio="true"></video>
```

### Remotion

```tsx
<Sequence durationInFrames={90}><Video src={a} muted /></Sequence>
<Sequence durationInFrames={120}><Audio src={a} /></Sequence>  {/* audio runs 30 frames longer */}
<Sequence from={90}><Video src={b} /></Sequence>
```
Use `useCurrentFrame()` + `interpolate()` for the tail fade (the volume callback is no longer recommended).

### CapCut

Separate audio from clip A, trim A's video shorter, then extend A's audio clip under B and fade it out.

Sources: [Wikipedia: J cut / L cut](https://en.wikipedia.org/wiki/J_cut) · [FFmpeg filters: adelay](https://ffmpeg.org/ffmpeg-filters.html#adelay) · [FFmpeg filters: amix](https://ffmpeg.org/ffmpeg-filters.html#amix) · [Remotion: <OffthreadVideo> (trimBefore)](https://www.remotion.dev/docs/offthreadvideo) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema)

## Graphic Match Cut

<a id="graphic-match-cut"></a>Cut between two shots that share a shape, colour or position on screen, so the eye slides from one to the other.

Built on [Match Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/components/match-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A round clock face becomes a round moon; a spinning wheel becomes a spinning record. The shape stays put, the world changes.

- **When:** Time jumps, before/after, product reveals, and linking two ideas without words.
- **Watch out:** If the shapes are not in the same place and size the match is lost; align them first.
- **Timing:** Hard cut, or 2–6 frames of crossfade for a softer match
- **Also called:** match cut, shape match, visual match, form cut
- **Card:** https://skills.varg.ai/skills/graphic-match-cut/

### FFmpeg

Align B to A (scale/position) and cut on the frame where the shapes coincide; a very short fade can soften it:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[1:v]scale=iw*1.08:-2,crop=1920:1080:x=40:y=10[b2];\
 [0:v]trim=0:3,setpts=PTS-STARTPTS[a2];[b2]trim=0:3,setpts=PTS-STARTPTS[b3];\
 [a2][b3]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

Ready primitives: `npx hyperframes add match-cut` (a circle that hard-swaps scenes and matches the incoming circle), `text-match-cut`, `type-match-cut`, `morph-swap`.

### Remotion

Wrap B in a transform that lines its subject up with A's, then cut with `<Series>`; for a soft match use `fade()` with `linearTiming({durationInFrames: 4})`.

### CapCut

Align the shapes with Basic → Position/Scale (use the overlay track at reduced opacity as a guide), then cut. CapCut also publishes AI camera transitions for match cuts.

### Components

- Match Cut (hyperframes): `npx hyperframes add match-cut` · https://skills.varg.ai/component/hf.match-cut/
- Text Match Cut (hyperframes): `npx hyperframes add text-match-cut` · https://skills.varg.ai/component/hf.text-match-cut/
- Type Match Cut (hyperframes): `npx hyperframes add type-match-cut` · https://skills.varg.ai/component/hf.type-match-cut/
- Morph Swap (hyperframes): `npx hyperframes add morph-swap` · https://skills.varg.ai/component/hf.morph-swap/

Sources: [Wikipedia: match cut](https://en.wikipedia.org/wiki/Match_cut) · [CapCut: whip pan and match cut transitions](https://www.capcut.com/resource/ai-camera-transitions-whip-pan-match-cut) · [HyperFrames: compositions](https://hyperframes.heygen.com/concepts/compositions)

## Action Match Cut

<a id="action-match-cut"></a>A movement started in shot A finishes in shot B: a jump, a throw, a door swing carried across two angles.

Built on [Cut the Curve](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cut-the-curve) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The motion is continuous even though the angle or location changes, so the cut disappears into the action.

- **When:** Action, sports, dance and transformation edits (outfit changes, location jumps on a jump or spin).
- **Watch out:** If speed or direction differs between the two halves the jump becomes visible; match velocity, not just pose.
- **Timing:** Cut at peak velocity, usually 2–4 frames into the move
- **Also called:** match on action, movement match, kinetic match
- **Card:** https://skills.varg.ai/skills/action-match-cut/

### FFmpeg

Find the frame pair by eye (or with `ffmpeg -vf select` thumbnails), then trim both so the move continues:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=end_frame=73,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=12,setpts=PTS-STARTPTS[b];\
 [a][b]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

`npx hyperframes add cut-the-curve`: the outgoing subject accelerates (power4.in), swaps at peak speed, the incoming one continues on the same curve.

### Remotion

Same as a hard cut; tune `trimBefore` on B frame by frame in the Studio until the motion lines up.

### CapCut

Step frame by frame with the arrow keys, split both clips at the matching moment of the move, and butt them together.

### Components

- Cut the Curve (hyperframes): `npx hyperframes add cut-the-curve` · https://skills.varg.ai/component/hf.cut-the-curve/
- Match Cut (hyperframes): `npx hyperframes add match-cut` · https://skills.varg.ai/component/hf.match-cut/

Sources: [Wikipedia: match cut](https://en.wikipedia.org/wiki/Match_cut) · [Wikipedia: cutting on action](https://en.wikipedia.org/wiki/Cutting_on_action) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim)

## Sound Match Cut

<a id="sound-match-cut"></a>Two different sounds that rhyme (a scream and a train whistle) bridge the cut and link the two scenes.

The sound of A morphs into a similar sound in B at the cut point; the picture change rides on the sound.

- **When:** Scene transitions with a twist, comedic links, trailers.
- **Watch out:** If the two sounds do not share pitch or rhythm the link reads as noise.
- **Timing:** Hard cut on the sound peak; 50–200 ms audio crossfade
- **Also called:** sound bridge match, audio match cut, sonic match
- **Card:** https://skills.varg.ai/skills/sound-match-cut/

### FFmpeg

Hard-cut picture; crossfade the two rhyming sounds over 0.15 s:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v][1:v]concat=n=2:v=1:a=0[v];[0:a][1:a]acrossfade=d=0.15:c1=qsin:c2=qsin[a]" \
  -map "[v]" -map "[a]" out.mp4
```
Note: acrossfade overlaps the audio (o=1), so audio ends 0.15 s before video; pad with `apad` if needed.

### HyperFrames

Two `<audio>` clips overlapping by 0.15 s with `data-fade-out` / `data-fade-in`, picture cut on the same second.

### Remotion

Place the two sound effects as `<Audio>` in overlapping `<Sequence>`s around the cut frame; interpolate their volume over 4–6 frames.

### CapCut

Separate audio, drag the second sound under the cut and use Fade in/out on both audio clips.

Sources: [Wikipedia: match cut](https://en.wikipedia.org/wiki/Match_cut) · [FFmpeg filters: acrossfade](https://ffmpeg.org/ffmpeg-filters.html#acrossfade)

## Cut on Action

<a id="cut-on-action"></a>Change angle while the subject moves. The movement hides the cut and keeps continuity.

Built on [Cut the Curve](https://github.com/heygen-com/hyperframes/tree/main/registry/components/cut-the-curve) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Wide to close-up as a hand reaches, a person sits or a head turns; viewers watch the motion, not the edit.

- **When:** Any coverage of the same action from two angles: interviews, cooking, product handling, sport.
- **Watch out:** Cutting before the movement starts or after it ends loses the cover; cut in the first third of the motion.
- **Timing:** Cut 2–4 frames after movement begins; overlap a frame or two of action
- **Also called:** cutting on action, continuity cut, movement cut
- **Card:** https://skills.varg.ai/skills/cut-on-action/

### FFmpeg

Same as a hard cut: pick the out-frame on A and in-frame on B inside the motion (`trim=end_frame=` / `trim=start_frame=`).

### HyperFrames

Two `<video>` clips with `data-media-start` chosen so the move continues; `data-start="a"` keeps them butted.

### Remotion

Use `<Series>`; preview at full speed, the cut must be judged in motion.

### CapCut

Split both angles at the motion point; multi-camera clips can also be lined up on stacked tracks and cut between.

### Components

- Cut the Curve (hyperframes): `npx hyperframes add cut-the-curve` · https://skills.varg.ai/component/hf.cut-the-curve/

Sources: [Wikipedia: cutting on action](https://en.wikipedia.org/wiki/Cutting_on_action) · [Walter Murch, In the Blink of an Eye (rule of six)](https://en.wikipedia.org/wiki/In_the_Blink_of_an_Eye_(Murch_book)) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim)

## Smash Cut

<a id="smash-cut"></a>An abrupt cut from one extreme to its opposite (calm to chaos, loud to silent) at the most surprising moment.

Mid-sentence or mid-scream the picture and the sound slam into something completely different.

- **When:** Comedy beats, horror, waking from a dream, hooks that reverse expectation.
- **Watch out:** Cushioning it with a transition or a fade kills the shock.
- **Timing:** 0 frames; cut sound and picture on the same frame
- **Also called:** shock cut, hard contrast cut
- **Card:** https://skills.varg.ai/skills/smash-cut/

### FFmpeg

Cut both streams on the same frame, no fades; drop audio of B in hard (no afade):
```bash
ffmpeg -i calm.mp4 -i loud.mp4 -filter_complex \
"[0:v]trim=0:4.5,setpts=PTS-STARTPTS[v0];[0:a]atrim=0:4.5,asetpts=PTS-STARTPTS[a0];\
 [v0][a0][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Two clips butted with `data-start="a"`, no `data-fade-in` on B.

### Remotion

`<Series>` with no transition; make sure B's audio starts at full volume on its first frame.

### CapCut

Split mid-action and butt the next clip; leave Transitions empty and no audio fade.

Sources: [Wikipedia: smash cut](https://en.wikipedia.org/wiki/Smash_cut) · [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter)

## Cutaway / Insert

<a id="cutaway-insert"></a>Briefly leave the main shot for a detail or related shot, then come back. Shows what is talked about and hides edits.

Main speaker, then 1–3 s of the object, screen or place mentioned, then back to the speaker.

- **When:** Explainers, interviews, product demos, and to cover a cut in the main shot.
- **Watch out:** Inserts unrelated to what is being said feel like filler.
- **Timing:** 1–3 s per insert
- **Also called:** insert shot, cutaway, cut-in, detail shot
- **Card:** https://skills.varg.ai/skills/cutaway-insert/

### FFmpeg

Overlay the insert on top of the continuous main shot between 3 and 5 s (main audio continues):
```bash
ffmpeg -i main.mp4 -i insert.mp4 -filter_complex \
"[1:v]trim=0:2,setpts=PTS-STARTPTS+3/TB,scale=1920:1080[ins];\
 [0:v][ins]overlay=eof_action=pass[v]" -map "[v]" -map 0:a out.mp4
```

### HyperFrames

Put the insert on a higher z-index over the main clip:
```html
<video id="ins" class="clip" src="insert.mp4" data-start="3" data-duration="2" muted data-track-index="1" style="z-index:2"></video>
```

### Remotion

```tsx
<AbsoluteFill><Video src={main} /></AbsoluteFill>
<Sequence from={90} durationInFrames={60}><Video src={insert} muted /></Sequence>
```

### CapCut

Drag the insert onto the track above the main track (Overlay on mobile), stretch it to full frame, mute it.

Sources: [Wikipedia: cutaway](https://en.wikipedia.org/wiki/Cutaway_(filmmaking)) · [FFmpeg filters: overlay](https://ffmpeg.org/ffmpeg-filters.html#overlay) · [HyperFrames: data attributes](https://hyperframes.heygen.com/concepts/data-attributes)

## Cross-Cutting

<a id="cross-cutting"></a>Alternate between two or more scenes happening at the same time, building tension or comparison.

A, B, A, B… with shots getting shorter as the two lines converge.

- **When:** Chases, countdowns, before/after stories, two people preparing for the same moment.
- **Watch out:** Alternating without escalation (same lengths throughout) flattens the tension.
- **Timing:** Shorten each pair: e.g. 3 s, 2 s, 1.2 s, 0.8 s
- **Also called:** parallel editing, intercutting, parallel action
- **Card:** https://skills.varg.ai/skills/cross-cutting/

### FFmpeg

Generate segments from two sources with shrinking lengths, then concat:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]split=2[a1][a2];[1:v]split=2[b1][b2];\
 [a1]trim=0:3,setpts=PTS-STARTPTS[s1];[b1]trim=0:2,setpts=PTS-STARTPTS[s2];\
 [a2]trim=3:4.2,setpts=PTS-STARTPTS[s3];[b2]trim=2:2.8,setpts=PTS-STARTPTS[s4];\
 [s1][s2][s3][s4]concat=n=4:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

Alternate `<video>` clips with relative starts (`data-start="s1"`, `data-start="s2"` …) and source offsets that keep each storyline moving forward.

### Remotion

Build the list of `{src, trimBefore, frames}` in code and map it to `<Series.Sequence>`; shrink `frames` each round.

### CapCut

Lay storyline A on the main track, cut it into pieces and drop pieces of B between them.

Sources: [Wikipedia: cross-cutting](https://en.wikipedia.org/wiki/Cross-cutting) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim)

## Invisible Cut

<a id="invisible-cut"></a>Hide a cut inside a frame that is fully covered (a passing object, a dark wall, a blur) to fake one continuous shot.

Built on [Whip Pan Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/components/whip-pan-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The camera passes behind a pillar or into darkness; when it comes out we are somewhere else, with no visible edit.

- **When:** One-take illusions, travel and transformation reels, product reveals through an object.
- **Watch out:** If the cover does not fill the whole frame for at least one frame, the edge of the cut flashes.
- **Timing:** Cut on a fully covered frame; optionally a 2–4 frame crossfade inside the cover
- **Also called:** hidden cut, seamless cut, stitch cut, one-shot illusion, wipe-by
- **Card:** https://skills.varg.ai/skills/invisible-cut/

### FFmpeg

Cut on the fully covered frame and smooth it with a very short fade inside the cover (offset = A length - T):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB[a];[1:v]fps=30,settb=AVTB[b];\
 [a][b]xfade=transition=fade:duration=0.1:offset=3.9[v]" -map "[v]" out.mp4
```

### HyperFrames

Cover-and-cut overlays: `hw-scribble-transition` and `mk-clone-wall-transition` fill the frame, the host cuts beneath, then they clear. Camera versions: `whip-pan-cut`, `zoom-through-transition`.

### Remotion

Use `fade()` with `linearTiming({durationInFrames: 3})` placed exactly on the covered frames, or `TransitionSeries.Overlay` to drop a cover element over the cut without changing timing.

### CapCut

Cut on the dark/covered frame; add a short Mix (0.1–0.2 s) or a mask that follows the passing object if the cover is not perfect.

### Components

- Whip Pan Cut (hyperframes): `npx hyperframes add whip-pan-cut` · https://skills.varg.ai/component/hf.whip-pan-cut/
- Zoom Through Transition (hyperframes): `npx hyperframes add zoom-through-transition` · https://skills.varg.ai/component/hf.zoom-through-transition/
- Scribble Transition (hyperframes): `npx hyperframes add hw-scribble-transition` · https://skills.varg.ai/component/hf.hw-scribble-transition/
- Text Clone Wall Transition (hyperframes): `npx hyperframes add mk-clone-wall-transition` · https://skills.varg.ai/component/hf.mk-clone-wall-transition/
- Push Through (remocn): `npx shadcn@latest add @remocn/push-through` · https://skills.varg.ai/component/remocn.push-through/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: <TransitionSeries>](https://www.remotion.dev/docs/transitions/transitionseries) · [HyperFrames: compositions](https://hyperframes.heygen.com/concepts/compositions)

## In-Camera Whip Pan Cut

<a id="in-camera-whip-cut"></a>End shot A and start shot B with real fast pans in the same direction, and cut inside the motion blur.

Built on [Whip Pan Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/components/whip-pan-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The image streaks sideways into a blur and comes out of the same blur in a new place.

- **When:** Travel, energy reels, time jumps, "meanwhile" moments; shoot both whips at the same speed and direction.
- **Watch out:** Pans in opposite directions or at different speeds break the illusion.
- **Timing:** Cut in the 2–4 blurriest frames; whole whip 6–10 frames at 30 fps
- **Also called:** whip pan cut, swish pan, flash pan, whip transition (shot)
- **Card:** https://skills.varg.ai/skills/in-camera-whip-cut/

### FFmpeg

Cut on the blurriest frames; add synthetic horizontal blur around the cut to merge the two whips:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v][1:v]concat=n=2:v=1:a=0,gblur=sigma=30:sigmaV=0:enable='between(t,3.9,4.1)'[v]" -map "[v]" out.mp4
```
(`sigmaV=0` blurs horizontally only; A is 4 s long here.)

### HyperFrames

`whip-pan-cut` primitive (matched velocity, capped directional motion blur) or the `whip-pan` shader block.

### Remotion

Hard cut in `<Series>`; for footage without real whips use remocn `whipPan()` as a presentation.

### CapCut

Cut both clips at the blurriest frames; add a Blur effect for 2–3 frames over the cut, or use a whip-style transition (see the Whip Swipe card).

### Components

- Whip Pan Cut (hyperframes): `npx hyperframes add whip-pan-cut` · https://skills.varg.ai/component/hf.whip-pan-cut/
- Whip Pan (hyperframes): `npx hyperframes add whip-pan` · https://skills.varg.ai/component/hf.whip-pan/
- Whip Pan (remocn): `npx shadcn@latest add @remocn/whip-pan` · https://skills.varg.ai/component/remocn.whip-pan/

Sources: [Wikipedia: whip pan](https://en.wikipedia.org/wiki/Whip_pan) · [FFmpeg filters: gblur](https://ffmpeg.org/ffmpeg-filters.html#gblur) · [remocn: Whip Pan](https://remocn.dev/docs/transitions/whip-pan)

## Speed Ramp

<a id="speed-ramp"></a>Change playback speed within a shot (fast into a moment, slow on it, fast out) to stress the beat.

Built on [Beat Freeze Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/beat-freeze-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Motion races, suddenly drops into slow motion on the key moment, then snaps back to speed.

- **When:** Sport, action, product hero shots, music edits; shoot at 60/120 fps for clean slow parts.
- **Watch out:** Slowing 24/30 fps footage below ~0.5× stutters; ramps on talking heads distort speech.
- **Timing:** Ramp transitions of 4–8 frames between speeds; slow section 0.3–0.5×
- **Also called:** time ramp, speed curve, velocity ramp, ramping
- **Card:** https://skills.varg.ai/skills/speed-ramp/

### FFmpeg

FFmpeg has no speed curve; approximate with constant-speed segments (1× → 2× → 0.5×):
```bash
ffmpeg -i in.mp4 -filter_complex \
"[0:v]split=3[s1][s2][s3];[0:a]asplit=3[t1][t2][t3];\
 [s1]trim=0:2,setpts=PTS-STARTPTS[v1];[t1]atrim=0:2,asetpts=PTS-STARTPTS[a1];\
 [s2]trim=2:4,setpts=(PTS-STARTPTS)/2[v2];[t2]atrim=2:4,asetpts=PTS-STARTPTS,atempo=2[a2];\
 [s3]trim=4:5,setpts=(PTS-STARTPTS)*2[v3];[t3]atrim=4:5,asetpts=PTS-STARTPTS,atempo=0.5[a3];\
 [v1][a1][v2][a2][v3][a3]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -r 30 out.mp4
```
atempo accepts 0.5–100; chain it for more. Add `minterpolate=fps=60` for smoother slow motion.

### HyperFrames

A `rate` lane in `data-automation` (0.1–10, log-scale interpolation):
```html
<video src="clip.mp4" data-start="0" data-duration="4" data-track-index="0"
  data-automation='{"version":1,"lanes":[{"target":"rate","points":[{"t":0,"v":1},{"t":2,"v":4},{"t":4,"v":0.5}]}]}'></video>
```

### Remotion

`playbackRate` cannot be interpolated directly. Accumulate the rate per frame and pass it as `trimBefore`, as in Remotion's accelerated-video snippet (each frame wraps the video in `<Sequence from={frame}>`).

### CapCut

Select clip → Speed → Curve → a preset (Montage, Hero, Bullet, Jump Cut, Flash In, Flash Out) or Custom and drag the points.

### Components

- Beat Freeze Cut (hyperframes): `npx hyperframes add beat-freeze-cut` · https://skills.varg.ai/component/hf.beat-freeze-cut/

Sources: [Wikipedia: speed ramping](https://en.wikipedia.org/wiki/Speed_ramping) · [FFmpeg filters: setpts](https://ffmpeg.org/ffmpeg-filters.html#setpts) · [FFmpeg filters: atempo](https://ffmpeg.org/ffmpeg-filters.html#atempo) · [Remotion: speed ramp snippet](https://www.remotion.dev/docs/miscellaneous/snippets/accelerated-video) · [HyperFrames: speed ramps](https://hyperframes.heygen.com/reference/speed-ramps) · [CapCut: speed curve tool](https://www.capcut.com/tools/speed-ramp)

## Freeze Frame

<a id="freeze-frame"></a>Stop on a single frame for a beat, to introduce a character, land a joke or add a caption.

Built on [Beat Freeze Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/beat-freeze-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Motion halts on one frame (often with a flash, a zoom or a name card), then resumes or cuts away.

- **When:** Character intros, "record scratch" moments, highlights in sport, the end of a short.
- **Watch out:** Freezing on a blurred frame; pick a sharp frame with a clear expression.
- **Timing:** 0.5–2 s hold; often a 2-frame white flash on entry
- **Also called:** freeze, hold frame, still frame, frame hold
- **Card:** https://skills.varg.ai/skills/freeze-frame/

### FFmpeg

Freeze at 2 s for 1 s and resume (tpad clones the last frame; apad keeps audio in sync):
```bash
ffmpeg -i in.mp4 -filter_complex \
"[0:v]split[v1][v2];[v1]trim=0:2,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1[f];\
 [v2]trim=2,setpts=PTS-STARTPTS[r];[f][r]concat=n=2:v=1:a=0[v];\
 [0:a]asplit[a1][a2];[a1]atrim=0:2,asetpts=PTS-STARTPTS,apad=pad_dur=1[fa];\
 [a2]atrim=2,asetpts=PTS-STARTPTS[ra];[fa][ra]concat=n=2:v=0:a=1[a]" -map "[v]" -map "[a]" out.mp4
```
Alternative: `loop=loop=29:size=1:start=60,setpts=N/FRAME_RATE/TB` repeats frame 60.

### HyperFrames

Insert the held frame as an image clip (extract it first with ffmpeg), then resume the video with `data-media-start`:
```html
<img class="clip" src="held.png" data-start="2" data-duration="1" data-track-index="0" />
```
Arbitrary mid-source freezes need that pre-extracted still.

### Remotion

`<Sequence freeze={60}>` (v4.0.476+) or `<Freeze frame={60} active={(f) => f >= 60 && f < 90}>`; videos pause while frozen.

### CapCut

Playhead on the frame → Freeze in the toolbar (desktop, inserts a ~3 s still) or Edit → Freeze (mobile); drag its edges to set the hold.

### Components

- Beat Freeze Cut (hyperframes): `npx hyperframes add beat-freeze-cut` · https://skills.varg.ai/component/hf.beat-freeze-cut/
- Freeze-Frame Dressing (hyperframes): `npx hyperframes add freeze-frame-dressing` · https://skills.varg.ai/component/hf.freeze-frame-dressing/

Sources: [Wikipedia: freeze frame shot](https://en.wikipedia.org/wiki/Freeze_frame_shot) · [FFmpeg filters: tpad](https://ffmpeg.org/ffmpeg-filters.html#tpad) · [FFmpeg filters: loop](https://ffmpeg.org/ffmpeg-filters.html#loop) · [Remotion: <Freeze>](https://www.remotion.dev/docs/freeze) · [Remotion: <Sequence>](https://www.remotion.dev/docs/sequence) · [CapCut: freeze frame (resource article)](https://www.capcut.com/resource/davinci-resolve-freeze-frame)

## Beat-Synced Cut

<a id="beat-synced-cut"></a>Place cuts on the beats of the music so the edit feels driven by the track.

Built on [Beat Timeline](https://github.com/heygen-com/hyperframes/tree/main/registry/components/beat-timeline) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Every cut lands on a kick, snare or downbeat; bigger changes on the bar or the drop.

- **When:** Montages, music videos, reels, ads with a music bed.
- **Watch out:** Cutting on every single beat for a whole piece gets monotonous; vary between beats, half-bars and bars.
- **Timing:** Cut 1–2 frames before the transient so the change lands with the sound
- **Also called:** cut to the beat, beat sync, music sync, auto beat
- **Card:** https://skills.varg.ai/skills/beat-synced-cut/

### FFmpeg

FFmpeg has no beat tracker. Get beat times elsewhere (e.g. `aubio beat song.wav`, librosa, or `npx hyperframes beats`), then trim each shot to the gap between beats:
```bash
# beats.txt: 0.00 0.52 1.04 1.56 ...
ffmpeg -i s1.mp4 -i s2.mp4 -i s3.mp4 -i song.wav -filter_complex \
"[0:v]trim=0:0.52,setpts=PTS-STARTPTS[a];[1:v]trim=0:0.52,setpts=PTS-STARTPTS[b];\
 [2:v]trim=0:1.04,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -shortest out.mp4
```

### HyperFrames

`npx hyperframes beats` writes a Studio beat grid for the music `<audio>` (`data-timeline-role="music"`); for a full beat-cut video use the music-to-video workflow. Blocks: `beat-timeline`, `beat-accent`, `beat-freeze-cut`.

### Remotion

Convert beat seconds to frames (`Math.round(t * fps)`), compute each `durationInFrames` as the difference, map to `<Series.Sequence>`, and add `<Audio>` for the track.

### CapCut

Select the music → Beats (auto beat markers) → cut clips to the markers; templates also auto-sync clips to beats.

### Components

- Beat Timeline (hyperframes): `npx hyperframes add beat-timeline` · https://skills.varg.ai/component/hf.beat-timeline/
- Beat Accent (hyperframes): `npx hyperframes add beat-accent` · https://skills.varg.ai/component/hf.beat-accent/
- Beat Freeze Cut (hyperframes): `npx hyperframes add beat-freeze-cut` · https://skills.varg.ai/component/hf.beat-freeze-cut/
- varg Music Video (varg): `git clone https://github.com/vargHQ/code2video-templates && python3 code2video-templates/varg-music-video/scripts/songmap.py song.mp3 --lyrics lyrics.txt --out songmap.json` · https://skills.varg.ai/component/varg.music-video/
- Anime Triple Split (varg): `git clone https://github.com/vargHQ/code2video-templates && cd code2video-templates/anime-triple-split && bash make.command` · https://skills.varg.ai/component/varg.anime-triple-split/

Sources: [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut)

## Split Screen

<a id="split-screen"></a>Show two or more shots at once in separate panels: comparison, reaction or simultaneous action.

Built on [Comparison Split](https://github.com/heygen-com/hyperframes/tree/main/registry/components/comparison-split) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The frame divides into halves, thirds or a grid, each panel playing its own clip.

- **When:** Before/after, reaction videos, duets, comparisons, phone calls.
- **Watch out:** Panels with the important subject cropped off at the divider; reframe each clip for its panel.
- **Timing:** Panels can slide in over 8–12 frames, then hold
- **Also called:** split-screen, side by side, multi-screen, picture grid, triptych
- **Card:** https://skills.varg.ai/skills/split-screen/

### FFmpeg

Left/right halves at 1920×1080 (each clip cropped to its centre half):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]crop=iw/2:ih,scale=960:1080[l];[1:v]crop=iw/2:ih,scale=960:1080[r];\
 [l][r]hstack=inputs=2[v]" -map "[v]" -map 0:a -shortest out.mp4
```
For grids use `xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0`.

### HyperFrames

Two clips on separate tracks clipped with CSS (`clip-path` or half-width wrappers); animated dividers: `comparison-split`, `before-after-wipe`.

### Remotion

```tsx
<AbsoluteFill style={{flexDirection: 'row'}}>
  <div style={{flex: 1, overflow: 'hidden'}}><Video src={a} style={{height: '100%', objectFit: 'cover'}} /></div>
  <div style={{flex: 1, overflow: 'hidden'}}><Video src={b} muted style={{height: '100%', objectFit: 'cover'}} /></div>
</AbsoluteFill>
```

### CapCut

Stack clips on overlay tracks and set Position/Scale per panel, or use a split-screen layout/template.

### Components

- Comparison Split (hyperframes): `npx hyperframes add comparison-split` · https://skills.varg.ai/component/hf.comparison-split/
- Before After Wipe (hyperframes): `npx hyperframes add before-after-wipe` · https://skills.varg.ai/component/hf.before-after-wipe/
- Anime Triple Split (varg): `git clone https://github.com/vargHQ/code2video-templates && cd code2video-templates/anime-triple-split && bash make.command` · https://skills.varg.ai/component/varg.anime-triple-split/
- Comic Panels (remocn): `npx shadcn@latest add @remocn/comic-panels` · https://skills.varg.ai/component/remocn.comic-panels/

Sources: [Wikipedia: split screen](https://en.wikipedia.org/wiki/Split_screen_(video_production)) · [FFmpeg filters: xstack](https://ffmpeg.org/ffmpeg-filters.html#xstack)

## Montage Sequence

<a id="montage-sequence"></a>A run of short shots, usually on music, that compresses time or builds one feeling.

Many 0.5–2 s shots in a row with a common rhythm, often with one recurring visual motif.

- **When:** Passage of time, progress, travel recaps, product feature runs, brand films.
- **Watch out:** Shots that are all the same size and motion; vary wide, medium and close and the direction of movement.
- **Timing:** 0.5–2 s per shot, on beats or half-bars
- **Also called:** montage, sequence of shots, training montage, time-compression montage
- **Card:** https://skills.varg.ai/skills/montage-sequence/

### FFmpeg

Concat many normalized shots (the concat filter accepts mixed sources after scaling):
```bash
ffmpeg -i s1.mp4 -i s2.mp4 -i s3.mp4 -i song.mp3 -filter_complex \
"[0:v]trim=0:1.2,setpts=PTS-STARTPTS,scale=1080:1920,setsar=1,fps=30[a];\
 [1:v]trim=0:0.8,setpts=PTS-STARTPTS,scale=1080:1920,setsar=1,fps=30[b];\
 [2:v]trim=0:1.6,setpts=PTS-STARTPTS,scale=1080:1920,setsar=1,fps=30[c];\
 [a][b][c]concat=n=3:v=1:a=0[v]" -map "[v]" -map 3:a -shortest out.mp4
```

### HyperFrames

Chain clips with relative `data-start` values; keep music on its own `<audio>` track; see `beat-timeline`.

### Remotion

Map an array of shots to `<Series.Sequence>`; put the music in a single `<Audio>` outside the series.

### CapCut

Import all shots, use AutoCut or a template, or cut manually to Beats markers.

### Components

- varg Music Video (varg): `git clone https://github.com/vargHQ/code2video-templates && python3 code2video-templates/varg-music-video/scripts/songmap.py song.mp3 --lyrics lyrics.txt --out songmap.json` · https://skills.varg.ai/component/varg.music-video/
- Beat Timeline (hyperframes): `npx hyperframes add beat-timeline` · https://skills.varg.ai/component/hf.beat-timeline/

Sources: [Wikipedia: montage (filmmaking)](https://en.wikipedia.org/wiki/Montage_(filmmaking)) · [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter)

## Rhythmic Cutting (3-2-1)

<a id="rhythmic-cutting-3-2-1"></a>Shorten shot lengths step by step (3 s, 2 s, 1 s, half a second) to build momentum into a payoff.

Built on [Beat Timeline](https://github.com/heygen-com/hyperframes/tree/main/registry/components/beat-timeline) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Each shot is shorter than the last until the edit lands on a longer hero shot or a drop.

- **When:** Before a reveal, a drop in the music, a punchline or the product hero shot.
- **Watch out:** Accelerating with no payoff shot at the end; the rhythm needs a landing.
- **Timing:** e.g. 90, 60, 30, 15, 15 frames at 30 fps, then a 2–3 s hold
- **Also called:** accelerating cuts, shrinking shot lengths, 3-2-1 rhythm, build-up cutting
- **Card:** https://skills.varg.ai/skills/rhythmic-cutting-3-2-1/

### FFmpeg

Generate trims from a list of durations and concat (bash loop builds the filter):
```bash
d=(3 2 1 0.5 0.5); f=""; i=0
for x in "${d[@]}"; do f+="[$i:v]trim=0:$x,setpts=PTS-STARTPTS,fps=30[v$i];"; i=$((i+1)); done
for j in $(seq 0 $((i-1))); do f+="[v$j]"; done
ffmpeg -i s1.mp4 -i s2.mp4 -i s3.mp4 -i s4.mp4 -i s5.mp4 -filter_complex "${f}concat=n=$i:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

Set `data-duration` per clip to 3, 2, 1, 0.5, 0.5 with `data-start` chained to the previous id.

### Remotion

```tsx
const lengths = [90, 60, 30, 15, 15, 75];
<Series>{shots.map((s, i) => <Series.Sequence key={i} durationInFrames={lengths[i]}><Video src={s} /></Series.Sequence>)}</Series>
```

### CapCut

Trim clips to shrinking lengths on the main track; use Beats markers for the half-bar and bar positions.

### Components

- Beat Timeline (hyperframes): `npx hyperframes add beat-timeline` · https://skills.varg.ai/component/hf.beat-timeline/

Sources: [Walter Murch, In the Blink of an Eye (rule of six)](https://en.wikipedia.org/wiki/In_the_Blink_of_an_Eye_(Murch_book)) · [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter)

## Pattern Interrupt

<a id="pattern-interrupt"></a>Every few seconds of a short, break the visual pattern: angle, zoom, graphic, sound hit, so attention resets.

Built on [Beat Accent](https://github.com/heygen-com/hyperframes/tree/main/registry/components/beat-accent) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A sudden zoom, a cut to B-roll, an on-screen graphic, a flash or a sound effect at regular intervals.

- **When:** Shorts, reels, TikToks and YouTube intros where viewers decide in seconds whether to stay.
- **Watch out:** Interrupts that do not relate to the words feel random; tie each one to a beat of the script.
- **Timing:** Every 2–4 s; each interrupt 3–10 frames
- **Also called:** visual reset, retention cut, scroll stopper, hook reset
- **Card:** https://skills.varg.ai/skills/pattern-interrupt/

### FFmpeg

Combine a punch-in segment, a 2-frame flash and a whoosh SFX at 3 s:
```bash
ffmpeg -i talk.mp4 -i whoosh.wav -filter_complex \
"[0:v]split[p][q];[p]trim=0:3,setpts=PTS-STARTPTS[w];\
 [q]trim=3,setpts=PTS-STARTPTS,crop=iw/1.2:ih/1.2,scale=1080:1920,setsar=1[t];\
 [w][t]concat=n=2:v=1:a=0,eq=brightness=0.6:enable='between(t,3,3.066)'[v];\
 [1:a]adelay=2950:all=1[s];[0:a][s]amix=inputs=2:normalize=0:duration=first[a]" \
  -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

`beat-accent` (impact flash + micro scale pulse), `editorial-flash-overlay`, a punch-in tween on `.inner`, plus an SFX `<audio>` clip.

### Remotion

Schedule interrupts as an array of frames; render a `<Sequence>` per interrupt holding a scale change, a flash `<AbsoluteFill>` or an `<Audio>` SFX.

### CapCut

Split every few seconds and alternate Scale, add a Flash/Shake effect or a sticker, and drop a whoosh from Audio → Sound effects.

### Components

- Beat Accent (hyperframes): `npx hyperframes add beat-accent` · https://skills.varg.ai/component/hf.beat-accent/
- Editorial Flash Overlay (hyperframes): `npx hyperframes add editorial-flash-overlay` · https://skills.varg.ai/component/hf.editorial-flash-overlay/
- Impact Shake (remocn): `npx shadcn@latest add @remocn/impact-shake` · https://skills.varg.ai/component/remocn.impact-shake/
- Camera Shake (hyperframes): `npx hyperframes add camera-shake` · https://skills.varg.ai/component/hf.camera-shake/

Sources: [FFmpeg filters: crop](https://ffmpeg.org/ffmpeg-filters.html#crop) · [FFmpeg filters: amix](https://ffmpeg.org/ffmpeg-filters.html#amix) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema)

## B-Roll Overlay Cut

<a id="b-roll-overlay"></a>Keep the A-roll voice running and lay B-roll pictures over it; edits in the A-roll disappear under the cover.

We hear the speaker continuously while seeing what they describe, returning to their face for key lines.

- **When:** Interviews, explainers, UGC ads, documentaries; whenever the speaker's face is not the information.
- **Watch out:** Covering emotional or key lines; let the face carry those.
- **Timing:** B-roll shots 1.5–4 s; enter and leave on phrase boundaries
- **Also called:** B-roll, cover footage, overlay cut, A-roll/B-roll
- **Card:** https://skills.varg.ai/skills/b-roll-overlay/

### FFmpeg

Overlay B-roll from 1.5 s for 2 s; A-roll audio continues:
```bash
ffmpeg -i aroll.mp4 -i broll.mp4 -filter_complex \
"[1:v]trim=0:2,setpts=PTS-STARTPTS+1.5/TB,scale=1920:1080,setsar=1[b];\
 [0:v][b]overlay=eof_action=pass[v]" -map "[v]" -map 0:a -c:a copy out.mp4
```
`setpts=...+1.5/TB` shifts the B-roll to start at 1.5 s; `eof_action=pass` returns to A-roll after it ends.

### HyperFrames

B-roll `<video muted>` clip on a higher track/z-index over the A-roll clip; A-roll keeps `data-has-audio="true"`.

### Remotion

```tsx
<AbsoluteFill><Video src={aroll} /></AbsoluteFill>
<Sequence from={45} durationInFrames={60}><Video src={broll} muted /></Sequence>
```

### CapCut

Drag B-roll onto the overlay track above the A-roll (mobile: Overlay → Add overlay), resize to full frame, mute it.

Sources: [Wikipedia: B-roll](https://en.wikipedia.org/wiki/B-roll) · [FFmpeg filters: overlay](https://ffmpeg.org/ffmpeg-filters.html#overlay) · [HyperFrames: data attributes](https://hyperframes.heygen.com/concepts/data-attributes)

## FFmpeg Concat Demuxer (Lossless)

<a id="ffmpeg-concat-demuxer"></a>Join files that share codec, resolution, fps and audio format without re-encoding, from a text list.

Plain hard cuts; output quality identical to the inputs.

- **When:** Joining segments rendered by the same pipeline (same encoder settings), chunked renders, camera files from one device.
- **Watch out:** Mixed sources: different codecs, sizes, fps or audio sample rates give glitches, wrong durations or no audio.
- **Timing:** Hard cuts only; inpoint/outpoint snap to packets
- **Also called:** concat demuxer, -f concat, ffconcat, lossless join, stream copy join
- **Card:** https://skills.varg.ai/skills/ffmpeg-concat-demuxer/

### FFmpeg

```bash
cat > list.txt <<'EOF'
ffconcat version 1.0
file 'part1.mp4'
file 'part2.mp4'
inpoint 1.0
outpoint 3.0
EOF
ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4
```
`inpoint`/`outpoint` work best with intra-frame codecs; with H.264 the first packets before the in-point leak in (a 2 s outpoint test gave 2.09 s). For frame-accurate trims, re-encode with the concat filter. `-safe 0` allows absolute/odd paths.

Sources: [FFmpeg formats: concat demuxer](https://ffmpeg.org/ffmpeg-formats.html#concat)

## FFmpeg Concat Filter (Re-encode)

<a id="ffmpeg-concat-filter"></a>Join any sources frame-accurately by decoding, normalizing and re-encoding them in one filter graph.

Plain hard cuts at exact frames, from mixed cameras, phones and AI generations.

- **When:** Mixed resolutions, fps or codecs; whenever trims must be frame-accurate.
- **Watch out:** Forgetting to normalize: concat needs matching size, SAR and pixel format per stream, and the same stream count per segment.
- **Timing:** Hard cuts
- **Also called:** concat filter, filter_complex concat, re-encode join
- **Card:** https://skills.varg.ai/skills/ffmpeg-concat-filter/

### FFmpeg

Three segments with video + audio each, normalized to 1080×1920 at 30 fps:
```bash
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -filter_complex \
"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,setsar=1,fps=30[v0];[0:a]aresample=48000[a0];\
 [1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,setsar=1,fps=30[v1];[1:a]aresample=48000[a1];\
 [2:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:-1:-1,setsar=1,fps=30[v2];[2:a]aresample=48000[a2];\
 [v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
Input order is segment by segment: v,a of segment 1, then v,a of segment 2. A clip without audio needs a silent stream (`anullsrc` + `atrim`) so every segment has the same streams.

Sources: [FFmpeg filters: concat](https://ffmpeg.org/ffmpeg-filters.html#concat-filter) · [FFmpeg filters: trim](https://ffmpeg.org/ffmpeg-filters.html#trim)

## Audio Crossfades, J and L in FFmpeg

<a id="ffmpeg-audio-crossfade-jl"></a>Crossfade audio with acrossfade, or build J/L-cuts by delaying one track with adelay and mixing with amix.

Sound changes smoothly or leads/trails the picture cut.

- **When:** Every join with dialogue or music; J/L-cuts for interviews and scene changes.
- **Watch out:** amix's default normalization halves levels per input; set `normalize=0` and control gain yourself.
- **Timing:** Crossfade 0.05–1 s; J/L lead or tail 0.3–2 s
- **Also called:** acrossfade, afade, adelay amix, audio split edit, audio overlap
- **Card:** https://skills.varg.ai/skills/ffmpeg-audio-crossfade-jl/

### FFmpeg

Crossfade (overlap by d, curves from afade: tri, qsin, hsin, esin, log, exp…):
```bash
[0:a][1:a]acrossfade=d=0.5:c1=tri:c2=tri[a]
```
J-cut (B's audio 1 s before B's picture, cut at 4 s):
```bash
[0:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=out:st=3.4:d=0.6[aa];
[1:a]atrim=0:4,asetpts=PTS-STARTPTS,afade=t=in:d=0.3,adelay=3000:all=1[ab];
[aa][ab]amix=inputs=2:normalize=0:duration=longest[a]
```
`adelay` takes milliseconds per channel (`1500|500`), `S` suffix for samples, `s` for seconds; `all=1` applies one delay to all channels.

Sources: [FFmpeg filters: acrossfade](https://ffmpeg.org/ffmpeg-filters.html#acrossfade) · [FFmpeg filters: adelay](https://ffmpeg.org/ffmpeg-filters.html#adelay) · [FFmpeg filters: amix](https://ffmpeg.org/ffmpeg-filters.html#amix)

## Remotion Overlay on a Cut

<a id="remotion-overlay-cut"></a>Keep a hard cut but draw something over it (flash, light leak, SFX graphic) without shortening the video.

Built on [Light Leak](https://remocn.dev/r/light-leak.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

A hard cut hidden under a short overlay centred on the cut point.

- **When:** Light leaks, flashes, whoosh graphics and stickers on cuts where the timing must not change.
- **Watch out:** Putting an overlay next to a transition or another overlay (not allowed).
- **Timing:** Overlay 8–30 frames, centred on the cut; shift with offset
- **Also called:** TransitionSeries.Overlay, cut overlay, light leak overlay, flash on cut
- **Card:** https://skills.varg.ai/skills/remotion-overlay-cut/

### Remotion

Requires v4.0.415+:
```tsx
import {TransitionSeries} from '@remotion/transitions';
import {lightLeak} from '@remotion/effects/light-leak';
import {Solid, interpolate, useCurrentFrame} from 'remotion';

const Leak = () => {
  const f = useCurrentFrame();
  return <Solid width={1920} height={1080} effects={[lightLeak({seed: 3, progress: interpolate(f, [0, 30], [0, 1], {extrapolateRight: 'clamp'})})]} />;
};

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><A /></TransitionSeries.Sequence>
  <TransitionSeries.Overlay durationInFrames={30}><Leak /></TransitionSeries.Overlay>
  <TransitionSeries.Sequence durationInFrames={90}><B /></TransitionSeries.Sequence>
</TransitionSeries>
// total stays 180 frames
```
`offset` (default 0) moves the overlay earlier (negative) or later. `lightLeak()` uses WebGL2.

### Components

- Light Leak (remocn): `npx shadcn@latest add @remocn/light-leak` · https://skills.varg.ai/component/remocn.light-leak/
- Editorial Flash Overlay (hyperframes): `npx hyperframes add editorial-flash-overlay` · https://skills.varg.ai/component/hf.editorial-flash-overlay/

Sources: [Remotion: <TransitionSeries>](https://www.remotion.dev/docs/transitions/transitionseries) · [Remotion: lightLeak() effect](https://www.remotion.dev/docs/effects/light-leak)
