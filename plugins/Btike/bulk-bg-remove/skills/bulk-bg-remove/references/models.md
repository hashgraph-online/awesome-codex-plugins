# Choosing a model

You rarely need to pick by hand: `--model auto --profile <kind>` (the default
model is `auto`) takes the best-scoring model for that kind of image that fits
in free RAM, and stops to ask when the only model that fits is more than half
a point worse (`--allow-fallback` accepts it). The profiles group the image
types below: `uniform` (products, white-on-white, labels, reflective, several
objects), `complex` (hair, fur, plants, thin parts), `people`, `scene`
(cluttered), `drawing`. Use this page for special cases and to explain a choice.


Measured on 69 distinct test images across 11 models (80 images judged; the
format folder re-encodes one product photo 11 times, so it counts once in the
means below). Each output was scored 0-10 by one blind visual judge at zoom.
Speed and RAM come from one worker on an Apple M5 CPU with edge matting on.
The per-type table below is for picking by hand: there, models within 0.5 points
count as a tie and the faster, lighter model wins. `auto` is stricter: it takes
the profile's top score and uses a lighter model only on an exact tie or when
the best one does not fit (and asks when that costs more than 0.5 points).

## Pick by image type

| Image type | Use `--model` | Runner-up | Why (mean score, n images) |
|---|---|---|---|
| Product on a plain or white background (catalogue) | `birefnet-general-lite` | `birefnet-massive` | 8.6 vs 8.5 on 35 real product catalogue photos; lite never scored 3 or less on them. `birefnet-general` 8.4 and 1.75x slower |
| White object on white | `birefnet-general-lite` | `birefnet-general` | 8.4 vs 8.0 (n=24) |
| Labels, printed text, flat logos | `birefnet-general-lite` | `birefnet-massive` | text 9.0 vs 8.5 (n=11); logos 9.5 vs 8.5 for `birefnet-dis` (n=2) |
| Chrome, gloss, reflective | `birefnet-general-lite` | `birefnet-general` | 8.6 vs 8.4 (n=5): tie |
| Dark on dark | `birefnet-general-lite` | `birefnet-general` | 7.7 vs 7.7 (n=3): tie |
| Thin parts (handles, poles, wires, loops) | `birefnet-general-lite` | `birefnet-general` | 7.6 vs 7.7 (n=22): tie. U2Net family 5.0-5.2 |
| Several objects on a clean background | `birefnet-general-lite` | `birefnet-general` | 7.1 vs 7.4 (n=12): tie |
| Hair or fur (people or animals) | `birefnet-general` | `birefnet-hrsod` | 7.5 vs 7.2; lite 6.6 (n=8) |
| People (portraits, groups) | `birefnet-general` | `birefnet-dis` | 7.7 vs 7.4; lite 7.1, `birefnet-portrait` 7.1 (n=7) |
| Long-haired pets | `birefnet-general` | `birefnet-hrsod` / `birefnet-portrait` | hrsod 7.8, portrait 7.6, general 7.3 (n=4): tie. Only portrait cut out the long-haired cat (9 vs 7 or less) |
| Plants, foliage, seed heads | `birefnet-general` | `birefnet-general-lite` | 7.7 vs 7.0 (n=3) |
| Busy or cluttered background | `birefnet-general` | `birefnet-hrsod` | 6.3 vs 5.7; lite 5.2 (n=6) |
| Clear glass or plastic | `birefnet-general-lite` | `birefnet-general` | 7.3 vs 7.4 (n=8): tie. No model keeps glass see-through, so the old background stays baked in |
| Small or low-res (under ~500 px) | `birefnet-general-lite` | `silueta` | 7.7 vs 7.7 (n=3): tie. Use silueta only when RAM is tight |
| Very large (45 MP) | `birefnet-general-lite` | any BiRefNet | 9 for all five BiRefNet general/dis/massive/hrsod (n=1) |
| Cartoon or anime drawing | `isnet-anime` | `birefnet-general-lite` | 9 vs 8 (n=1). Use it for drawn art only |
| No clear subject (landscape, shelf) | ask the user | `birefnet-general` | best mean 5.3 (n=3). Ask what to keep or crop first |

## All models

The 01-05 columns are the folder means: 01 edges (n=10), 02 materials (n=8),
03 composition (n=9), 04 formats (n=7, deduped) and 05 real catalogue photos (n=35).
"≤3" counts the images scored 3 or less out of 69 (an unusable result).
Times are seconds per image and peaks are GB, given as catalogue photos / worst
folder.

| Model | Mean | 01 | 02 | 03 | 04 | 05 | ≤3 | s/img | Peak RAM | Licence |
|---|---|---|---|---|---|---|---|---|---|---|
| birefnet-general | 7.9 | 7.0 | 7.8 | 6.8 | 8.3 | 8.4 | 1 | 5.6 / 9.6 | 12.3 / 17.5 | MIT |
| **birefnet-general-lite** (default) | 7.8 | 6.2 | 7.6 | 6.6 | 8.2 | 8.6 | 2 | 3.2 / 6.5 | 10.3 / 15.7 | MIT |
| birefnet-hrsod | 7.6 | 6.4 | 7.4 | 6.6 | 7.6 | 8.3 | 3 | 5.6 / 9.7 | 12.5 / 16.9 | MIT |
| birefnet-massive | 7.5 | 5.3 | 7.0 | 6.0 | 8.1 | 8.5 | 4 | 5.6 / 9.0 | 12.4 / 17.7 | MIT |
| birefnet-dis | 7.4 | 5.5 | 7.3 | 5.7 | 7.8 | 8.4 | 4 | 5.5 / 7.9 | 12.4 / 17.9 | MIT |
| isnet-general-use | 6.4 | 5.2 | 5.4 | 3.6 | 7.1 | 7.6 | 11 | 1.3 / 14.3 | 4.1 / 10.3 | Apache-2.0 |
| silueta | 6.3 | 4.5 | 5.1 | 4.1 | 6.7 | 7.5 | 11 | 0.4 / 6.1 | 2.2 / 9.6 | Apache-2.0 |
| u2net | 6.3 | 4.4 | 5.6 | 4.2 | 6.7 | 7.3 | 8 | 0.5 / 3.3 | 3.2 / 9.5 | Apache-2.0 |
| birefnet-portrait | 6.2 | 5.6 | 3.5 | 4.0 | 7.3 | 7.4 | 15 | 5.5 / 14.4 | 12.4 / 18.5 | MIT |
| u2net_human_seg | 4.0 | 3.3 | 2.8 | 3.1 | 4.9 | 4.5 | 37 | 0.8 / 3.8 | 3.6 / 8.2 | Apache-2.0 |
| isnet-anime | 2.3 | 0.5 | 2.0 | 2.2 | 1.4 | 3.1 | 54 | 1.2 / 4.0 | 4.0 / 7.0 | Apache-2.0 |

All 11 models processed all 82 bench files with no failures: HEIC, AVIF, WebP,
TIFF, BMP, CMYK, 16-bit grayscale, palette PNG, an ICC profile, EXIF rotation,
a wrong extension, existing alpha, 180 px and 45 MP.

## RAM and the free-RAM gate

- The BiRefNet models peak at about 10-12.5 GB on catalogue-size photos. The
  U2Net and IS-Net models peak at 2-4 GB.
- On the hair, fur and thin-structure photos (4-5 MP) every model peaked 5-6 GB
  higher, with lite reaching 15.7 GB and general 17.5 GB. The 45 MP photo did
  not cause that jump, so photo size alone does not predict the peak. When free
  RAM is tight on photos like these, use `--fast-edges`, which skips edge matting.
- The dry-run `plan` reports `min_free_ram_gb` for the model `auto` picked.
  Never lower `--min-free-ram` to force a start. With `auto`, a RAM blocker
  means even the lightest model for that profile does not fit: free RAM or use
  another machine. A blocker mentioning `--allow-fallback` means a lighter,
  clearly worse model fits: ask the user before adding it.

## Models to avoid

- `isnet-anime`: it was trained on drawings. On 54 of 69 photos it returned a
  near-empty ghost; it won only the cartoon.
- `u2net_human_seg`: it segments people only. On product photos it removed or
  fragmented the subject (3 or less on 19 of 35 catalogue photos).
- `birefnet-portrait` for non-people: it returned empty or near-empty on a
  hydrant, a truck and a logo (0), and it punched holes in white label
  areas. Keep it for long-haired pets or a person in a crowd.
- `u2net` and `silueta` when thin parts or gaps matter: they keep the
  background inside loops and handle holes, and they drop branches and poles
  (plant 2 vs 8, cable loops 3 vs 9).

## Mixed folders: decide quickly

1. Default to `birefnet-general-lite`. It is within 0.1 of the best mean
   overall, the fastest BiRefNet and the lightest, and it scored best on
   real product catalogue photos.
2. Switch the whole batch to `birefnet-general` when most images are people,
   hair or fur, plants or cluttered scenes. On those it leads by 0.7-1.2
   points at 1.75x the time and about +2 GB RAM.
3. Otherwise run lite, then re-run only the weak images with a better model
   using `--model birefnet-general --force`. Flag these:
   - images with the warning `edge matting skipped: Trimap did not contain
     foreground values`. In this bench, 79 of 80 judged outputs with that
     warning scored 3 or less (empty or ghost).
   - people and pets with loose hair, and scenes with no single subject.
4. If an image has no clear subject or is clear glass on a coloured background,
   ask the user rather than trying more models.
