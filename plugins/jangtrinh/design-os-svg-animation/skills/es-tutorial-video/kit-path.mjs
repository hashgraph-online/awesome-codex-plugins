/* Where the tutorial kit lives for this copy of the skill: a host bundle carries it as ./kit (written by
 * scripts/sync-tutorial-skill-hosts.mjs); inside the repo it is promo/_tutorial-kit. TUTORIAL_KIT overrides both. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const SKILL_DIR = path.dirname(fileURLToPath(import.meta.url));

export function kitDir() {
  const candidates = [process.env.TUTORIAL_KIT, path.join(SKILL_DIR, 'kit'), path.resolve(SKILL_DIR, '..', '..', 'promo', '_tutorial-kit')].filter(Boolean);
  const hit = candidates.find((d) => fs.existsSync(path.join(d, 'tutorial-project.mjs')));
  if (!hit) throw new Error(`tutorial kit not found; looked in: ${candidates.join(', ')}`);
  return hit;
}

/** Import the kit's shared module (config schema, project loader, timeline evaluator). */
export const kitModule = () => import(pathToFileURL(path.join(kitDir(), 'tutorial-project.mjs')).href);
