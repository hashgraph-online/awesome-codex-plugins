// Watcher configuration: review-bot identity, approval checks, and the
// markers used to spot review automation. Values come from an optional
// JSON file and are extended by command-line flags.

import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { UsageError } from './errors.mjs';

export const DEFAULT_CONFIG_PATH = path.join('.endostack', 'watch-pr.json');

// Default pattern for a review-pass identifier inside a bot comment, for
// example "run-id: 8f2c" or "automation_id=42". Override with passIdPattern.
export const DEFAULT_PASS_ID_PATTERN = '(?:run|automation)[-_ ]?id\\s*[:=]\\s*([A-Za-z0-9._-]+)';

const LIST_KEYS = ['reviewBots', 'reviewBotHosts', 'reviewBotMarkers', 'approvalChecks', 'reviewCheckMarkers'];

export function emptyConfig() {
  return {
    reviewBots: [],
    reviewBotHosts: [],
    reviewBotMarkers: [],
    approvalChecks: [],
    reviewCheckMarkers: ['security-review', 'security review'],
    passIdPattern: DEFAULT_PASS_ID_PATTERN,
  };
}

export function validateConfig(raw, source) {
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    throw new UsageError(`${source} must hold a JSON object`);
  }
  const cfg = emptyConfig();
  for (const [key, value] of Object.entries(raw)) {
    if (LIST_KEYS.includes(key)) {
      if (!Array.isArray(value) || value.some((v) => typeof v !== 'string' || v.trim() === '')) {
        throw new UsageError(`${source}: ${key} must be a list of non-empty strings`);
      }
      cfg[key] = value.map((v) => v.trim());
    } else if (key === 'passIdPattern') {
      if (typeof value !== 'string' || value === '') throw new UsageError(`${source}: passIdPattern must be a non-empty string`);
      try {
        new RegExp(value, 'i');
      } catch (err) {
        throw new UsageError(`${source}: passIdPattern is not a valid regular expression (${err.message})`);
      }
      cfg.passIdPattern = value;
    } else {
      throw new UsageError(`${source}: unknown key '${key}'`);
    }
  }
  return cfg;
}

// Load the file named by --config, or the default path when it exists.
// A missing default file is fine; a missing explicit file is a usage error.
export async function loadConfig(opts, { cwd = process.cwd(), readText = (p) => readFile(p, 'utf8') } = {}) {
  let cfg = emptyConfig();
  const explicit = opts.configPath;
  const file = path.resolve(cwd, explicit ?? DEFAULT_CONFIG_PATH);
  let text = null;
  try {
    text = await readText(file);
  } catch (err) {
    if (explicit) throw new UsageError(`cannot read --config ${explicit}: ${err.code ?? err.message}`);
  }
  if (text !== null) {
    let raw;
    try {
      raw = JSON.parse(text);
    } catch {
      throw new UsageError(`${file} is not valid JSON`);
    }
    cfg = validateConfig(raw, file);
  }
  cfg.reviewBots = [...cfg.reviewBots, ...(opts.reviewBots ?? [])];
  cfg.approvalChecks = [...cfg.approvalChecks, ...(opts.approvalChecks ?? [])];
  return cfg;
}
