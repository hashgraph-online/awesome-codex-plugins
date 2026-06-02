---
name: captcha-auto-skill
description: Generate captcha candidate answers with a local OCR first strategy, then use DashScope by default while keeping ModelScope as an explicit manual override and sending only the cropped captcha image for remote inference.
---

# Captcha Auto Skill

Use `scripts/run.mjs` when you need captcha auxiliary recognition.

## Workflow

1. Install the bundle into a project and run `npm install` once inside the installed skill directory.
2. Put provider secrets in the target project's `.env.local`, not in the skill directory.
3. Preferred path: generate a candidate answer from a local captcha image with `node .codex/skills/captcha-auto-skill/scripts/run.mjs --input="<captcha-image>"`.
4. Optional page-assist path: inspect a captcha on a live page with `node .codex/skills/captcha-auto-skill/scripts/run.mjs --url="<url>"`.
5. Optional browser actions stay opt-in. Add `--apply-page-actions` only when you want the runtime to fill the detected input and click a nearby submit control.
6. The runtime captures only the cropped captcha region for remote inference.
7. Routing policy:
   - `free-first`: local OCR -> DashScope
   - `paid-latest`: local OCR -> DashScope `qwen3.6-plus`
   - `ModelScope`: manual override only; use `--provider=modelscope` when you explicitly want it
8. Remote model catalogs are cached under the current project's `.codex/cache/captcha-auto-skill/catalogs/`.
9. Use `--refresh-catalog` to bypass the cached catalog, and adjust `CAPTCHA_CATALOG_TTL_SECONDS` when you want a different cache lifetime.

## Required Configuration

- Secrets must come from the current shell or the project-local `.env.local`.
- Supported keys:
  - `CAPTCHA_MODELSCOPE_API_KEY`
  - `CAPTCHA_DASHSCOPE_API_KEY`
  - `CAPTCHA_MODELSCOPE_BASE_URL`
  - `CAPTCHA_DASHSCOPE_BASE_URL`
  - `CAPTCHA_DEFAULT_PROFILE`
  - `CAPTCHA_CATALOG_TTL_SECONDS`

## Guardrails

- `--api-key` is disabled. Do not pass secrets on the command line.
- Keep local OCR as the first attempt before cloud inference.
- Do not read or write `~/.openclaw/openclaw.json`.
- Do not upload a full-page screenshot unless `--debug-screenshots` is enabled.
- These ModelScope models are denylisted and must not be used:
  - `Qwen/Qwen3-VL-8B-Instruct`
  - `Qwen/Qwen3-VL-235B-A22B-Instruct`
- Specialized OCR models such as `Qianfan-OCR` are future work and are not part of v1 routing.

## Notes

- `Qwen/Qwen3.5-397B-A17B` remains a valid manual ModelScope override when passed with `--provider=modelscope`.
- `qwen3.6-plus` is the default DashScope flagship model for `paid-latest`.
- The published bundle is self-contained under `skills/captcha-auto-skill/` and does not rely on repository-root source files after installation.
