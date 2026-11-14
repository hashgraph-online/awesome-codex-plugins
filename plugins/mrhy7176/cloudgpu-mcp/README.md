# CloudGPU MCP

[CloudGPU](https://cloudgpu.app) MCP server: let an AI agent compare GPU compute costs, approve source-specific billing, run a job, bring the results back and shut the GPU down. The same API key and balance also cover CloudGPU's OpenAI-compatible model API, so an agent can call a hosted model without renting anything.

> "Fine-tune a 7B base model with LoRA on data/train.jsonl and put the adapter in ./outputs."

The agent checks live prices and quotes you, rents the GPU once you say yes, uploads your code and data, starts training in the background, watches the logs, downloads the adapter and destroys the instance. You get the files and the final cost.

It is a local (stdio) MCP server. It works with any MCP client that can start one: Claude Code, Cursor, Cline, opencode, goose, VS Code, Windsurf and others.

## Install

For the browser-approval flow, add this local MCP server **without** an API key first:

```bash
claude mcp add cloudgpu -- npx -y cloudgpu-mcp
```

For another stdio client, use `command: "npx"` and `args: ["-y", "cloudgpu-mcp"]`; omit the environment key. Ask the Agent to call `connect_account`, open its returned CloudGPU link yourself, approve the account, spending limit, GPU concurrency and expiry, then let it call `finish_connect`. Never paste your password or API key into the conversation. The client must support and configure MCP; the approval link alone does not install tools in an arbitrary assistant. Existing API-key setup remains available below.

1. Create an API key at [cloudgpu.app/api](https://cloudgpu.app/api) and add a prepaid balance (card or USDT).
2. Add the server to your client. Node.js 18 or newer is required. The key goes in the environment variable `CLOUDGPU_API_KEY`.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add cloudgpu --env CLOUDGPU_API_KEY='<YOUR_API_KEY>' -- npx -y cloudgpu-mcp
```
</details>

<details>
<summary><b>Cursor</b> (<code>~/.cursor/mcp.json</code> or <code>.cursor/mcp.json</code>)</summary>

```json
{
  "mcpServers": {
    "cloudgpu": {
      "command": "npx",
      "args": ["-y", "cloudgpu-mcp"],
      "env": { "CLOUDGPU_API_KEY": "<YOUR_API_KEY>" }
    }
  }
}
```
</details>

<details>
<summary><b>Cline</b> (MCP Servers → Configure MCP Servers → <code>cline_mcp_settings.json</code>)</summary>

```json
{
  "mcpServers": {
    "cloudgpu": {
      "command": "npx",
      "args": ["-y", "cloudgpu-mcp"],
      "env": { "CLOUDGPU_API_KEY": "<YOUR_API_KEY>" }
    }
  }
}
```
</details>

<details>
<summary><b>opencode</b> (<code>opencode.json</code>)</summary>

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "cloudgpu": {
      "type": "local",
      "command": ["npx", "-y", "cloudgpu-mcp"],
      "environment": { "CLOUDGPU_API_KEY": "<YOUR_API_KEY>" },
      "enabled": true
    }
  }
}
```
</details>

<details>
<summary><b>goose</b> (<code>~/.config/goose/config.yaml</code>, or <code>goose configure</code> → Add Extension → Command-line Extension)</summary>

```yaml
extensions:
  cloudgpu:
    name: cloudgpu
    type: stdio
    cmd: npx
    args: ["-y", "cloudgpu-mcp"]
    envs:
      CLOUDGPU_API_KEY: "<YOUR_API_KEY>"
    enabled: true
    timeout: 300
```
</details>

3. Optional but recommended: copy [`rules/cloudgpu.md`](rules/cloudgpu.md) into your project as `AGENTS.md`, `.cursor/rules/cloudgpu.md` or `.clinerules/cloudgpu.md`. It tells the agent to quote before renting, download before shutting down, and never leave a GPU running. The server also exposes the same text as the resource `cloudgpu://rules`.

To check the install, ask your agent: "List the GPUs available, then estimate the cost for a 24 GB GPU for one hour. Do not create anything." You should see `list_gpus` and `estimate_cost` calls and a quote, and nothing is rented.

## Agent Skill

The same guidance is available as two [Agent Skills](https://agentskills.io):

- [`skills/cloudgpu/SKILL.md`](skills/cloudgpu/SKILL.md): renting and using a GPU. Claude Code loads it on demand when you ask for a GPU job. It expects the `cloudgpu` MCP tools to be installed (see above).
- [`skills/cloudgpu-model-api/SKILL.md`](skills/cloudgpu-model-api/SKILL.md): calling the OpenAI-compatible model API at `https://cloudgpu.app/v1` without renting a GPU. It works with the MCP tools or with just a `CLOUDGPU_API_KEY`.

- **Claude plugin:** both skills are included automatically when you install the CloudGPU Claude plugin from this repo's marketplace:

  ```
  /plugin marketplace add cloudgpu-app/cloudgpu-mcp
  /plugin install cloudgpu@cloudgpu
  ```

- **Codex plugin:** the same repository is an Agent Plugins package (`plugin.json`, `mcp.json`, and `skills/`). Codex shows it as CloudGPU. The server reads `CLOUDGPU_API_KEY` from the environment.

  ```
  codex plugin marketplace add cloudgpu-app/cloudgpu-mcp
  ```

- **Claude Code, personal install:** copy `skills/cloudgpu/` and `skills/cloudgpu-model-api/` to `~/.claude/skills/`.
- **Claude Code, project install:** copy `skills/cloudgpu/` and `skills/cloudgpu-model-api/` to `.claude/skills/` in your project.
- **Cursor, Codex, Cline, Amp and other agents that read Agent Skills:** install both skills with the [skills CLI](https://skills.sh):

  ```
  npx skills add cloudgpu-app/cloudgpu-mcp
  ```

## Tools

| Tool | What it does |
|---|---|
| `get_account` | Balance, and how many instances the account may run at once |
| `list_gpus` | GPU models with VRAM, live price per GPU-hour and availability |
| `list_templates` | Ready-made images: JupyterLab, Ollama, ComfyUI, LLaMA-Factory, … |
| `compare_compute_costs` | Compare live total billed GPU cost for up to eight compatible candidates; no reservation or creation approval |
| `estimate_cost` | Live quote for a GPU and a number of hours, plus your balance afterwards; returns a `quote_id` |
| `create_instance` | Rents from an approved quote, with a budget, a time limit and an idle limit |
| `get_status` / `list_instances` | Status, minutes run, cost so far, auto-shutdown limits |
| `run_command` | Runs a command on the instance; `background=true` for long jobs |
| `tail_logs` | Latest log lines, whether the job finished, GPU utilisation |
| `upload` / `download` | Files and folders between your computer and the instance (SFTP) |
| `stop_instance` | Destroys the instance and stops billing |
| `list_models` | Models on the OpenAI-compatible API, for inference without renting a GPU |
| `run_job` | Starts a GPU, runs one command and destroys the GPU, all on CloudGPU's servers; safe to retry with the same `idempotency_key` |
| `get_job` / `list_jobs` | Job status, exit code, cost, the last ~4 KB of output and the job's history |
| `cancel_job` | Stops a job and destroys its GPU |
| `get_agent_readiness` / `assess_task_fit` | Anonymous capability, billing, task suitability and evidence checks; no GPU is created |
| `request_top_up` / `wait_for_funds` | Human-only payment link and bounded polling for actual credit; no automatic charge or Job |
| `quote_storage_budget` / `confirm_storage_budget` | Quote and explicitly approve an earmarked storage transfer; backend rollout and owner permissions apply |
| `resume_artifact_upload` | Resume the same owned multipart reservation with the original local file and checksum |
| `connect_account` / `finish_connect` | Gets a key without copying one: the user approves this assistant in the browser with a spending limit and a number of GPUs at once |

The server also provides a `train_on_cloudgpu` prompt.

## Guardrails

- **A quote first.** `create_instance` only takes a `quote_id` from `estimate_cost` and `user_confirmed=true`.
- **Server-side limits.** Every instance is created with `max_spend_usd`, `max_hours` and an idle limit (60 minutes by default). CloudGPU's servers check them and destroy the instance when one is hit, even if your client has disconnected or your laptop is asleep.
- **Your own ceiling.** `CLOUDGPU_MAX_SPEND_USD` and `CLOUDGPU_MAX_HOURS` cap what the agent may set.
- **Results before shutdown.** After commands have run, `stop_instance` refuses until something has been downloaded, unless the user confirms `force=true`.
- **Secrets stay out of the chat.** The instance's SSH login is used inside this process and never returned to the model. Tool output is scrubbed of the API key and login details. Uploading `.ssh`, `.env`, key files or your whole home directory needs `allow_sensitive=true`.
- **The instance stays manageable.** Commands that change the root password, SSH configuration, firewall or the platform's monitoring agent are refused. CloudGPU shuts down instances that it can no longer monitor.
- **Jobs are not started twice.** `run_job` sends an `Idempotency-Key`. Resending the same job returns the same job instead of starting a second GPU, and the server refuses the same key with different parameters.
- **Keys with a budget.** A key from `connect_account` has a total spending limit, a number of GPUs it may run at once and an expiry date, all enforced by CloudGPU's servers. Revoke it at https://cloudgpu.app/api and it can no longer start anything.
- **Read-only mode.** `CLOUDGPU_READ_ONLY=1` registers only the look-up tools.

## Configuration

| Env | Default | |
|---|---|---|
| `CLOUDGPU_API_KEY` | (or `connect_account`) | From https://cloudgpu.app/api. Without it, a key saved by `finish_connect` in `~/.config/cloudgpu/credentials.json` is used |
| `CLOUDGPU_MAX_SPEND_USD` | `50` | Highest budget the agent may set for one instance |
| `CLOUDGPU_MAX_HOURS` | `24` | Longest time limit the agent may set |
| `CLOUDGPU_READ_ONLY` | off | `1` = look-up tools only |
| `CLOUDGPU_BASE_URL` | `https://cloudgpu.app` | Override the API host |

## Model API on the same balance

The key also works with the OpenAI-compatible API at `https://cloudgpu.app/v1`. Call `list_models` (or `GET /v1/models`) to see the available model IDs. Model prices are on [cloudgpu.app/api](https://cloudgpu.app/api).

## Optional persistent files and Workspaces

These tools require persistent storage to be explicitly enabled on the server;
they return `storage_not_enabled` until it is ready. Discover server capabilities
at `/v1/public/compute-capabilities`. Read `get_storage` for current included allowance, quota, prices and retention. Storage fees are separate from GPU Job budgets. Uploads above the included allowance require `accept_storage_charges=true` after user agreement; the default is false. Budget-limited connect-link keys cannot enable paid storage. Files expose `expires_at`; downloading does not renew retention. Versions containing expired files become unavailable, while active Jobs defer deletion.

- `get_compute_catalog` and `quote_compute` use public discovery and server quotes,
  including required starting balance and `supports_jobs`. Pass the server quote to
  `run_job` as `quote_id`; the original `estimate_cost` remains a local quote for
  interactive instance rentals.
- `get_storage`, `list_files`, `list_workspaces`, `list_workspace_versions` and
  `get_workspace_version` show saved files, versions and usage.
- `upload_artifact` and `download_artifact` transfer persistent files, including
  datasets/models, without returning storage credentials to the assistant.
- `save_workspace` saves regular project files as an immutable version. It refuses
  known credential paths and symlinks, and skips `.git`, `node_modules`,
  `__pycache__` and `.venv`. Save dependency manifests so the next GPU can rebuild
  its environment. The returned `workspace_version_id` can be passed to `run_job`.
- `delete_file` and `delete_workspace_version` require explicit user confirmation
  and refuse active references.

This restores project files into a fresh directory before the Job command. It is
not full-disk restore and does not automatically save edits or collect outputs.
Continue saving results from the command itself. Large-model restore speed and
cross-supplier cache behavior must be measured before relying on them. Backend restore plans travel via SSH stdin, never in
Job command arguments or saved scripts; the user command starts after restoration.
This does not protect transfer-time memory from root on the GPU. Failed deletions
or expired uploads may remain pending while the server verifies cleanup; quota is
released only after confirmed removal. With storage disabled, normal catalog,
account, instance and Job tools keep working without a storage provider.


The developer acceptance script `node scripts/acceptance.mjs` is read-only by
default. Its `--paid` mode is for an explicitly authorized internal test account
only; it can create two Jobs capped at $0.03 each. Do not run paid mode as part of
ordinary package tests.

## Without MCP

The server wraps CloudGPU's public REST API, which any agent or script can call with the same key:

```bash
curl https://cloudgpu.app/v1/gpu/offers -H "Authorization: Bearer $CLOUDGPU_API_KEY"
```

## Command-line tool

The package also installs a `cloudgpu` command for using the same API from a terminal (Node.js 18.3 or newer, no extra dependencies):

```bash
npm install -g cloudgpu-mcp      # or run it once with: npx -p cloudgpu-mcp cloudgpu --help
cloudgpu login                   # saves your key to ~/.config/cloudgpu/config.json (mode 0600)
cloudgpu offers                  # GPU models with live price and availability
cloudgpu up --gpu "RTX 4090" --template comfyui --max-minutes 120 --max-spend 5 --wait
cloudgpu ssh <id>                # opens your system ssh to the instance
cloudgpu down <id>               # destroys it and stops billing (asks first; --yes to skip)
```

| Command | What it does |
|---|---|
| `login` | Save an API key (input hidden, or piped on stdin); checked against the API first |
| `offers [--template ID]` | GPU models, VRAM, live price per GPU-hour, availability |
| `templates` | Ready-made images and the GPU each recommends |
| `up --gpu MODEL [--template ID] [--count N] [--max-minutes N] [--max-spend USD] [--idle-minutes N] [--setup FILE] [--wait]` | Rent an instance; `--setup` runs a bash script once as root after hand-over (log in `/root/cloudgpu-setup.log`); `--wait` polls until it is running or failed, then prints the SSH command and URL |
| `ls` / `status <id>` | Instances with status, minutes run and cost so far |
| `ssh <id> [-- ARGS]` | Run `ssh` with the instance's host, port and user; `--show-password` prints the password if there is one |
| `down <id> [--yes]` | Destroy the instance; its disk is erased, so download results first |
| `balance` | Balance and how many instances the account may run |

`CLOUDGPU_API_KEY` takes precedence over the saved key, and `CLOUDGPU_BASE_URL` overrides the API host. Read commands accept `--json`; SSH passwords are left out of JSON unless you pass `--show-password`. Every command has `--help`. Errors print the API's message and exit non-zero (2 for usage errors).

## Links

- MCP docs: https://cloudgpu.app/docs/mcp
- GPU pricing: https://cloudgpu.app/pricing
- Model API and prices: https://cloudgpu.app/api
- API reference: https://cloudgpu.app/api/docs · OpenAPI: https://cloudgpu.app/openapi.json · For LLMs: https://cloudgpu.app/llms.txt

CloudGPU here means cloudgpu.app. Prepaid balance, source-specific minute or started-hour billing; when the balance runs out, running instances are destroyed and their disks erased, so keep enough balance for the job and download results as you go.

## Development

```bash
npm install
npm test
node src/index.js   # stdio server; set CLOUDGPU_API_KEY first
node src/cli.js --help
```

## License

MIT, see [LICENSE](LICENSE).


### Apply a Workspace to a GPU you already rent

Use `list_workspace_instances`, then `get_workspace_application` with the saved `version_id` and the selected `instance_id`. After the user agrees, call `apply_workspace` with `user_confirmed: true`, then poll status. The files appear in a new private project directory; existing files are never overwritten. This does not install dependencies, execute project code or start, stop, or restart a GPU. Rental billing continues during transfer. Budgeted Agent keys can only target instances created with the same key. Workspace requires a funded account.

Repeated application of the same version to the same instance returns the existing result, including user edits after success. On `needs_attention`, `failed` or `conflict`, inspect the result rather than automatically retrying. A new saved version creates a separate directory. The feature must be enabled by the server; unavailable storage does not disable ordinary GPU rental or Job tools.

### D13 model preparation (0.8.0)

Version 0.8.0 adds three preparation tools; check both the installed tools and live backend capabilities before using them:

- `resolve_model_reference`: resolve a public Hugging Face branch/tag and explicit filenames to a commit-addressed manifest, sizes and available LFS SHA-256. No weights are hosted by CloudGPU. To enable verified use of the instance’s existing mirror, up to 8 selected JSON configuration files of at most 64 KiB each may be read from the pinned origin and SHA-256 hashed, within a shared 15-second deadline. Weight files are not fetched by this resolver. Private/gated models are refused.
- `prepare_job_rerun`: read parameters from a successful owned Job. No new GPU, old quote or old idempotency key. Obtain a fresh quote and explicit budget approval before `run_job`.
- `prepare_model_deployment`: prepare a setup script for the **existing ComfyUI template**, with direct model downloads and optional UI-format workflow JSON. Use the model name as a category (e.g. `checkpoints`, `loras`, `vae`). Review and approve the script before deploying. Custom nodes are not installed and workflows are not executed automatically. This is preparation support, not a real-GPU-validated template catalog.

`run_job` accepts optional `model_references`. A supporting backend is checked before submission; an old backend cannot silently ignore the references. Models are downloaded after Workspace restoration, into `$CLOUDGPU_MODEL_DIR/<name>/<path>`. Download time consumes the same rental budget. File size/checksum, disk and download timeout failures stop the Job and follow the existing release-evidence flow, without provisioning retries. The weights disappear with the GPU unless the user separately persists them; no R2 model cache is added.

Agent-first interaction: ask your Agent to run the project again; no separate web Job console or model JSON form is required. Team-authorized keys spend the selected team wallet; personal funds are separate.

Suggested workflow: resolve references → review model license/files and compatible environment → get quote → obtain explicit budget/time/GPU approval → run once with a stable idempotency key → poll status/cost → prepare a rerun only after success. Output collection remains the user's command's responsibility.

See [`examples/pinned-model-job.mjs`](examples/pinned-model-job.mjs) for a default **dry-run** REST example. Do not enable submission during routine tests. Bounded internal acceptance covered actual MCP, candidate HTTP authentication/MySQL, independent model hashes, two GPU runs and release. A separate ComfyUI image accepted model links and a workflow file. This does not validate arbitrary custom nodes or graph execution.

## Small Job output snapshots and diagnosis (0.7.0)

This branch adds `diagnose_job` (read-only) and `save_job_output` (explicit storage write). Check the installed tool list before using them; they are not a claim about the currently published npm release.

`save_job_output` stores only the ended Job output tail as a small Artifact. It is not a full log, file collector, disk snapshot or automatic backup. Known credential patterns and queried URLs are refused. Review output for other sensitive data before approving storage. Existing eligibility, quota, retention and explicit paid-storage consent apply; the GPU Job budget does not authorize paid storage. No GPU is created, kept alive or stopped by these tools. Matching snapshots are verified and reused when found; concurrent different client processes may still create duplicate artifacts.

`diagnose_job` reports the error category, platform instance status and whether platform charges are final. It does not prove supplier release, infer that command failures are always user errors, or automatically rerun work. `needs_attention` requires resource reconciliation before a new task. A rerun requires a fresh quote, explicit approval and a new idempotency key.

Registry configuration allows discovery and connect-link approval without pre-entering a key. A tool-enabled MCP client is still required; a link does not install a client or grant unlimited spending. No new fixed infrastructure or model storage is introduced.

### Optional Job output collection (requires backend capability)

Call `run_job` with `outputs: {"files":["metrics.json"],"max_bytes":1048576}` and a command that writes to `"$CLOUDGPU_OUTPUT_DIR/metrics.json"`. Files are relative to this dedicated directory; the platform does not scan the disk. The server refuses unsupported backends rather than silently starting a Job without saving results. GPU download/execution/upload time shares the same time and spend limits.

After completion, inspect `get_job.output_collection`: only `succeeded` confirms collection. Each saved entry gives `file_id`, `sha256`, `size_bytes` and status; use existing file download tools. Partial failure may retain ready files, but is not overall success. Cancellation, budget exhaustion, instance loss or interrupted collection can prevent saving; GPU release still proceeds with no automatic re-run. Files follow the existing account quota, storage pricing and 30-day retention. `accept_storage_charges` defaults false and requires explicit user agreement to paid storage. The 10 MiB default/100 MiB maximum is a transfer bound, not a new user quota. File-name protections cannot guarantee that user-selected file contents contain no secrets.

### Job log snapshot safety

Version 0.8.0 still has a credential-filter gap in `save_job_output`; upgrading to 0.8.0 did not fix it. The 0.9.0 candidate rejects quoted JSON credential keys, common prefixed/aliased secret fields, authorization schemes, queried/user-info URLs and bounded common escaped representations before any storage operation. Safe logs remain byte-identical. This is a conservative recognizable-pattern check, not a guarantee that arbitrary, encrypted or unknown credentials will be detected. Save only logs you know are sanitized, with explicit user approval; no actual exposure is established by this fix.

## Reusable task drafts (D16)

`list_task_templates` and `prepare_task_template` are local, read-only tools: no account is required, no API call is made, and preparing a draft never rents a GPU. Start with `gpu-check`, `csv-summary`, or `workspace-python`. CSV work normally belongs on your local CPU; do not rent a GPU merely to process a small CSV.

```json
{"template_id":"gpu-check","persist_results":false}
```

For an existing project, pass `workspace-python`, an immutable `workspace_version_id`, and a reviewed relative `.py` entrypoint. The script runs in the restored project; prepare its dependencies yourself. Inference/training compatibility is not certified. For model/workflow file preparation, `prepare_model_deployment` remains available. The experimental execution recipes below reuse a prepared environment; image/SDXL LoRA is not included.

The returned `run_job_draft` deliberately omits GPU selection, quote, budget, time limit, approval and idempotency key. Request a live quote, obtain explicit approval, then call existing `run_job`. Failed tasks are not automatically retried. To preserve results, explicitly request `persist_results`; normal storage eligibility, retention, quota and fees apply. `workspace-python` also requires the exact `output_files` your script writes under `$CLOUDGPU_OUTPUT_DIR`. Storage-fee consent defaults to false and is separate from GPU approval.

### Experimental application execution recipes

`comfyui-workflow` runs an API-format workflow saved in an immutable Workspace against an **already prepared ComfyUI** application on GPU loopback (default port 8188). Models and custom nodes must already be available and reviewed. Supply `workflow_path`, `image_count` (1–4) and optionally `comfy_port`/`timeout_seconds`. It checks readiness, submits exactly once, polls that prompt and writes explicit `image-N.png` files plus `task-summary.json`. Lost submission responses, errors, redirects or unexpected output counts stop the task; no second prompt is submitted.

`causal-lm-lora` is **small causal-language-model LoRA**, not ComfyUI/image/SDXL training. Supply `dataset_path` (JSONL with a `text` field), a pinned public `model_reference` including configuration/tokenizer/weights, and reviewed `target_modules`. Optional `steps` (1–200), `rank` (1–16), `sequence_length` and `learning_rate` bound the work. Reuse an image with compatible CUDA, torch, transformers, peft and safetensors already installed. Model loading is offline from the D13 model directory with remote model code disabled. It writes `adapter_model.safetensors`, `adapter_config.json` and `task-summary.json`.

Both recipes require `persist_results=true` and an immutable Workspace. They do not install software or start servers, and preparation does not select a GPU, infer a budget, claim image compatibility or consent to storage charges. The existing Job API checks output-collection availability before accepting the request. GPU time, downloads and collection share the approved Job cap; existing storage charges are separate. Failed collection does not keep the GPU disk alive. Do not save arbitrary private logs as artifacts.

**Validation boundary:** ComfyUI HTTP execution/output and LoRA orchestration have local protocol fixtures, not real GPU generation/training or quality acceptance. These recipes remain experimental. Check the selected image and model before a paid run; no universal compatibility claim is made.

## Bounded batches (D17 first stage)

1. Prepare each reviewed Job with a fresh `quote_compute` quote, its own GPU spending cap and time limit. Select output storage explicitly.
2. Call `prepare_job_batch` with a caller-retained `batch_key`, `jobs` (1–8) and `total_budget_usd`. Preparation is local and read-only. The sum of per-Job maximum spending must fit the total and client cap; this is a **GPU budget**, excluding separately approved storage charges.
3. Present all tasks, their quotes, time limits and combined cap to the user. Only after explicit approval, call `run_job_batch` with the identical input, returned `approved_plan_sha256` and `user_confirmed=true`.
4. Retain the manifest, batch key and response receipt. Partial acceptance is possible; this is not an atomic transaction or an independent scheduler. A lost acknowledgement stops new submissions. To reconcile, replay only the **identical** approved manifest/key: existing server-side idempotency returns the original Jobs. Never invent replacement keys or silently change an expired quote. Changing a task requires a new review; an old batch key is not permission for extra spending.
5. Poll `get_job_batch` with the explicit Job IDs. `stopping`, `needs_attention`, unknown or unavailable state requires reconciliation. Do not treat a failed status or a destroy request as independent supplier release evidence. Cancel individual Jobs only through the existing `cancel_job` tool when authorized.

There are **no automatic failed-execution retries**. Each submitted Job survives a client disconnect using the existing durable backend queue. Unsubmitted members do not continue in the background if the MCP process exits. Fresh-attempt retry automation and a durable batch-level coordinator are not included. No warm GPU pool or new infrastructure is required.


### Private local batch receipts (0.12.0)

`run_job_batch` now journals submission intents and accepted Job IDs under `CLOUDGPU_CONFIG_DIR` (default `~/.config/cloudgpu`), in a private `batch-receipts-v1` directory. `get_job_batch_receipt({batch_key})` reads this local metadata without an API request. It records no commands, complete manifests, API keys, model URLs or signed links. Keep your original reviewed manifest separately.

After a client restart, reconnect with the **same scoped API key and endpoint**. Inspect the receipt, then use `get_job_batch` for live status. Replaying the exact approved manifest queries known accepted Jobs; only an uncertain acknowledgement is reconciled by the original create request/key. Unavailable, `stopping` or `needs_attention` stops progress. A local historical status is not a current supplier release audit. A missing receipt (another device/key, an older client, or lost files) is never proof that no GPU exists.

The local store must support private file permissions, no-follow file opens and atomic hard links. An unsafe/unavailable store refuses new batch submissions; a write failure after acceptance returns the known Job ID and stops later members. Do not silently switch to a new key or discard uncertain records. New entries are refused once 1,024 batch directories are observed for a key/endpoint; this local housekeeping check is not a concurrent server quota. Archive **verified terminal** receipts explicitly. Original single-Job tools remain available.

This is client-local receipt durability, not a server-side batch coordinator. Unsubmitted members do not run while the client is closed. No automatic retry of failed execution, new-attempt spending, refund or cancellation is added. Preparing a plan still creates no GPU and requires no account; paid submission still requires exact plan approval, fresh quotes and existing GPU/storage limits. Scopes on different keys or endpoints are separate; inspect existing resources before intentionally changing either.

Keep the exact original manifest outside the receipt store. Expired quotes for unsubmitted members may require reconciliation followed by a newly reviewed plan for the remaining work; do not overwrite the old ledger or regenerate keys merely to bypass expiry. Terminal status without final cost evidence also stops a journaled resume.

One in-flight batch retains its original API credential and endpoint even if another tool connects a different account concurrently. `not_submitted` in a returned call receipt means unvisited **in that invocation only**; those entries may have accepted Jobs from an earlier call. Inspect the saved receipt and live Job IDs before deciding what remains.

Use 0.12.1 or newer for directory-entry durability: newly created config/receipt directories and their parent entries are synced before paid submission. A parent-directory sync failure refuses new batch work. Existing 0.12.0 receipt records remain readable; preserve their IDs and original keys rather than deleting them. Process-exit tests alone do not constitute physical power-loss testing.

### Rental billing quotes (0.13.0)

`estimate_cost` obtains a short-lived server billing quote and reports the minimum charge, billing increment and preauthorization. Most sources charge by the minute. A whole-hour source starts billing at resource allocation, has a one-hour minimum and charges each started hour in full; voluntary stop does not refund unused time inside that hour. Show these terms and the estimate before requesting the user’s approval. `rent_gpu` submits the same approved billing quote; expired quotes require a new estimate and approval. Do not infer billing periods from the GPU model or hourly price.

Upgrade your installed `cloudgpu-mcp` package and restart the MCP client to load the new tools. This update does not restart existing GPUs.

### Registry namespace update (0.13.1)

The current MCP Registry listing is `io.github.cloudgpu-app/cloudgpu-mcp`, matching the repository organization. Older entries under `io.github.mrhy7176/cloudgpu-mcp` are historical. The npm package remains `cloudgpu-mcp`; existing stdio configurations and scoped API keys do not change. Upgrade the package and restart your MCP client.

### Agent compute planning (0.14.0)

Ask your connected Agent: “Compare compatible GPUs for this task, include preparation and download time, and show the minimum charge before creating anything.” `compare_compute_costs` checks live rental quotes and sorts by estimated billed GPU cost, including whole-hour minimums. It does not benchmark speed or prove Job/template support. A fresh `estimate_cost` and explicit billing approval are still required to rent.

Can one GPU serve several Agent tasks? Yes: sequential approved `run_command` calls can use the same running rental, within its original budget, deadline and idle limit. Check `list_instances` / `get_status` first. Independent `run_job` calls and “rerun” each provision separately; they do not share an instance. Do not extend limits or keep an idle GPU merely because an hour was charged. Save outputs before stopping; Workspace is explicit persistence, not a disk snapshot.

MCP clients must install or upgrade this package and restart their local MCP process. The account connection link authorizes a supported client; it cannot install tools into any arbitrary AI service.

### Several tasks, one GPU allocation (0.15.0)

`prepare_task_pipeline` prepares 1–8 reviewed commands to run sequentially as one Job. They share the GPU and filesystem; each step has a new shell, so shell variables and in-memory model processes do not persist between steps. A nonzero step exit stops subsequent steps. Dependencies and any required models must already be prepared; this is not application-quality or GPU-model acceptance.

Preparation makes no API request or reservation. Review the returned command, obtain a compatible Job quote and explicit total GPU budget/deadline approval, then call `run_job` once. Retain that submission's idempotency key if its response is lost. The manifest fingerprint is informational, not a server-enforced approval or submission key. Independent Jobs still use independent allocations; this is not the durable batch coordinator.

For an existing rental, the reviewed command can instead be passed to `run_command` in the approved working directory, within its original limits. Apply a Workspace separately when needed. The draft never stops or extends an existing rental. Whole-hour sources remain usable through the existing explicitly approved rental path; this release does not remove their current automatic-Job compatibility gate.

With `persist_summary=true`, the Job draft explicitly collects only `pipeline-summary.json` through the existing output collector, using current storage quota/retention and `accept_storage_charges=false`. The summary contains step IDs, exit codes and state, not raw logs, commands or arbitrary task results. Result-file persistence must be configured and approved separately. The summary must not already exist; missing output collection or a conflicting file aborts before commands run.

### Funded connection, storage growth and remote MCP

Version 0.16.0 was verified on npm and the official Registry on 2026-11-13. The current stdio inventory is 57 tools. The remote endpoint at `https://cloudgpu.app/mcp` uses Streamable HTTP JSON responses and OAuth authorization code with S256 PKCE; it exposes 23 tools safe without local filesystem/SSH access. Public discovery needs no login; account and paid operations require scoped owner authorization. Always check live backend capabilities and actual source-specific billing.

`connect_account` returns a direct Google link and email alternative. Pending connection state is private, origin-bound and survives restart; the server allows 30 minutes for approval. Browser payment does not approve compute. `request_top_up` creates only a short-lived owner link; `wait_for_funds` requires a real credit signal and sufficient live balance. Neither creates a Job.

Dedicated storage budget is a separate, explicitly confirmed wallet reservation, consumed only by actual UTC daily peak usage. Unused surplus can return after existing files, uploads and pending daily charges remain covered. It is not revenue or an automatic refill. Capacity can grow with budget, subject to published technical limits, and retention remains 30 days. Budget-limited Agent keys cannot reserve funds or consent to paid storage. Disabling new self-service transfers must not disable accounting for existing reserves.

Multipart resume keeps the same reservation and original file hash. GPU restore renewal is file-scoped, temporary and feature-gated; no general account key is installed on a GPU. Local fixtures do not certify TB-sized transfers. Backend automatic public-model preparation currently has a 600-second deadline: a 9.8GB Wan video case exceeded it on the measured link. Prepared images or explicitly reviewed bounded download commands need their own acceptance; do not promise that every size below the model byte limit loads in time.

The Python SDK and optional framework adapters are under [`python/`](python/README.md). PyPI publication requires an owner-configured Trusted Publisher. Real LangChain Core 1.8.0, OpenAI Agents SDK 0.24.0 and CrewAI 1.6.1 tool/invocation and anonymous HTTP acceptance passed; no paid model or GPU operation was used. See the Python README for exact scope and reproduction.

The reviewed [Python SDK0.1.0 release](https://github.com/cloudgpu-app/cloudgpu-mcp/releases/tag/python-v0.1.0) has a public wheel, source distribution and SHA256SUMS. The public wheel was downloaded and its checksum and ten SDK tests passed. PyPI is not yet configured; use the exact release URL rather than an unrelated package. Hermes root installation and existing-owner private connection/catalog acceptance passed after packaging/profile fixes in cloudgpu-app/hermes-cloudgpu#5.

### Reproducible paid task cases

See [environment check, synthetic causal-LM LoRA and tiny ComfyUI video cases](examples/verified-tasks/README.md) for pinned scripts, observed fees, download checksums and release evidence. They preview locally by default; paid submission needs owner approval. Resume an accepted Job by ID to download results without another GPU. For persistent tasks, `assess_task_fit` accepts `expected_output_bytes`; current direct collection and bounded network fallback limits are returned by the live contract.

### Durable server batches and whole-hour Jobs (0.16.3)

Use `prepare_job_batch` to review every command, fresh compute quote, deadline and aggregate GPU cap. Pass the exact manifest/hash and explicit user approval to `run_server_job_batch`. The server atomically commits all child Job rows or none; it dispatches from the database after client/server restarts, waiting for account/Key execution slots. `get_server_job_batch(batch_id)` returns bounded states/cost summaries; use individual `get_job` for detailed outputs. `cancel_server_job_batch` requires approval and preserves charges for already-started hours. Failed commands are not automatically rerun, and an uncertain provider result never authorizes another GPU.

REST equivalents: `POST /v1/job-batches` with `Idempotency-Key`, `total_budget_usd` and 1–32 `jobs`; `GET /v1/job-batches/{batch_id}`; `POST /v1/job-batches/{batch_id}/cancel`. The MCP reviewed manifest remains capped at eight children. Replaying the identical key/body returns the existing children. Existing `run_job_batch` retains its explicitly non-atomic client submission behavior for compatibility; the server tool never falls back to it.

For whole-hour Jobs, call `estimate_cost` for the exact configuration and accept the minimum/billing period. Supply its `billing_quote_id` plus `billing_accepted=true` to `run_job` or each batch child, in addition to the compute `quote_id` and execution approval. Each allocation needs a separate current billing quote. The Job cap must cover the minimum; elapsed portions of a started hour are not voluntarily refunded. Billing quotes last five minutes: an expired queued Job fails without allocation and requires a new reviewed request. It is never silently renewed or routed under different billing terms. Recovery uses durable provider receipts and independent upstream presence checks; ambiguous intents remain `needs_attention`.
