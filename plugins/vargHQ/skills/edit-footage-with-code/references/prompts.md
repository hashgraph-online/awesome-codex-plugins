# Prompts

Written for this skill's loop, after reading the prompts practitioners published. Replace everything in `<angle brackets>`. Each one is short because the numbers live in the skill: name a number here only to change it.

## Plain cut of a talking head

```text
Use the edit-footage-with-code skill. Edit <take.mp4> into a clean cut.
Target length: <about N minutes, or "whatever is left once it is tight">.
Remove dead air, retakes and stumbles. Pick the best take of any repeated line.
Keep any pause right before a number or a punchline, and list them for me.
Stop after the plan for my yes, and again after the rough cut for me to listen.
No captions, graphics or music yet.
```

## Short vertical ad from raw takes

```text
Use the edit-footage-with-code skill. Edit <raw/> into a 9:16 ad of about <30> s that follows <style/ad.md>.
Hook first, then <problem, proof, offer>. Pick the best take of each line.
No gap over 0.45 s. No shot under 1.2 s. Do not speed up my voice.
Captions: 1-3 words chunked by meaning, lower third, never over my face.
No whoosh unless I ask. Show prices exactly as I say them.
Master to -14 LUFS. Give me a review page with the takes you chose and every cut.
```

## Long video with graphics on a locked cut

```text
Use the edit-footage-with-code skill with <HyperFrames | Remotion>.
The spoken cut in <edit/acut.mp4> is locked. Do not change it.
From its transcript, list the moments that need something on screen and why, at most one card per <10> s.
Show me one still per card. After I approve, build each card as a separate plate that enters on its word
and sits away from my face. Render a 20 s sample before the rest.
```

## Add captions only

```text
Use the edit-footage-with-code skill. Add captions to <video.mp4> with <HyperFrames | Remotion>.
Transcribe this exact file and time every caption from that transcript.
<Script is in script.md: take spelling from it, keep the times from the transcript.>
<3-5 words | 1-3 words> per caption, broken by meaning. No cue under 0.35 s. Inside the title-safe area and away from the face.
Check the spelling of every name on the web. Render, then show me a contact sheet.
```

## Learn a style from references, once per format

```text
Study these reference videos: <link 1> <link 2> <link 3>.
Measure, do not describe: cuts per minute, shortest and median shot, caption words and position, zoom levels,
share of B-roll, music level, how the first 3 seconds work. Label anything you could not measure.
Write style/<format>.md using the template in edit-footage-with-code's notes-and-rules.md.
Treat these as inspiration, never a copy: my face, my voice, my brand.
```

## Fix notes after a watch

```text
These are my notes after watching all of it. Fix exactly these and nothing else. Scenes <1, 3> are approved: do not touch them.
<00:27: the last word is clipped.>
<01:02: punch-in too strong. Reduce it, keep the eyes at the same height.>
<00:43: show screenshot.png while I explain this, return to me when the explanation ends.>
Under each note, write what you changed or why you did not. Re-render only the changed ranges.
Then propose a rule for each note that should never come up again, and wait for my yes before saving it to rules.md.
```

## Turn an approved edit into a reusable skill

```text
Turn this approved edit into a small style file for this format. Include my corrections, my pacing and your checks.
Separate general rules from choices specific to this video. Turn every numeric rule into a check in QA.
```

## Independent review, for a sub-agent that has not seen the work

```text
You did not make this video and owe it nothing. Watch <out.mp4> through its frames and <qa/qa.json>, against <style/format.md>.
Write a verdict, then problems ranked by what a viewer would notice, each with a timecode and evidence, then the top 5 fixes.
Do not edit anything. Do not soften it. Separately list what you could not verify, including anything that needs ears.
```

## Short instructions once it is set up

Once the style file exists, plain short requests work. These are from Remotion's maker:

```text
import videos from ~/Downloads folder
put the videos in a sequence
trim the silence off them
generate captions
fix typos in captions
```
