// Writes output files with exclusive create, in parts of at most 16 MiB of
// text each so a very large output never needs one giant write.

import fs from 'node:fs';
import path from 'node:path';

export const PART = 16 * 1024 * 1024;
const MARKER = /@!@!@(STARTMSG|ENDMSG) /;

export function writeFiles(dir, files) {
  for (const [name, text] of files) {
    if (MARKER.test(text)) throw new Error(`Refusing to write ${name}: it still contains TLC tool-mode markers.`);
    const fd = fs.openSync(path.join(dir, name), 'wx');
    try {
      for (let i = 0; i < text.length; i += PART) fs.writeSync(fd, text.slice(i, i + PART));
    } finally {
      fs.closeSync(fd);
    }
  }
}
