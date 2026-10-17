import { color } from './search-multiselect.mts';

// Pixel-style BOSS logo with a gray gradient, mirroring the `npx skills` banner.
const LOGO_LINES = [
  '██████╗  ██████╗ ███████╗███████╗',
  '██╔══██╗██╔═══██╗██╔════╝██╔════╝',
  '██████╔╝██║   ██║███████╗███████╗',
  '██╔══██╗██║   ██║╚════██║╚════██║',
  '██████╔╝╚██████╔╝███████║███████║',
  '╚═════╝  ╚═════╝ ╚══════╝╚══════╝',
];

const GRAYS = ['250', '248', '245', '243', '240', '238'];

export function printBanner(): void {
  if (!process.stdout.isTTY) return;
  const lines = LOGO_LINES.map((line, index) => {
    const gray = GRAYS[Math.min(index, GRAYS.length - 1)]!;
    return `\x1b[38;5;${gray}m${line}\x1b[0m`;
  });
  process.stdout.write(`\n${lines.join('\n')}\n\n`);
}

export function badge(text: string): string {
  return `\x1b[46m\x1b[30m ${text} \x1b[0m`;
}

export { color };
