import { type ChildProcess, spawn } from 'node:child_process';

export type SpawnOpenProcess = (
  command: string,
  args: string[],
  options: { detached: true; stdio: 'ignore' },
) => Pick<ChildProcess, 'on' | 'unref'>;

export function createOpenUrl(
  spawnProcess: SpawnOpenProcess,
  platform: NodeJS.Platform,
): (url: string) => boolean {
  return (url: string): boolean => {
    const command = platform === 'darwin' ? 'open' : platform === 'win32' ? 'cmd' : 'xdg-open';
    const args = platform === 'win32' ? ['/c', 'start', '', url] : [url];

    try {
      const child = spawnProcess(command, args, { detached: true, stdio: 'ignore' });
      child.on('error', () => {
        // The boolean API can only report synchronous spawn failures.
      });
      child.unref();
      return true;
    } catch {
      return false;
    }
  };
}

export function openUrl(url: string): boolean {
  return createOpenUrl(spawn, process.platform)(url);
}
