#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 127
fi

DOCKERFILE="${RUST_DEPLOY_DOCKERFILE:-Dockerfile}"
CONTEXT="${RUST_DEPLOY_CONTEXT:-.}"
IMAGE="${RUST_DEPLOY_IMAGE:-rust-service-preflight:local}"

if [ ! -f "$DOCKERFILE" ]; then
  echo "Dockerfile not found: $DOCKERFILE" >&2
  exit 2
fi

echo "==> docker build -f $DOCKERFILE -t $IMAGE $CONTEXT"
docker build -f "$DOCKERFILE" -t "$IMAGE" "$CONTEXT"

if [ -n "${RUST_DEPLOY_SMOKE_COMMAND:-}" ]; then
  echo "==> docker run smoke command"
  docker run --rm "$IMAGE" sh -c "$RUST_DEPLOY_SMOKE_COMMAND"
else
  echo "==> skipping smoke run; set RUST_DEPLOY_SMOKE_COMMAND to run one"
fi
