# From the prototype to a real video

## Before the first paid run

- Every character, product and place in frame has an image reference. Without one, a stand-in can come back literally.
- The clip has no text, labels, outlines or UI. Whole seconds, 24 fps. Look at the tail.
- Generate at 480p first, then upscale or re-render only the winners. Re-check the higher resolution: motion can change.
- Runs of 4 to 15 s, one location. Don't split one continuous scene into tiny runs: faces and light drift between generations.
- Quote it, get a yes, run ONE short test, then the batch.

## The prompt, in this order

```text
@video1 is rehearsal footage: stand-ins walked the scene so camera, timing and movement could be locked. Take from it
ONLY the camera path and framing, the timing of every action and cut, and where each element is and how it moves. No
shape, proportion, surface, colour or lighting from @video1 belongs in the final frame. The result must not look like @video1.

@image1 is <character>: <identity details in words too>. @image2 is <place>: <what is where>.
Only these people exist: <count and names>.

Look: <one line from the moodboard: film stock, lens feel, palette>.
Light: <direction, source, Kelvin or a named reference>. Ignore any lighting in @video1.

N shots, hard cuts exactly as in @video1:
1. 0.0-3.5 s. <Shot size and angle as the previz shows them>. <Who does what>. Camera: <the move, in words>.
   End state: <position, facing, what they hold>.
2. 3.5-6.0 s. Continuing from that end state. <...>. Camera: <...>.

Where a stand-in's proportions differ from the real object's, keep its path and timing and give it true proportions.
If the words and @video1 disagree about position or motion, @video1 wins.
No text, letters, numbers, logos or UI. No music. No dialogue unless written above.
```

Why each part is there:

| part | evidence |
|---|---|
| "only the camera, timing, positions" | the same line was reached separately by unrelated users writing in Japanese, Chinese and English |
| don't name the shapes | "A prompt that names the proxies' shapes ('the box figure becomes', 'each cone is') anchors the model on those shapes and it renders them as they are." (Scenario) |
| name what not to inherit | "Do not inherit @Video1's low-poly geometry, faceted surfaces, mannequin anatomy... viewport lighting or Blender overlays." (GrandVisionsAI, 361 bookmarks) |
| describe the shot as the previz shows it | our run: 2 of 2 shots with conflicting words followed the words. "any inconsistency between previz and prompt weakens the effect. So subtract" (k_matsumaru) |
| name each camera move | our run: the one shot that named its move kept it; of 6 that didn't, 3 kept it, 1 stopped and 2 reversed. Small sample. Also recommended by aisongman |
| end state per beat | atsu_mada's template; stops the next beat from jumping |
| identity in words too | the model can't read a detail the source doesn't show: "'Clearly visible' in the prompt can't give the model information the source video doesn't provide." (cellinlab) |
| tie-break clause | Scenario's sheet uses it. We didn't test it. Our conflicts above had no such clause |

For loose guidance instead of strict: say "broad choreography and camera movement", because the same reference can be used
tightly or loosely. Prompts that keep only positional relations let the model add speed the source didn't have.

## Storyboard pages instead of a clip

PJ Ace's block makes boards behave as key frames:

```text
STORYBOARD
Follow panels 1 to 26 in order, each a key frame: match camera position, framing, screen direction and action, moving
handheld between panels; cut only where the shot number changes. The panels are grey previz stand-ins; every look comes
from the references and this text.
```

## Other control videos

- **Depth map of the clip or an act-out** (Depth Anything): two reports say it keeps the camera and frees the performance. Loses faces.
- **Motion blur** helped two pros on fast objects.
- **Colour-coded parts** can tell the model what's what, as in Aharon Rabinowitz's Cinema 4D thread: "Ignore its flat color-coded parts, plain sky, and placeholder boxes."
- **White clay** with an explicit line (@aratamadao, translated): "The reference video is untextured white clay. Use only the motion, timing, eye movement, camera and overall silhouette. Ignore the white colour, rough surfaces and lighting." It lets the model redraw seams as natural flesh, though details drift unless you write them.

## After generation: check it

```bash
uv run scripts/measure_shot.py previz.mp4 --start 0 --end 3.5
uv run scripts/measure_shot.py generated.mp4 --start 0 --end 3.5
python3 scripts/compare.py previz.mp4 generated.mp4 --out qa --video
```

Compare direction and size of the move. Check cut times. Look at frames side by side. A 2D measure can't tell a pan from a
truck, and it's weak on clips with few background features: trust the `trust` field and your eyes. Video models also
return slightly wrong lengths (one report: 9.0 s from a 9.2 s reference), so stretch the clip back before cutting it in.

Fix small things in the edit and regenerate only what the edit can't fix. Repair ladder, cheapest first: re-cut; rerun with
words changed; simplify the previz around the failure; split the run; change route (storyboard, depth, or plain prompt).

## Model notes

| model | what's reported |
|---|---|
| Seedance 2.5 | Best followed by far. Holds positions and cuts, and usually camera. Drifts on contact, fast action, identity in fights. Copies stiffness. One provider refused a grey mannequin clip, so try a tint. Reports conflict on 2.5 vs 2.0: @reidhannaford found 2.5 worse on identical inputs, @PocketScreenAI better on light |
| Wan 3 | Flips between copying and ignoring |
| Kling 4 | Tended to ignore the previz in the one test found. Keyframes and start/end frames work better there |
| MiniMax H3 | Reads proxies literally; its reference route kept layout well in one report (Japanese signboards too) |
| Veo 3.1 | No evidence found |
