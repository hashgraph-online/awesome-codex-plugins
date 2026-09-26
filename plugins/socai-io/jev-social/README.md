<img src="https://raw.githubusercontent.com/socai-io/jev-social/main/docs/banner.png" alt="Jev Social — Jev × socai" width="100%" />

# Jev Social — browser-grounded social research

**Jev is cool. Giving it a bounded view of social evidence is cooler.**

[![GitHub stars](https://img.shields.io/github/stars/socai-io/jev-social?style=flat-square&label=stars)](https://github.com/socai-io/jev-social/stargazers)
[![Skills installs](https://skills.sh/b/socai-io/jev-social)](https://skills.sh/socai-io/jev-social/jev-social)
[![tests](https://github.com/socai-io/jev-social/actions/workflows/test.yml/badge.svg)](https://github.com/socai-io/jev-social/actions/workflows/test.yml)
[![release](https://img.shields.io/github/v/release/socai-io/jev-social?style=flat-square&label=release)](https://github.com/socai-io/jev-social/releases/latest)
[![license](https://img.shields.io/github/license/socai-io/jev-social?style=flat-square&label=license)](LICENSE)

<a href="https://ossdrop.com/tool/jev-social"><img src="https://ossdrop.com/badge/jev-social" alt="#1 Tool of the Day on OSSDrop" width="250" height="56"></a>

Jev chooses each next operation: search, open a particular post or profile, read comments, explicitly requested TikTok media download, or finish. The local `socai CLI` executes the selected command in your real Chrome. Each result goes back to Jev before the next decision.

<p>
  <img src="https://raw.githubusercontent.com/socai-io/jev-social/main/docs/platforms/instagram.png" height="32" alt="Instagram">
  &nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/socai-io/jev-social/main/docs/platforms/tiktok.png" height="32" alt="TikTok">
  &nbsp;&nbsp;
  <img src="https://raw.githubusercontent.com/socai-io/jev-social/main/docs/platforms/linkedin.svg" height="32" alt="LinkedIn">
</p>

[⭐ Star Jev Social](https://github.com/socai-io/jev-social/stargazers) · [Live site](https://socai-io.github.io/jev-social/) · [Social research guide](https://socai-io.github.io/jev-social/social-research/) · [Security and data flow](SECURITY.md) · [Real 64-second Jev report](docs/example-report.md) · [Recorded TikTok video evidence](docs/tiktok-evidence.md) · [Discord](https://discord.gg/CpQdA7bwt8) · [Jev](https://typesafe.ai/)

## Try it

With Node 20+ and Chrome already signed in to Instagram, TikTok, or LinkedIn:

```bash
npx github:socai-io/jev-social#v0.1.8 onboard
npx github:socai-io/jev-social#v0.1.8
```

Onboarding prompts for the OpenRouter key and offers to install the official `socai CLI` when it is missing. The second command opens the loopback-only demo.

![Earlier routing-only demo](https://raw.githubusercontent.com/socai-io/jev-social/main/docs/jev-social.gif)

The recording above shows the earlier routing-only prototype. Current runs include a history of every operation chosen by Jev.

## Why this pairing

Jev chooses from a changing list of concrete, read-only operations. The list includes exact targets discovered in previous results, so Jev decides which post to open and which `socai CLI` operation to run. The local CLI handles the underlying navigation, clicks, scrolling, and extraction; Jev does not choose arbitrary DOM coordinates or generate shell commands.

```text
"find handmade art on Instagram"
        │
        ▼
   Jev chooses the platform
        │
        ▼
   Jev chooses an operation ◄──── observed results
        │                              ▲
        ├─ search                      │
        ├─ open a selected profile     │
        ├─ open a selected post        │
        ├─ read comments / download    │
        │         └──── socai CLI ─────┘
        └─ finish → cards · table · evidence report
```

https://github.com/user-attachments/assets/4849e0f3-87d5-4a0d-8e0b-2a58e3d0267a

This video also predates the per-operation Jev loop.

## Available operations

| Platform | Jev can select |
| --- | --- |
| Instagram | Search, open a profile and its post cards, open a specific post/reel and read comments, inspect page state |
| TikTok | Search, open an author, read a selected video and its comments, download that video's media only when the goal explicitly requests it, inspect page state |
| LinkedIn | Search people/content/companies, read a selected profile/company/post, read experience or education, inspect page state |

Only commands exposed by the installed socai CLI are offered. Targets come from captured results or explicit URLs in the user's request. Unsupported, malformed, and low-confidence decisions do not execute. Previously attempted operations are removed from the next choice set.

The run stores each choice, confidence, command, observed result summary, and elapsed time. Login/access gates, decision failures, and step limits produce partial results rather than a success claim. After collection, Jev Social can use the existing OpenRouter key to synthesize a concise report from a bounded, sanitized evidence payload. Every accepted finding must cite a captured source; foreign URLs, missing citations, raw JSON, and local paths fail validation and fall back to the deterministic evidence report. Report sections stream into the fixed panel while captured cards stay visible, and the downloaded `report.md` is the same Markdown shown in the browser. The synthesizer has no browser or shell tools and does not depend on `socai research`.

The report model defaults to `openai/gpt-4o-mini` and may incur normal provider usage. Set `OPENROUTER_REPORT_MODEL` to another available model, or set it to `off` to keep report generation fully deterministic. Speed varies with the number of chosen operations, the live site, and the selected report model.

## Privacy and local data

- Jev Social does not read or copy the browser cookie store directly. The installed `socai CLI` uses the Chrome profile you selected; use a separate profile or test account for sensitive research.
- OpenRouter is the default decision provider. Decision requests contain the full research goal plus the requested platform, current action labels, source URLs, earlier action summaries, and short visible-text excerpts. The application does not intentionally add cookies, downloaded media, raw CLI JSON, or filesystem fields, but user input and visible social content are untrusted and can themselves contain personal or path-like text. Optional report synthesis receives a separate bounded, sanitized evidence payload; set `OPENROUTER_REPORT_MODEL=off` to disable that second model call. A configured Kev or Simple Jev endpoint keeps decision requests on the explicit loopback server and never receives the OpenRouter key.
- Recoverable checkpoints live under `${JEV_SOCIAL_HOME:-~/.jev-social}`; `socai` stores its own evidence and downloaded media separately. There is no automatic cleanup schedule. Stop the app, inspect the run, and remove only the specific checkpoint or evidence directory you no longer need.
- TikTok media download becomes an available action only when the research goal explicitly requests an offline copy. That intent is retained in the operation history; there is no second confirmation after the explicit request.

The complete field limits, file permissions, provider-retention boundary, browser-session boundary, and recovery procedure are documented in [Security and data flow](SECURITY.md#data-flow-credentials-and-retention).

## Recorded evidence

| Recorded run | Captured result | Elapsed time | Verification boundary |
| --- | --- | ---: | --- |
| [Instagram Jev research loop](docs/example-report.md) | Four captured records after two searches and one post-detail read | 63.969 s | Sanitized public copy; one opened post is separated from three discovery cards |
| [TikTok CLI search](docs/tiktok-evidence.md#search) | Five public TikTok result URLs | 7.570 s | socai CLI timing, not Jev decision-loop timing |
| [TikTok video detail](docs/tiktok-evidence.md#video-detail-and-media-download) | Metadata, a 7,988,959-byte MP4, and a 95,592-byte poster | 38.263 s | Partial run: media succeeded, comments were unavailable |

These are individual local observations, not a benchmark or guaranteed latency. Live-site behavior, network conditions, login state, and the operations Jev selects can change the total time.

## Reproducible benchmark

v0.1.8 includes fixed Instagram, TikTok, and LinkedIn tasks plus a privacy-safe collector and p50/p95 summary generator. Once the runner initializes, every research attempt stays in the dataset, including access gates, interruptions, empty results, and failures. Exact task/environment groups—including the Jev Social runtime—remain `INCOMPLETE` until they contain at least ten distinct runs.

No live benchmark results are published yet. The commands, row contract, timing definitions, and publication gate are documented in [benchmark/README.md](benchmark/README.md).

## Run it

Node 20+, a decision provider (OpenRouter Jev or a loopback Kev server), and a current `socai CLI`.

Fastest OpenRouter path — no repository clone required. Onboarding prompts for the key and offers to install the official socai CLI when it is missing:

```bash
npx github:socai-io/jev-social#v0.1.8 onboard
npx github:socai-io/jev-social#v0.1.8
```

To let Codex invoke the same browser-grounded workflow through GitHub CLI 2.101 or newer:

```bash
gh skill install socai-io/jev-social jev-social@v0.1.8 --agent codex --scope user
```

Or install it from the [skills.sh directory](https://skills.sh/socai-io/jev-social/jev-social) with the cross-agent Skills CLI:

```bash
npx skills add https://github.com/socai-io/jev-social/tree/v0.1.8/skills/jev-social --skill jev-social
```

For OpenCode, install the tested v0.1.8 skill into its natively discovered project skill directory:

```bash
npx skills add https://github.com/socai-io/jev-social/tree/v0.1.8/skills/jev-social --agent opencode
```

For OpenClaw, install the v0.1.8 skill from its immutable release commit into the current workspace:

```bash
npx skills add https://github.com/socai-io/jev-social/tree/c411ae1532dd37ab94f8164f13552ed05f4c9ecc/skills/jev-social --skill jev-social --agent openclaw --copy
```

The skill pins the documented Jev Social CLI release, preserves its read-only and login-gate boundaries, and returns source-linked evidence instead of raw run JSON. Platform availability is checked against the installed socai CLI before a run.

To work from a source checkout instead:

On macOS and Windows, onboarding can install a missing `socai CLI`. On Linux, install a current `socai CLI` separately, then put it on `PATH` or set `SOCAI_BIN` before onboarding.

```bash
git clone https://github.com/socai-io/jev-social.git
cd jev-social
npm install
npm start -- onboard
npm start
```

To run v0.1.8 through local [Kev](https://github.com/jaredpalmer/kev), start its TypeSafe-compatible server on loopback, then launch the tagged Jev Social release without an OpenRouter key:

```bash
# Terminal 1
git clone https://github.com/jaredpalmer/kev.git
cd kev
git checkout 2855ba2a55a80579176a459f78b95d03548cabb5
uv sync --extra serve
uv run --extra serve python -m kev.serve --run jaredpalmer/kev-4b@139fdd94f1b6a6ad80cc15e08fcb99cac885a101 --port 8009

# Terminal 2
export JEV_SOCIAL_SYSTEM_ONE_URL=http://127.0.0.1:8009/v1/systemone
export JEV_SOCIAL_SYSTEM_ONE_MODEL=kev-latest
export JEV_SOCIAL_SYSTEM_ONE_TIMEOUT_MS=120000
export OPENROUTER_REPORT_MODEL=off
npx github:socai-io/jev-social#v0.1.8
```

The local endpoint must be plain HTTP on `localhost`, `127.0.0.1`, or `::1`, with the exact `/v1/systemone` path. Jev Social does not send the OpenRouter key to it, rejects redirects and oversized responses, and keeps the same typed choice validation. Local inference allows up to 120 seconds by default; lower it with `JEV_SOCIAL_SYSTEM_ONE_TIMEOUT_MS`. `OPENROUTER_REPORT_MODEL=off` uses the deterministic source-linked report; the browser and social-platform traffic still runs through local `socai` and Chrome.

[Simple Jev](https://github.com/featherless-ai/simple-jev) is also compatible when it is self-hosted on loopback with a Choice-capable model. The [tested setup and compatibility matrix](docs/simple-jev.md) pin the evaluated Jev Social release, Simple Jev source, and model revision; the recorded decision timings are not browser-speed claims.

Opens `http://127.0.0.1:8766`. Loopback only. Leave the platform on **Jev · auto**, type a goal, watch the timer.

```bash
npm start -- search "find emerging design creators on Instagram" --platform auto --limit 4
npm start -- search "find AI wearable trends on TikTok" --platform auto --limit 4
npm start -- search "find AI product managers in San Francisco on LinkedIn" --platform auto --limit 4
npm start -- search "find handmade art on Instagram and read the comments" --limit 4 --max-steps 12
```

`--limit` is the target result count and per-search/profile collection size (1–100). All captured records are retained, including intermediate profile cards. `--max-steps` bounds the decision loop (1–30, default 12); each selected operation or finish decision consumes one step. The HTTP search endpoints also accept `maxSteps`.

For browser connection checks, platform login barriers, and safe status diagnostics, see [Troubleshooting](https://github.com/socai-io/jev-social/blob/main/docs/troubleshooting.md).

---

If this is useful, [star Jev Social](https://github.com/socai-io/jev-social/stargazers) or [join the Discord](https://discord.gg/CpQdA7bwt8).
