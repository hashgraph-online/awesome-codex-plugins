---
name: cloudgpu
description: Rent and use a cloud GPU on CloudGPU (cloudgpu.app) through the `cloudgpu` MCP tools. Use when the user wants to rent a GPU, run a training, fine-tuning, inference or ComfyUI job on a cloud GPU, or mentions CloudGPU or cloudgpu.app, and the `cloudgpu` MCP tools are available.
---

# CloudGPU

Follow these steps whenever you rent or use a GPU on CloudGPU (cloudgpu.app) through the `cloudgpu` MCP tools.

## Before renting

1. Call `get_account` and `list_gpus`. Pick a GPU with enough VRAM for the job, and don't rent more GPU than the job needs. As a rough guide, LoRA on a 7–8B model fits in 24 GB, and a full fine-tune of the same model needs 80 GB or more.
2. Check existing `list_instances` before renting. A compatible running rental can run multiple approved commands inside its original limits. Optionally compare billed task costs with `compare_compute_costs`, then call `estimate_cost` with preparation/download/output time included.
3. Show the user a short quote before you rent anything:
   - the GPU and how many,
   - the price per hour,
   - the billing increment and minimum charge: some sources charge a minimum one hour and every started hour in full, with no voluntary-stop refund of unused charged time,
   - the estimated hours and cost,
   - the budget and time limit you will set,
   - their balance after the job.
4. Rent only after the user says yes. Pass `user_confirmed=true` only in that case.

## Renting

- Always set `max_spend_usd` and `max_hours`. CloudGPU's servers destroy the instance when either is reached, even if you have disconnected.
- Keep `idle_minutes` on (default 60). Include setup time when agreeing limits before creation. Never silently extend the approved budget, time or idle limits.
- Call `get_status` at intervals, not in a tight loop, until the instance is `running`.
- On failure, inspect actual charges and release status; do not promise zero charges or automatic refunds. Do not retry creation while the result or resource release is uncertain.

## Working on the instance

- Put code and data on the instance with `upload`. Do not upload credentials.
- Use `run_command` for short steps. For training, long installs or big downloads, use `background=true` and follow progress with `tail_logs`.
- Instances come with Python and CUDA, but not always PyTorch. Check first: `nvidia-smi -L` and `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`.
- If PyTorch is missing, plain `pip install torch` installs a current CUDA build. It is a few GB, so run it with `background=true`. Index URLs for older CUDA versions (for example `.../whl/cu124`) may have no wheel for the machine's Python, which can be very new. Only use them if the project needs that CUDA version, and then create an environment with an older Python first (`conda create -y -n work python=3.12`, then `conda activate work && ...` in each command).
- If `nvidia-smi` shows no GPU once the instance is running, stop and tell the user. CloudGPU detects such machines and shuts them down automatically.
- **Do not** change the root password, edit the SSH configuration, change the firewall, or stop the platform's monitoring agent (`cgpu-*` processes). The platform must keep its access to the instance; if that access is lost, the platform shuts the instance down. The MCP server refuses such commands.
- Never use the GPU for cryptocurrency mining or anything the [acceptable use policy](https://cloudgpu.app/aup) forbids. Instances that do so are shut down.

## Finishing (always)

1. Download every result: model weights, adapters, checkpoints, logs, metrics. Destroying an instance erases its disk. Workspace persists only files explicitly uploaded and ready, under its quota/retention policy. It is not an automatic disk backup. Storage fees are separate from GPU budgets.
2. Call `stop_instance`.
3. Tell the user what ran, where the results are on their computer, and the final cost from `stop_instance`.

If anything goes wrong mid-way, do not leave the instance running. Download whatever exists, stop the instance, then explain what happened.

## Balance and top-ups

- If `get_account` or `estimate_cost` shows the balance would not cover the quoted job, do not call `create_instance`. Tell the user how much is missing and ask them to top up at https://cloudgpu.app/billing (card or USDT). When they say it is done, call `estimate_cost` again before renting.
- `create_instance` also checks the balance. If it is below the estimate or budget plus 10%, the MCP server does not rent anything and returns an error that starts with `Not rented: balance $... is below $...` and points to https://cloudgpu.app/billing. If the CloudGPU API itself rejects the request with HTTP status 402, the error reads `CloudGPU API error 402 <code>: <message>` followed by the same billing link. Handle both the same way as above: stop, tell the user how much is missing, and do not retry.
- Never top up, enter card details or move money on the user's behalf. The user does that themselves on the billing page.

## Checking prices without the MCP server

If the `cloudgpu` tools are not available, read current prices from https://cloudgpu.app/gpu-prices.json (machine-readable, with an `updated_at` field) or https://cloudgpu.app/pricing. Check `updated_at` and tell the user how fresh the data is. Do not quote prices from memory.

## Optional persistence

Discover tools and `GET /v1/public/compute-capabilities` first. Persistence is
unavailable when that endpoint is missing or `storage` is false. Never promise
free storage, a retention period or automatic output collection.

When enabled, ask before saving private project files. Use `save_workspace` for
regular source/config/dependency-manifest files, `upload_artifact` for persistent
results or datasets/models, and `download_artifact` to retrieve them. Pass the
saved `workspace_version_id` to `run_job` to restore the files before execution.
The service does not restore a boot disk and does not automatically save edits;
the Job command must still save its results before shutdown. Do not upload secrets.

For Jobs, prefer `quote_compute` for a server quote and send its `quote_id` with
the chosen candidate. Its `required_starting_balance` is separate from the task
estimate. The original `estimate_cost` quote belongs to `create_instance`.

## Only need a model, not a GPU?

The same API key works for CloudGPU's model API at `https://cloudgpu.app/v1`. Call `list_models` to see the models. If you only need inference on a hosted model, use the API instead of renting a GPU.

## If the MCP server is not installed

If no `cloudgpu` tools are available, the MCP server needs to be set up first:

- Command: `npx -y cloudgpu-mcp`
- Environment variable: `CLOUDGPU_API_KEY`, with a key created at https://cloudgpu.app.
- Never paste the key into the chat or into files in the project. Ask the user to put it in their MCP client's configuration or environment themselves.

See the [README](https://github.com/cloudgpu-app/cloudgpu-mcp#install) for per-client setup.

## Jobs and instance reuse

Sequential approved `run_command` calls may reuse a running rental within its original budget, deadline and idle limit. Check ownership, readiness and free memory/disk first. Independent `run_job` calls and `prepare_job_rerun` provision separately, not into that live rental. Job/template support is configuration-specific; inspect `supports_jobs` and obtain a Job quote, never substitute the rental quote. Do not keep an idle GPU merely to consume a prepaid hour. Confirm result persistence and release when finished.

## Connect with an approval link

In a configured MCP client, call `connect_account`, show the owner its link, then `finish_connect` after approval. No password or API key is pasted in chat. The link grants scoped access; it does not automatically install an MCP server in arbitrary AI products.
