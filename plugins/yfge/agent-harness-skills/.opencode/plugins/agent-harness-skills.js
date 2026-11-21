/**
 * Agent Harness Skills plugin for OpenCode.
 *
 * Injects a compact startup bootstrap so OpenCode agents discover the harness
 * methodology immediately, and registers this repository's skills directory
 * for runtimes that honor plugin config hooks.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BOOTSTRAP_MARKER = 'agent-harness-skills:bootstrap:v1';

let bootstrapCache;

const readTextIfExists = (filePath) => {
  try {
    return fs.readFileSync(filePath, 'utf8').trim();
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return '';
    }
    throw error;
  }
};

const buildBootstrapContext = (skillsDir) => {
  if (bootstrapCache !== undefined) {
    return bootstrapCache;
  }

  const indexPath = path.resolve(__dirname, '../../INDEX.md');
  const index = readTextIfExists(indexPath);
  const routing = index || [
    '# Skill Index',
    '',
    '- Start with `repo-harness-assessment` for existing repository harness work.',
    '- Load the matching Agent Harness Skill before substantive repository harness work.',
  ].join('\n');

  bootstrapCache = [
    `<!-- ${BOOTSTRAP_MARKER} -->`,
    'You have Agent Harness Skills available through this OpenCode plugin.',
    '',
    'Startup routing:',
    "- Use OpenCode's native skill tool to list skills, then load the relevant skill for substantive repository harness work.",
    `- Skills directory: ${skillsDir}`,
    '- For lightweight discussion, read-only inspection, or routing questions, use the index first and load a skill only if needed.',
    '- If native skill discovery is unavailable, read the relevant `SKILL.md` from that directory directly.',
    '- Keep guidance repo-neutral and follow the target repository validation rules before delivery.',
    '',
    routing,
  ].join('\n');

  return bootstrapCache;
};

const hasBootstrapContext = (systemParts) =>
  systemParts.some(
    (part) => typeof part === 'string' && part.includes(BOOTSTRAP_MARKER)
  );

export const AgentHarnessSkillsPlugin = async () => {
  const skillsDir = path.resolve(__dirname, '../../skills');

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },
    'experimental.chat.system.transform': async (_input, output) => {
      output.system = Array.isArray(output.system) ? output.system : [];
      if (hasBootstrapContext(output.system)) {
        return;
      }

      const bootstrap = buildBootstrapContext(skillsDir);
      const insertionIndex = output.system.length > 0 ? 1 : 0;
      output.system.splice(insertionIndex, 0, bootstrap);
    },
  };
};

export default AgentHarnessSkillsPlugin;
