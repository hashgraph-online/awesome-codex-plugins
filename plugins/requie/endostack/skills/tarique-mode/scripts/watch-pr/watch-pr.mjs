import { main } from './lib/main.mjs';

main(process.argv.slice(2)).then(
  (code) => {
    process.exitCode = code;
  },
  (err) => {
    process.stderr.write(`error: internal failure: ${err?.stack ?? err}\n`);
    process.exitCode = 70;
  },
);
