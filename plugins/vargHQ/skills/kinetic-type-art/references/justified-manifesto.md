# Justified manifesto column

A manifesto or mission statement set word by word into one justified column, with photos opening in the gaps between paragraphs. For brand films, founder letters, launch statements. Variants: dark, light. 16:9, 9:16, 1:1; 12-20 s.

## How the pros do it
- Justify only with hyphenation on; otherwise you get large holes between words. When space must be added, add it between words, never between letters [23].
- Fix the measure (column width) first and let the text flow into it word by word; the column edge is the design [25].
- Pace to reading speed: adults read about 20 characters/s [37]; one word per beat at 100-140 BPM keeps the statement readable.
- Lay the column on a grid with an asymmetric position (left third or right third in 16:9) [25].
- Measure word widths up front (userland measurement, no reflow per frame) so you can compute final justified positions and animate each word straight into its slot [9].
- Grotesque or editorial serif, never both in the body; one accent word per paragraph may switch face.
- A photo opens inside the column (a gap widens between two lines), not on top of the text.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `justified-manifesto.dark` | White Inter on near-black, red accent word | bg #0B0B0D, ink #F2EFE8, accent #FF5A1F, Inter 600, 64 px at 1080p, leading 1.05 |
| `justified-manifesto.light` | Black serif on paper | bg #F2EFE8, ink #111111, Instrument Serif 400, 72 px, leading 1.0, accent italic |
| `justified-manifesto.caps` | Condensed caps block, poster feel | Anton or League Gothic caps 96 px, +0.04em tracking, leading 0.92 |

## Timing and numbers
- Words per beat: 1 (default). At 120 BPM a 30-word manifesto takes 15 s. Allow bursts of 2 words/beat for short function words ("of the", "and we").
- Word entrance: hard cut-in (0 f) or 4-6 f rise of 0.15em with `power3.out`. Justification reflow when a new word joins a line: existing words slide 6-8 f `power2.out`.
- Photo gap: the lines above and below part by 30-45% of frame height over 10-14 f (`power3.inOut`), photo holds 1-2 beats, gap closes 8-10 f.
- Column at 1920x1080: 720-880 px wide (5-7 grid columns), 96 px margin; 1080x1920: 936 px wide (full minus 72 px sides), safe top 220 px, bottom 380 px; 1080x1080: 860 px.
- Measure: 25-40 characters per line at display sizes; fewer than 20 per line makes justification gaps unavoidable.
- End: hold the full column 1.5-2 s, then a hard cut to the signature or logo.

## Build it
1. Lay out the whole text once off-screen with hyphenation (`hyphens: auto`, `lang` set) and `text-align: justify`; record each word's final x, y, width (or use a measurer [9]).
2. Insert soft hyphens before measuring so the layout is stable; snapshot positions.
3. On the timeline, reveal word i at beat i (computed from absolute time [38]); place it at its final justified position, or animate earlier words on the current line toward their final spacing.
4. For photo gaps, translate the line groups above and below; the photo sits in a clipped rect between them.
5. HyperFrames: `per-word-rise` or `kinetic-center-build` for the per-word mechanics; `mk-emphasis-type` for an oversized background word [41].

## Mistakes that look amateur
- Justified without hyphenation → rivers and holes [23].
- Letter-spacing used to fill lines → space words, not letters [23].
- Lines re-justify every frame with jitter → compute final layout once, then animate to it.
- Two-word-per-beat for the whole piece → too fast to read [37].
- Photo dropped over text → open a gap inside the column.
- Centered column → loses the editorial feel; offset it on the grid [25].

## Sources
[9] @_chenglou, text measurement — https://x.com/_chenglou/status/2037713766205608234
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html — caps tracking for the caps variant
[23] Butterick, Justified text — https://practicaltypography.com/justified-text.html — hyphenation, word spacing
[25] PRINT, Swiss Style — https://www.printmag.com/?p=1387 — grid, asymmetry
[37] Netflix Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide — 20 cps
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — per-word-rise, kinetic-center-build, mk-emphasis-type
