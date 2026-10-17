import fs from 'node:fs';
import path from 'node:path';

/**
 * Emit a structured progress event to .meta/progress.jsonl
 *
 * @param {string} cwd - Working directory
 * @param {string} feature - Feature name
 * @param {object} event - Event object { type, ...data }
 */
function emitProgress(cwd, feature, event) {
  const progressPath = path.join(cwd, '.boss', feature, '.meta', 'progress.jsonl');
  const metaDir = path.dirname(progressPath);

  if (!fs.existsSync(metaDir)) {
    try {
      fs.mkdirSync(metaDir, { recursive: true });
    } catch (err) {
      process.stderr.write('[boss-skill] emitProgress/mkdirSync: ' + err.message + '\n');
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
    process.stderr.write('[boss-skill] emitProgress/append: ' + err.message + '\n');
  }
}

export { emitProgress };
