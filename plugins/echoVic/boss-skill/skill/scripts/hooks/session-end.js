import fs from 'node:fs';
import path from 'node:path';
import { renderMarkdown } from '../../cli/runtime/report/render-markdown.mts';
import { buildSummaryModel } from '../../cli/runtime/report/summary-model.mts';
import { writeJson } from '../lib/boss-utils.js';

function run(rawInput) {
  const input = JSON.parse(rawInput);
  const cwd = input.cwd || '';

  const bossDir = path.join(cwd, '.boss');
  if (!fs.existsSync(bossDir)) return '';

  let entries;
  try {
    entries = fs.readdirSync(bossDir, { withFileTypes: true });
  } catch (err) {
    process.stderr.write('[boss-skill] session-end/readdirSync: ' + err.message + '\n');
    return '';
  }

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const execJsonPath = path.join(bossDir, entry.name, '.meta', 'execution.json');
    if (!fs.existsSync(execJsonPath)) continue;

    let data;
    try {
      data = JSON.parse(fs.readFileSync(execJsonPath, 'utf8'));
    } catch (err) {
      process.stderr.write('[boss-skill] session-end/readExecJson: ' + err.message + '\n');
      continue;
    }

    const status = data.status || 'unknown';
    const feature = data.feature || entry.name;

    if (status === 'running' || status === 'completed' || status === 'failed') {
      const stages = data.stages || {};
      const stagesSummary = {};
      for (const sKey of Object.keys(stages).sort((a, b) => Number(a) - Number(b))) {
        const stage = stages[sKey] || {};
        stagesSummary[sKey] = {
          name: stage.name || 'unknown',
          status: stage.status || 'unknown',
        };
      }

      const sessionState = {
        feature,
        pipelineStatus: status,
        stagesSummary,
        timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
        cwd,
      };

      const sessionStatePath = path.join(cwd, '.boss', '.session-state.json');
      try {
        writeJson(sessionStatePath, sessionState);
      } catch (err) {
        process.stderr.write('[boss-skill] session-end/writeSessionState: ' + err.message + '\n');
      }

      try {
        const reportPath = path.join(cwd, '.boss', feature, 'summary-report.md');
        const model = buildSummaryModel(feature, { cwd });
        fs.writeFileSync(reportPath, renderMarkdown(model), 'utf8');
      } catch (err) {
        process.stderr.write('[boss-skill] session-end/generateReport: ' + err.message + '\n');
      }
    }
  }

  return '';
}

export { run };
