#!/bin/sh
set -e

echo "==> Running Drizzle migrations..."
export NODE_PATH=/app/node_modules:/deps/node_modules

if [ -d "{{MIGRATION_DIR}}" ]; then
  node -e "
    const { drizzle } = require('drizzle-orm/node-postgres');
    const { migrate } = require('drizzle-orm/node-postgres/migrator');
    const { Pool } = require('pg');
    const pool = new Pool({ connectionString: process.env.DATABASE_URL });
    const db = drizzle(pool);
    migrate(db, { migrationsFolder: '{{MIGRATION_DIR}}' })
      .then(() => { console.log('Migrations complete'); pool.end(); })
      .catch(e => { console.error('Migration failed:', e); process.exit(1); });
  "
fi

echo "==> Starting application..."
exec node {{ENTRY_FILE}}
