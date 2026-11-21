---
name: imagera-media
description: "Create or edit images, video clips, voiceovers and music with Imagera and save them into the project. Use when the user asks for a picture, illustration, hero image, product shot, logo concept, thumbnail, social image, short video, animated image, voiceover or background music for their app, website, docs or content."
---

# Imagera media

Make the media this project needs through the Imagera MCP server (`https://mcp.imagera.ai/mcp`), on the user's own Imagera account.

## Steps

1. Work out what the project needs: subject, size or aspect ratio (match where it will be used), style that fits the existing design, and how many.
2. Call `check_credits`, then `estimate_cost` for the planned calls. Tell the user the credit cost and wait for a yes before anything that spends credits.
3. Generate: `generate_image` for new pictures, `edit_image` to change one they have, `generate_video` or `animate_image` for clips, `generate_voice` for narration, `generate_music` for a track.
4. Long jobs return an id: poll `check_job` until it is done.
5. Download each result into the project's existing asset folder with a descriptive file name, reference it from the code, and give every image meaningful alt text.
6. Show the user what was made and where it was saved. Offer one revision round rather than regenerating unasked.

## Rules

- Quote before spending; never loop retries that spend credits.
- Keep prompts about the subject, not about the tool.
- Respect the project's licence notes and never put real people's likeness into an image without their permission.

## Tools

| Tool | What it does | Cost |
|---|---|---|
| `check_credits` | Check credits | free read |
| `estimate_cost` | Estimate cost | free read |
| `check_job` | Check job | free read |
| `list_skills` | List skills | free read |
| `check_skill_run` | Check skill run | free read |
| `list_identities` | List saved IDs | free read |
| `generate_image` | Generate image | spends credits |
| `edit_image` | Edit image | spends credits |
| `upscale_image` | Upscale image | spends credits |
| `detect_ai` | Detect AI image | spends credits |
| `generate_video` | Generate video | spends credits |
| `animate_image` | Animate image | spends credits |
| `enhance_video` | Enhance video | spends credits |
| `generate_3d_model` | Generate 3D model | spends credits |
| `generate_auto` | Imagera Auto | spends credits |
| `generate_voice` | Generate voice | spends credits |
| `clone_voice` | Clone voice | spends credits |
| `generate_music` | Generate music | spends credits |
| `chat_with_model` | Chat with model | spends credits |
| `compare_models` | Compare models | spends credits |
| `run_skill` | Run skill | spends credits |
| `save_identity` | Save ID | spends credits |
| `research_brand` | Research brand | spends credits |

Access: the Imagera MCP server is part of the Pro plan; sign in with your Imagera account when the agent asks.
