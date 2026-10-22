import { createCodexSession } from './codex-session.mjs';

export async function createManagedNativeSession(options) {
  return createCodexSession(options);
}
