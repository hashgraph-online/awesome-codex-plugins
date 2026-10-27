# Production translation and visual repair

For delivery, append the [output-stage audit](final-audit.md). The original
translation/BabelDOC/economical vision/repair/recheck chain remains intact.
The added stage reads actual final mono/dual PDFs and source in fresh contexts,
not earlier pass markers. `best.*` alone is a review candidate. The CLI exits
successfully for a dry plan or `delivery_allowed=true` only. Current real audit
capability is unvalidated, so a model clear reply cannot grant acceptance.

Configure two roles independently: (1) economical translation, such as Luna or a
running local text model; (2) an economical vision-capable model for rendered-page
inspection, eligible text replacement and recheck. The program does not pick,
upgrade or fall back to another model. The model name does not prove vision support.

Copy `assets/pipeline.example.json` and its translation job beside your input.
Set the two actual models, fresh output folders and budgets. Paths are relative
to their own JSON files. The starter pipeline reviews page1; remove `pages` for
all pages after budgeting one image probe plus at least one call per page.

```sh
python scripts/pdf_pipeline.py pipeline.json --engine babeldoc --final-audit-config assets/final-audit.example.json
python scripts/pdf_pipeline.py pipeline.json --engine babeldoc --final-audit-config assets/final-audit.example.json --execute
```

The dry run validates both providers, page scope, mono output and engine flags
without inference. Execution translates/typesets first, selects the validated
mono PDF, then invokes the configured vision backend. Repairs retain the bounds,
numeric/formula guards, pixel regression check and follow-up acceptance described
in [visual review](visual-review.md). A failed translation starts no review.
Sampled, unresolved, failed and budget-exhausted runs never become full acceptance.
Original translation and rejected candidates remain available. Final retained
PDFs and `pipeline-report.json` are in the pipeline output directory.

Codex uses the existing ChatGPT login, with both models explicitly selected.
Compatible APIs use `type: openai`, `base_url`, `model`, `auth: env` and an
`api_key_env` variable name. No literal key is permitted. For visual review add
`vision: true`, `retries: 0`; choose `response_format` explicitly if the server
needs `json_object` or `none` rather than strict `json_schema`. Replies are still
validated locally. Choose `token_limit_field: max_completion_tokens` for servers
which require that field; the local-compatible default is `max_tokens`.
An unsupported request fails without format retries or model changes.

`assets/job.local.example.json` and `visual-review.local.example.json` connect to
an already-running local OpenAI-compatible server. Explicit `auth: none` is
restricted to loopback and requires no key or installed credential. BabelDOC's
SDK receives a temporary nonsecret placeholder; the visual HTTP client sends no
Authorization header in that mode. Replace model placeholders with existing
installed model IDs. No model installation or download is performed.

The image capability probe is mandatory and billed/accounted as an attempt.
It uses a fresh random image code, not a claim inferred from the model name.
A server ignoring image parts fails the probe before document review. Passing
the probe is not evidence of translation accuracy or a guarantee of OCR quality.
Page-review cache hits still require one fresh probe per run. Hard call/time/round
caps include failed attempts; unknown monetary cost stays null. API usage retains
its original prompt/completion/detail counter names without double summing them.

Native translation retains program-owned slots, marker and explicit-name guards.
The legacy compatible translation route remains BabelDOC's direct API, with
engine retry/cache behavior; do not assume the native bridge's extra identifier
guards or call accounting apply to that route. Its result still needs the complete
visual loop and independent acceptance for the intended document class.

Astra is a separate development assessment after the economical production loop:
use `assets/visual-review.development.example.json` against `production/best.mono.pdf`.
Its role is `development_acceptance`, repair is disabled, and its findings are
compared with the source by the developer. Production never invokes this profile
automatically. Twenty-one pages need at least22 Astra calls including the probe.

Protocol references: [OpenAI vision](https://developers.openai.com/api/docs/guides/images-vision),
[Ollama's compatible local image interface](https://docs.ollama.com/api/openai-compatibility).
Protocol support and deterministic HTTP tests do not mean every local model has
been run or accepted. Record the actually tested backend/model and untested cases.
