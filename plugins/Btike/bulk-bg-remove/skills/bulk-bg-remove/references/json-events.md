# `--json` events

With `--json`, `bulk-bg-remove` prints one JSON object per line on stdout and
nothing else. stderr may carry warnings; judge a run by its exit code and the
`finished` event. Every event has `type` and `at` (Unix time, seconds). Fields are
only ever added, never renamed or removed.

## Order

```
scan → plan → [sample_sheet] → [model_download → model_ready] → worker_loading → worker_ready
     → job_started → job_stage… → job_done | job_failed   (per image)
     → verify_started → [review_sheets] → finished
```

`--dry-run` stops after `plan`. `paused`/`resumed` can appear at any time
during the run. `error` or `interrupted` end the stream early.

## Events

| type | fields |
|---|---|
| `scan` | `hardware` {`platform`, `cpu_name`, `cpu_logical`, `cpu_performance`, `ram_total_gb`, `ram_available_gb`, `device`} · `inventory` {`input`, `images`, `total_mb`, `max_megapixels`, `formats` {format: count}, `skipped` [{`path`, `reason`}]: files that are not supported images, hidden image files (`hidden file`), earlier output folders (`earlier output folder (-no-bg)`) and, with `--max-megapixels`, larger photos (`larger than --max-megapixels N (M MP): run it on its own`)} · `output` |
| `sample_sheet` | `path` (a PNG in a temporary folder), `images` [file names]: only with `--sample-sheet` |
| `plan` | `images`, `mode` (`queue`/`parallel`), `workers`, `threads_per_worker`, `binding_limit` (`RAM`/`CPU`), `ram_per_worker_gb`, `min_free_ram_gb`, `pause_below_gb`, `estimated_output_gb`, `free_disk_gb`, `eta_seconds`, `blockers` [str], `warnings` [str], `model` (the model that will run), `model_choice` (null unless `--model auto`: {`profile`, `model`, `score`, `best_model`, `best_score`, `best_needs_gb`, `needs_gb`, `fits`, `gap`}, scores 0-10 from the bench), `edges` (`matte`/`clean`/`mask`), `output_format` (`png`/`webp`/`jpg`), `finish` (null, or {`background` (`#RRGGBB` or null), `square`, `pad` (% per side), `size` (px or null)} with `--shop`, `--background`, `--square`, `--pad` or `--size`), `already_done` |
| `model_download` | `model` (first run only: weights are being downloaded) |
| `model_ready` | `model` |
| `worker_loading` / `worker_ready` | `worker`. They can repeat mid-run for the same `worker`: when free RAM runs low, a worker whose memory grew is restarted (~2 s). Normal, not a crash |
| `worker_failed` | `worker`, `reason` |
| `job_started` | `job`, `worker`, `source`, `destination` |
| `job_stage` | `job`, `worker`, `stage` (`loading`, `removing`, `refining`, `compositing`, `saving`), `progress` (percent, 0–100, reached as the stage starts) |
| `job_done` | `job`, `worker`, `width`, `height`, `seconds`, `note` (null or a short remark, `; `-separated: `edge matting skipped: …`, `edge matting at N MP to fit free RAM`, `upscaled ×N from a small original (N px)`, and with any finishing also `empty cut-out: no subject detected` or `nothing removed: background kept`, which verify cannot see on a finished output), `source`, `done`, `total` (images finished so far, done or failed, out of the run's total), `certified` (with `--review-sheets`: `true` when the chroma-key check passed and the cut-out needs no review, `false` when it does, `null` when not checked), `check` (why: `certified`, `background is not plain`, `subject too close to the background colour`, `something unlike the background was removed`, `half-transparent areas away from the edge`, `background colour left on the edge`, `background colour kept inside the cut-out`, `the model is unsure (mirrored photo differs)`, `no subject found`, `nothing was removed`, `check could not run (…)`) |
| `job_failed` | `job`, `worker`, `reason`, `source`, `done`, `total` |
| `job_skipped` | `source`, `reason` (`already done`) |
| `paused` | `free_ram_gb`, `needed_gb`: free RAM dropped below the reserve, new images wait (if nothing frees up, pending images fail with `not enough free RAM (pause timed out)`) |
| `resumed` | `free_ram_gb` |
| `verify_started` | `outputs` |
| `review_sheets` | `sheets` [{`path`, `images` [{`n`, `label`, `source`, `output`, `zoom`, `audit`}]}]: only with `--review-sheets`, and only when this run produced cut-outs. PNGs in a temporary folder, 12 per sheet; `n` counts from 1 in each run, `label` is the output path relative to the output folder (stable across runs); `zoom` is a JPEG close-up of the cut-out on black and on white (judge from it, not from the PNG: viewers often drop transparency); `audit` (`true`: certified, sheeted as a spot check). Top level: `certified` (all cut-outs the check certified) and `audit` (how many of those are on the sheets as audits; the rest are left off). Without `--review-all`, only cut-outs that need review are sheeted |
| `finished` | `output`, `images`, `processed`, `already_done`, `failed` [{`path`, `reason`}], `not_processed` [{`path`, `reason`}], `warnings` [{`path`, `warning`}], `seconds`, `certified` (cut-outs the chroma-key check certified, or null when it did not run) |
| `error` | `message` (the run stopped) |
| `interrupted` | (Ctrl+C) |

## `doctor --json`

A single object, not a stream (abridged):

```json
{
  "version": "0.1.3",
  "hardware": {"ram_total_gb": 34.4, "ram_available_gb": 22.0, "device": "cpu", "...": "..."},
  "model": "birefnet-general-lite",
  "model_path": "/Users/me/.u2net/birefnet-general-lite.onnx",
  "model_peak_ram_gb": 9.4,
  "min_free_ram_gb": 12.1,
  "checks": {"heic": true, "avif": true, "webp": true,
             "model_downloaded": true, "enough_free_ram": true},
  "ready": true,
  "auto": {"uniform": {"model": "birefnet-general-lite", "score": 8.6, "gap": 0.0, "...": "..."},
           "complex": {"model": "birefnet-general", "score": 7.6, "gap": 0.0, "...": "..."}},
  "models": [{"name": "silueta", "min_free_ram_gb": 3.4, "fits": true}]
}
```

`model` is what `auto` would use for product photos right now (or the model
passed with `--model`). `auto` has the pick for every profile, for a 12 MP
photo: `fits: false` means no model fits (the run would be blocked for RAM);
`fits: true` with a `gap` above 0.5 means a run with that profile would stop
and ask (`--allow-fallback`).
`ready` ignores `model_downloaded` (models download on first run). Exit code
`2` when not ready.
