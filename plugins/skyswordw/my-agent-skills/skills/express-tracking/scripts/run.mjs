#!/usr/bin/env node

import { runCli } from "../src/run.mjs";

runCli().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`错误: ${message}`);
  process.exitCode = 1;
});
