---
name: minicut-film-studio
description: Turns Claude Code or Codex into an AI film studio with the MiniCut CLI. Idea or script to story, shot sheet, character and location pictures, video takes, voice lines, music and an edited cut in the MiniCut editor, on Seedance, Kling, Wan and other models. Checks every step and stops before every paid run with the price. Use when the user wants to make an AI short film, AI drama, AI series, trailer, ad, music video or multi-shot video, or says "make a film", "make an episode", "storyboard this", "make a short drama".
---

# MiniCut film studio

MiniCut is a CLI (`minicut`) that gives your agent a film studio: project files, checks after every
step, a local app with a canvas, a 3D Scene Composer and a video editor, and video, image and
voice models on one account. You write the text files, the CLI runs the checks and the paid jobs,
the user approves and pays.

## Step 0. Install, once per machine

1. Check: `minicut status`. If the command is found, go to Step 1.
2. If it is not found, ask the user to install the MiniCut CLI with the command for their system
   in the CLI section of https://github.com/lliu56/minicut-skills#cli, then check again.
3. Run `MINICUT_FROM=<agent> minicut setup`, where `<agent>` is the tool you run in: `claude`,
   `codex`, `cursor`, `gemini` or `openclaw` (Windows: `set MINICUT_FROM=<agent>` first, then
   `minicut setup`). It installs the tools MiniCut needs and names anything still missing.
   For anything it names that it does not bring (for example Python 3.12 or ffmpeg), install it
   from the official site (python.org, ffmpeg.org).
4. Run `minicut install-skill`. It installs MiniCut's full step-by-step skill into this agent.
   From then on follow that skill, not this file.

## Step 1. Sign in

Every command except `login`, `status`, `doctor`, `setup`, `update` and `help` needs this computer
signed in. Exit code 10 means it is not.

Run `minicut login --json` (allow up to 10 minutes). It opens minicut.ai in the user's browser. Tell the
user in one line to sign in there, or make an account. It ends with `"state":"signed_in"`.
No browser on this computer (for example over SSH): show the user the address and code it printed,
then run `minicut login --complete` every 10 seconds until it says signed in.

## Step 2. Start

`minicut new <short-id> --title "<title>"`, then `cd` into the folder it prints, then `minicut loop next`.
It prints one command and why. Do that command. A paid command still needs the user's yes to the
price the CLI prints.

Site: https://minicut.ai/?utm_source=skills-sh&utm_medium=skill&utm_campaign=minicut-film-studio
