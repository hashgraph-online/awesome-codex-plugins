// Entry point with injectable dependencies. The launcher calls main() with
// real ones; tests call it with fakes.

import { parseCli, HELP } from './args.mjs';
import { loadConfig } from './config.mjs';
import { UsageError } from './errors.mjs';
import { processRunner } from './exec.mjs';
import { githubReader } from './github.mjs';
import { EXIT } from './proof.mjs';
import { render } from './render.mjs';
import { watch } from './watch.mjs';

export const realClock = {
  now: () => Date.now() / 1000,
  sleep: (s) => new Promise((resolve) => setTimeout(resolve, Math.max(0, s) * 1000)),
};

export async function main(argv, deps = {}) {
  const stdout = deps.stdout ?? ((s) => process.stdout.write(s));
  const stderr = deps.stderr ?? ((s) => process.stderr.write(s));
  let opts;
  let cfg;
  try {
    opts = parseCli(argv);
    if (opts.help) {
      stdout(HELP);
      return EXIT.READY;
    }
    cfg = await loadConfig(opts, { cwd: deps.cwd, readText: deps.readText });
  } catch (err) {
    if (err instanceof UsageError) {
      stderr(`error: ${err.message}\nrun 'watch-pr --help' for usage\n`);
      return EXIT.USAGE;
    }
    throw err;
  }
  const reader = deps.reader ?? githubReader(deps.run ?? processRunner({ cwd: deps.cwd }));
  const clock = deps.clock ?? realClock;
  const write = (v) => stdout(`${opts.pretty ? render(v) : JSON.stringify(v)}\n`);
  return watch(opts, cfg, { reader, clock, write });
}
