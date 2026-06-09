---
name: sealos-canvas
description: Run a local read-only HTML topology UI for a project already deployed by Sealos Skills and return a localhost URL. Use when the user asks to view, inspect, visualize, render, open, or run a local canvas for deployed Sealos resources, mentions ".sealos", Sealos deployment state, Kubernetes resources, topology, resource graph, localhost UI, or invokes "/sealos-canvas".
---

# Sealos Canvas

## Overview

Render the current repository's deployed Sealos resources as a locally hosted HTML canvas. This skill is view-only: it reads `.sealos/state.json` and Kubernetes resources, starts a temporary `127.0.0.1` UI server, and returns the local URL to the user.

## Hard Rules

1. Do not deploy, update, restart, patch, delete, or apply resources.
2. Only use read commands such as `kubectl get` and `kubectl config view`.
3. Use the Sealos kubeconfig at `~/.sealos/kubeconfig`.
4. Do not display Secret data or full ConfigMap contents.
5. If the project has no `.sealos/state.json` with `last_deploy`, stop and tell the user to deploy first with `/sealos-deploy`.
6. If kubeconfig or live resource access is unavailable, report the script message and stop.

## Workflow

### 1. Resolve the project

Use the current working directory unless the user provides a local path:

```bash
WORK_DIR="$(pwd)"
```

Confirm this is the intended repository before generating output.

### 2. Start the local canvas UI

Run:

```bash
node "<SKILL_DIR>/scripts/generate-canvas.mjs" --work-dir "$WORK_DIR"
```

Keep this process running while the user is viewing the canvas. The script writes JSON to stdout after the local server starts.

If `ok` is `false`, show the `message` to the user and end the flow. Do not run fallback discovery, do not deploy, and do not create any other artifact.

If `ok` is `true`, use `local_url` as the primary output.

### 3. Open the local URL

Open the returned URL with the browser:

```text
http://127.0.0.1:<port>/index.html
```

Then summarize:

- local UI URL
- app URL
- node count
- edge count

Stop the server process when the user is done viewing the page or when the current task ends.

## Output Contract

Success:

```json
{
  "ok": true,
  "local_url": "http://127.0.0.1:63220/index.html",
  "html_path": "/abs/path/.sealos/canvas/index.html",
  "node_count": 5,
  "edge_count": 4,
  "app_url": "https://example.sealos.run"
}
```

Stop condition:

```json
{
  "ok": false,
  "reason": "not_deployed",
  "message": "This project has not been deployed by Sealos Skills yet. Run /sealos-deploy first, then run /sealos-canvas again."
}
```

## Visual Target

The locally hosted UI should feel like a topology canvas, not a table:

1. Top bar with app name, namespace, deployed app URL, generated time, and local UI status.
2. Dark dotted-grid canvas with deterministic resource-card layout.
3. Resource cards for app, ingress, services, pods, config, secrets, and volumes.
4. Dashed or solid SVG connector lines between related resources.
5. PVC/volume references attached as strips on the related card when possible.
6. Detail panel for the selected resource.
7. Events panel with recent related Kubernetes events.
8. Status colors for ready, sleeping, warning, and failed states.
9. Lightweight pan, zoom, fit, and reset controls.

Theme extraction is best effort. Reuse the user's repo accent color, font, and radius when easy to detect, but preserve operational readability.

## Script

`scripts/generate-canvas.mjs` is the deterministic entrypoint. It:

1. Reads `.sealos/state.json`.
2. Verifies `~/.sealos/kubeconfig` and `kubectl`.
3. Reads live namespace resources with `kubectl get`.
4. Builds a sanitized `canvasModel` with `app`, `nodes`, `edges`, `events`, and `theme`.
5. Renders `assets/canvas-template.html` into an internal `.sealos/canvas/index.html` cache.
6. Starts a temporary local HTTP server and prints `local_url`.

Use `--no-serve` only for tests or CI checks that should generate HTML without keeping a server process alive.
