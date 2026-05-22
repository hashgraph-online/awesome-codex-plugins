#!/bin/sh
set -e

echo "==> Starting application..."
exec node {{ENTRY_FILE}}
