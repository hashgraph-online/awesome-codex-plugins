#!/usr/bin/env node

import { pathToFileURL } from 'node:url';

import { DEFAULT_CONSOLE_PORT, startConsole, stopConsole } from './server.mjs';

export function parseOptions(args = []) {
  let port = DEFAULT_CONSOLE_PORT;
  let open = true;
  let help = false;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--port') {
      const raw = args[index + 1];
      if (raw === undefined || !/^\d+$/.test(raw)) {
        throw new Error('--port requires an integer between 0 and 65535');
      }
      port = Number(raw);
      if (port < 0 || port > 65535) {
        throw new Error('--port requires an integer between 0 and 65535');
      }
      index += 1;
    } else if (arg === '--no-open') {
      open = false;
    } else if (arg === '--help' || arg === '-h') {
      help = true;
    } else {
      throw new Error(`unknown option: ${arg}`);
    }
  }
  return { port, open, help };
}

function usage() {
  return [
    'Usage: open-control-console [--port PORT] [--no-open]',
    '',
    'Starts the loopback Codex Agents Workflow console using the real user config.',
    `Defaults to 127.0.0.1:${DEFAULT_CONSOLE_PORT}; pass --port 0 to request a random free port.`,
    'Keep this process running while the page is open; press Ctrl+C to stop it.',
  ].join('\n');
}

export async function main(args = process.argv.slice(2)) {
  const options = parseOptions(args);
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }

  const state = await startConsole({ port: options.port, open: options.open });
  process.stdout.write('Codex Agents Workflow console is running.\n');
  process.stdout.write(`Configuration: ${state.configPath}\n`);
  process.stdout.write(`Loopback port: ${state.port}\n`);
  if (!state.browser.opened) {
    process.stdout.write(`Open manually (do not share this tokenized URL): ${state.url}\n`);
  }
  process.stdout.write('Keep this terminal open. Press Ctrl+C to stop the console.\n');

  await new Promise((resolve) => {
    let stopping = false;
    const shutdown = () => {
      if (stopping) return;
      stopping = true;
      void stopConsole().finally(resolve);
    };
    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
  });
}

const isMain = import.meta.url === pathToFileURL(process.argv[1] || '').href;
if (isMain) {
  main().catch((error) => {
    process.stderr.write(`open-control-console: ${error.message}\n`);
    process.exitCode = 1;
  });
}
