import * as fs from 'node:fs';
import * as path from 'node:path';

export interface ProgressEvent {
  type: string;
  data?: Record<string, unknown>;
}

export function emitProgress(cwd: string, feature: string, event: ProgressEvent): void {
  const progressPath = path.join(cwd, '.boss', feature, '.meta', 'progress.jsonl');
  const metaDir = path.dirname(progressPath);

  if (!fs.existsSync(metaDir)) {
    try {
      fs.mkdirSync(metaDir, { recursive: true });
    } catch (err) {
      process.stderr.write(`[boss-skill] emitProgress/mkdirSync: ${(err as Error).message}\n`);
      return;
    }
  }

  const entry = JSON.stringify({
    timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
    type: event.type,
    feature,
    data: event.data || {},
  });

  try {
    fs.appendFileSync(progressPath, entry + '\n', 'utf8');
  } catch (err) {
    process.stderr.write(`[boss-skill] emitProgress/append: ${(err as Error).message}\n`);
  }
}
