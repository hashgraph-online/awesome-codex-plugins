#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const path = require('node:path');

const collector = path.resolve(__dirname, '../../../mcp/yandex-wordstat/scripts/wordstat_cloud_gateway_collect.py');
const result = spawnSync('python3', [collector, ...process.argv.slice(2)], { stdio: 'inherit' });
if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status ?? 1);
