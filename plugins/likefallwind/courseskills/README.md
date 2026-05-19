# courseskills

Course creation skills for **Codex** and **Claude Code**. This repository packages the same workflows as both clients' plugin formats and as standalone Claude Code skills.

| Skill | What it does |
|---|---|
| **ai-tutorials** | Design AI course syllabi, lectures, and hands-on projects |
| **codex2course** | Topic / outline -> handout -> Imagegen slide images -> PDF |
| **api2course** | Topic / outline -> handout -> OpenAI API slide images -> PDF |
| **pdf2video** | Slide deck -> per-slide narration -> TTS audio -> mp4 |
| **movecourse** | Copy generated lesson mp4 files into the aistudy101 website `course-assets` tree |

The repository is intentionally laid out around one shared `skills/` directory:

- Claude Code can install the skills directly.
- Claude Code can also install this repo as a plugin through `.claude-plugin/marketplace.json`.
- Codex can install it from the Codex marketplace manifest at `.agents/plugins/marketplace.json`, which points back to `.codex-plugin/plugin.json`.

---

## Install

### Skills(Easy)

Requires [Node.js](https://nodejs.org/). Restart Claude Code after installing.

```bash
npx skills add likefallwind/courseskills
```

Install one skill only:

```bash
npx skills add likefallwind/courseskills --skill ai-tutorials
npx skills add likefallwind/courseskills --skill codex2course
npx skills add likefallwind/courseskills --skill api2course
npx skills add likefallwind/courseskills --skill pdf2video
npx skills add likefallwind/courseskills --skill movecourse
```

### Claude Code plugin

Use this if you want plugin-style namespacing and marketplace updates:

```text
/plugin marketplace add likefallwind/courseskills
/plugin install courseskills@courseskills
```

Installed plugin skills are namespaced:

```text
/courseskills:ai-tutorials
/courseskills:codex2course
/courseskills:api2course
/courseskills:pdf2video
/courseskills:movecourse
```

For local plugin development or testing:

```bash
claude --plugin-dir /path/to/courseskills
```

### Codex plugin

Codex installs this repository through its marketplace system.

For Codex App on Windows, use **Add marketplace** with:

```text
Source: https://github.com/likefallwind/courseskills.git
Git ref: main
Sparse paths: .agents/plugins
```

For Codex CLI:

```bash
codex plugin marketplace remove courseskills || true
codex plugin marketplace add \
  'https://github.com/likefallwind/courseskills.git' \
  --ref main \
  --sparse .agents/plugins

codex plugin list --source courseskills
codex plugin install courseskills --source courseskills
```

On Windows PowerShell, use `codex.cmd` instead of `codex` if PowerShell blocks `.ps1` scripts.

For detailed Codex App, Windows CLI, WSL, Linux, and macOS setup notes, see [docs/codex-install.md](docs/codex-install.md).

---

## Prerequisites

### codex2course

- Codex or Claude Code with the `imagegen` skill/tool available for slide image generation.
- Python 3 + [Pillow](https://pillow.readthedocs.io/) for PDF assembly:

  ```bash
  pip install Pillow
  ```

### api2course

- `OPENAI_API_KEY` set in the environment. The image script uses `gpt-image-2`.
- Python 3. The OpenAI image script uses only the standard library.
- Python 3 + [Pillow](https://pillow.readthedocs.io/) for PDF assembly:

  ```bash
  export OPENAI_API_KEY=your_key_here
  pip install Pillow
  ```

### pdf2video

- A completed slide deck from `codex2course` or `api2course`.
- [ffmpeg](https://ffmpeg.org/) on `PATH` for video assembly.
- TTS provider:
  - `edge`: free Microsoft Edge read-aloud voices via `edge-tts`.
  - `minimax`: paid API route. Requires `MINIMAX_API_KEY` and Python `requests`.

  ```bash
  pip install edge-tts requests
  export MINIMAX_API_KEY=your_key_here
  ```

### movecourse

- An AI-generated course directory containing `lessonN/*.mp4` files.
- The aistudy101 website checkout at `/home/likefallwind/code/aistudy101-website`.

---

## Shared workflows

Both Codex and Claude Code use the same skills and output layout. The skills are incremental: they inspect what already exists and continue from the next missing stage instead of redoing approved work.

```text
# ai-tutorials
Design a 10-lesson LLM application development course for CS undergrads.

# codex2course
Create a 6-hour Python async course for backend engineers.

# api2course
Use api2course to create a 6-hour Python async course with OpenAI API generated slides.

# pdf2video
Turn the course in ./course/ into a narrated lecture video, voice: zh-CN-YunxiNeural.

# Full course asset flow
Design a Vibe Coding course, build slides, then produce a narrated mp4.

# Publish generated videos only
Move only this generated course's videos to aistudy101 course-assets as ai-enlightenment.
```

---

## Output layout

```text
course/
├── outline.md          # Course info + image-generation settings
├── handout.md          # Full teaching notes
├── slide-units/        # Per-slide content derived from handout.md
├── slides/             # Rendered .png pages: 000-cover ... zzz-ending
├── course-deck.pdf     # Assembled slide deck
├── audio.md            # TTS voice / padding settings
├── narration/          # Per-slide spoken text
├── audio/              # Per-slide .mp3 files
└── course-video.mp4    # Final narrated lecture video
```

---

## Scripts

Several skills ship helper scripts used internally. You can also run them directly:

| Script | Purpose |
|---|---|
| `skills/codex2course/scripts/split_handout.py` | Slice `handout.md` into `slide-units/` |
| `skills/codex2course/scripts/images2pdf.py` | Combine `slides/*.png` into a PDF |
| `skills/api2course/scripts/generate_openai_image.py` | Generate one slide image with the OpenAI Image API |
| `skills/api2course/scripts/split_handout.py` | Slice `handout.md` into `slide-units/` |
| `skills/api2course/scripts/images2pdf.py` | Combine `slides/*.png` into a PDF |
| `skills/pdf2video/scripts/synth_audio.py` | Synthesize narration audio |
| `skills/pdf2video/scripts/assemble_video.py` | Pair slides + audio into `course-video.mp4` |
| `skills/movecourse/scripts/movecourse.py` | Copy or move `lessonN/*.mp4` into website course-assets |

```bash
python skills/codex2course/scripts/split_handout.py course/handout.md
python skills/codex2course/scripts/images2pdf.py course/slides course/course-deck.pdf
python skills/api2course/scripts/generate_openai_image.py --prompt-file course/prompt.txt --out course/slides/001.png
python skills/pdf2video/scripts/synth_audio.py course/
python skills/pdf2video/scripts/assemble_video.py course/
python skills/movecourse/scripts/movecourse.py --course ai-enlightenment --source course/ --dry-run
```
