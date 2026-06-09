#!/bin/sh
set -e

echo "==> Running TypeORM migrations..."
npx typeorm migration:run -d {{DATASOURCE_PATH}}

echo "==> Starting application..."
exec node {{ENTRY_FILE}}
