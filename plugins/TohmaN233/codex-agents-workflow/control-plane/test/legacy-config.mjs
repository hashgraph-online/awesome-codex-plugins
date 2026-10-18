import { readFile, writeFile } from 'node:fs/promises';
import { LEGACY_CONFIG_VERSION, loadConfig } from '../lib/config.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

// Explicit historical fixtures exercise compatibility; release defaults are current.
const historicalPipelines = [
  {
    "id": "implementation-with-review",
    "name": "Implementation with independent review",
    "enabled": false,
    "description": "Run a bounded implementation stage followed by a separate read-only review stage.",
    "route": "full",
    "tags": [
      "implementation",
      "review",
      "two-stage",
      "default"
    ],
    "stages": [
      {
        "id": "implementation",
        "role": "implementer",
        "provider_id": "native-luna",
        "access": "bounded_write",
        "requires_user_approval": false,
        "template": "ROLE\nImplement the settled bounded change. Stay inside the owned paths and preserve concurrent work.\n\nOBJECTIVE\n{{task}}\n\nCONTEXT\n{{context}}\n\nCONSTRAINTS AND OWNERSHIP\n{{constraints}}\n\nVERIFICATION\n{{verification}}\n\nRETURN\nSTATUS: complete | partial | blocked\nCHANGES: file-by-file summary from the real diff\nVERIFIED: exact commands and concrete output\nJUDGMENT CALLS: material decisions or none\nGAPS: unfinished work or none"
      },
      {
        "id": "review",
        "role": "reviewer",
        "provider_id": "native-sol",
        "access": "read_only",
        "requires_user_approval": false,
        "template": "ROLE\nIndependently review the completed implementation. Remain read-only and do not fix your own findings.\n\nSTATED GOAL\n{{task}}\n\nIMPLEMENTATION RESULT AND CONTEXT\n{{context}}\n\nCONSTRAINTS AND ACCEPTANCE BOUNDARY\n{{constraints}}\n\nPRIMARY VERIFICATION EVIDENCE\n{{verification}}\n\nRETURN\nVERDICT: ship | fix-first | rethink\nBLOCKING FINDINGS: precise locations and required fixes, or none\nNON-BLOCKING RISKS: concise list, or none\nMISSING EVIDENCE: checks still required, or none\nRESIDUAL RISK: most important remaining risk, or none"
      }
    ]
  }
];
export async function legacyConfig(defaultConfigPath = DEFAULT_CONFIG_PATH) {
  const current = JSON.parse(await readFile(defaultConfigPath, 'utf8'));
  const { roles } = JSON.parse(await readFile(new URL('../builtin-role-definitions.json', import.meta.url), 'utf8'));
  const { workflow_store, legacy_mapping, strict_executor, ...retained } = current;
  return { ...retained, version: LEGACY_CONFIG_VERSION, task_types: [...roles, ...structuredClone(historicalPipelines)] };
}

export async function writeLegacyConfig(configPath, defaultConfigPath = DEFAULT_CONFIG_PATH) {
  const config = await legacyConfig(defaultConfigPath);
  await writeFile(configPath, JSON.stringify(config, null, 2) + '\n');
  return config;
}

export async function loadLegacyConfig({ configPath, defaultConfigPath = DEFAULT_CONFIG_PATH }) {
  await writeLegacyConfig(configPath, defaultConfigPath);
  return loadConfig({ configPath, defaultConfigPath });
}
