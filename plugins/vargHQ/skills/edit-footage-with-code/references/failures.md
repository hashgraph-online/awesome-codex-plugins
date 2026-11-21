# What goes wrong, and how you can tell

Ranked by how many independent people report it and what it costs. This is our judgment, not a measured frequency. "Detect" is what you can check yourself.

| # | Failure | Detect | Fix |
|---|---|---|---|
| 1 | **Clipped word ends** | `hot_joins` in `qa_cut.py`: speech still loud at the join. A fresh transcript usually hides this, though it sometimes shows it ("dose" becomes "doe") | Cut at the quietest slice, raise the tail, fade inside the padding |
| 2 | **One prompt on long raw footage** | Repeated sentences, wrong order, missing lines in the cut's transcript | Stages: cut, plates, composite. For a short video, film a short script |
| 3 | **Graphics drift out of sync** | A cue's frame differs from its word's frame by over 2 frames, growing toward the end | Look words up. Key to word index. Move everything as a set |
| 4 | **"Passed checks" taken as good** | Checks cannot see this | Sample real frames. A person watches with sound |
| 5 | **Slides and the agent look** | Over 5 text elements; text repeats the spoken sentence; everything arrives at once; same entrance twice running | Keywords only, each on its word, from references, with less motion |
| 6 | **Full renders used for review** | More than one full render before the spoken cut is locked | Rough cut, trims, then one render. Low-res drafts, re-render changed ranges |
| 7 | **Music masks the voice** | Final mix's fresh transcript under 95%; music sections far louder than speech | Duck, keep the bed low, ramp out before end cards. Offer no music |
| 8 | **Too many sound effects** | A whoosh with no visible event; effect louder than speech | Off by default. Each must answer what pacing problem it solves |
| 9 | **The same mistake returns** | A new note matches an old one; rule file unchanged after a review | `rules.md`, read first. Turn numbers into checks |
| 10 | **Approved work changes** | Pixel difference in frozen ranges between renders | Name frozen scenes. Add "what stays" to each note |
| 11 | **Wrong color on log or HDR** | ffprobe `color_transfer` shows HLG or PQ; low-contrast picture; odd skin | HDR: convert first. Log: proper transform first. A person judges skin |
| 12 | **Misheard names, invented facts** | On-screen text not in the script or transcript | Take text from the script. Check names on the web. Show numbers as spoken |
| 13 | **Face covered or cropped out** | Face box meets a caption or graphic box. Eye height jumps between zoom levels | Calibrate crops to a detected face. Graphics on the far side |
| 14 | **Bad joins** | Clicks, a repeated breath. "Sounds wrong" needs a person | 30 ms fades. If it persists, export a timeline and trim by hand |
| 15 | **Removing pauses that matter** | A removed gap right before a number or punchline | List them for review. Keep the beat by rule |
| 16 | **Judder or black video** | Variable or mismatched rate in ffprobe; iPhone MOV black in preview | `fps=N -fps_mode cfr`. Judge the exported file |
| 17 | **Frozen or dead stretches** | Frozen over 0.3 s; over 3 s with nothing moving | Re-cut from source, never hold a frame. Move stills or use a recording |
| 18 | **Hard-coded timings** | Frame literals in components; later scenes break after an early change | One timing file and a cue sheet |
| 19 | **Flash frames** | `qa_cut.py` reports `flash_at`; the join sheet shows the wrong picture | Move the cut. Ours came from a slate, and every audio check passed it |
| 20 | **Unreadable text** | Under 28 px at 1080; a card shorter than its reading time; cue under 0.35 s | Bigger type on vertical, longer holds, safe zones |
| 21 | **Loudness or clipping wrong** | Off target; true peak above -1 dBTP. One first edit peaked at -0.03 dB | Two-pass loudnorm on the final mix, then measure again |
| 22 | **Silent layer and font failures** | Overlay hides captions; rendered font differs | Subtitles last. `document.fonts.check` |
| 23 | **Trusting model judges** | A judge reports a glitch that frames do not show | Hints only. Check every claim against frames |
| 24 | **Private data on screen** | Names, emails, keys, timezone or location in frames | Audit frames before publishing |
| 25 | **Sameness** | Empty style file, no references used | Decide what is different before starting. A person reviews |

Sources for each row are in [sources.md](sources.md).
