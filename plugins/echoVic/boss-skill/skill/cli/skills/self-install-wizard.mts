import * as fs from 'node:fs';

import { cancel, intro, log, outro, spinner } from '@clack/prompts';

import { printBanner } from './banner.mts';
import { readInstalledVersion } from './installer.mts';
import { PROMPT_CANCELLED, searchMultiselect } from './search-multiselect.mts';

export interface WizardAgent {
  name: string;
  detected: boolean;
  dest: string;
  method: 'copy' | 'codex-copy' | 'plugin';
  /** performs the actual install; throws on failure */
  install: () => void;
  /** extra actions performed alongside the copy (hooks merge, plugin registration) */
  sideEffects: string[];
  /** lines shown after a successful install (e.g. plugin usage hint) */
  postInstallNote?: string[];
}

const CANCELLED = 130;

// Self-install wizard styled after `npx skills add`: pixel banner, single-skill
// summary, then a search-multiselect with detected agents locked as
// "always included" and the remaining agents searchable.
export async function runInstallWizard({
  version,
  agents,
}: {
  version: string;
  agents: WizardAgent[];
}): Promise<number> {
  printBanner();
  intro(`@blade-ai/boss-skill v${version}`);

  log.success('Found 1 skill');
  log.info('Skill: boss');
  log.message('BMAD Harness Engineer — pluggable pipeline skill for coding agents.');

  const agentSpin = spinner();
  agentSpin.start('Loading agents…');
  const detected = agents.filter((agent) => agent.detected);
  const others = agents.filter((agent) => !agent.detected);
  agentSpin.stop(`${agents.length} agents`);

  const picked = await searchMultiselect({
    message: 'Which agents do you want to install to?',
    items: others.map((agent) => ({ value: agent.name, label: agent.name, hint: agent.dest })),
    lockedSection: {
      title: 'Detected agents',
      items: detected.map((agent) => ({
        value: agent.name,
        label: agent.name,
      })),
    },
    required: true,
  });
  if (picked === PROMPT_CANCELLED) {
    cancel('Install cancelled.');
    return CANCELLED;
  }

  const targets = [...detected, ...others.filter((agent) => picked.includes(agent.name))];
  if (targets.length === 0) {
    outro('Nothing to do.');
    return 0;
  }

  const failures: { agent: WizardAgent; error: string }[] = [];
  for (const agent of targets) {
    const previous =
      agent.method !== 'plugin' && fs.existsSync(agent.dest)
        ? readInstalledVersion(agent.dest)
        : undefined;
    const spin = spinner();
    spin.start(`Installing to ${agent.name}…`);
    try {
      agent.install();
      const upgrade = previous ? ` (v${previous} → v${version})` : '';
      spin.stop(`✅ ${agent.name}${upgrade}`);
      for (const effect of agent.sideEffects) {
        log.message(`   ↳ ${effect}`);
      }
      if (agent.postInstallNote && agent.postInstallNote.length > 0) {
        log.info(agent.postInstallNote.join('\n'));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      spin.error(`❌ ${agent.name}: ${message}`);
      failures.push({ agent, error: message });
    }
  }

  const succeeded = targets.length - failures.length;
  if (failures.length > 0) {
    log.error(`Failed: ${failures.map((failure) => failure.agent.name).join(', ')}`);
    outro(
      `Installed to ${succeeded}/${targets.length} agent(s). Retry failed agents with: boss-skill install --yes`,
    );
    return 1;
  }

  outro('Done! Restart your agent or start a new session to pick up boss-skill.');
  return 0;
}
