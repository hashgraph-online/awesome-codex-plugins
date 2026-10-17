import fs from 'node:fs';
import path from 'node:path';
import * as runtime from '../../cli/runtime/application/pipeline.mts';
import {
  isAgentReportStatus,
  toPipelineAgentStatus,
} from '../../cli/runtime/domain/agent-report.mts';
import { AGENT_STAGE_MAP, findActiveFeature, readExecJson } from '../lib/boss-utils.js';
import { emitProgress } from '../lib/progress-emitter.js';

/**
 * 读取子代理上报的结构化状态。
 *
 * 状态的权威来源是 `boss runtime report-agent-status` 写入的事件流 —— 子代理调用该命令时
 * 枚举已在工具层校验过。此处只从 hook 输入里取已解析好的结构化字段，
 * 不再用正则从自然语言消息里提取（旧实现把 message 截断到前 500 字符，
 * 而状态块在末尾，导致较长的成功回复被误判为 failed）。
 */
function readReportedStatus(input) {
  const candidates = [
    input.structured_output,
    input.structuredOutput,
    input.agent_status,
    input.agentStatus,
  ];

  for (const candidate of candidates) {
    if (!candidate) continue;
    if (typeof candidate === 'string') {
      if (isAgentReportStatus(candidate)) {
        return { status: candidate, reason: '' };
      }
      continue;
    }
    if (typeof candidate === 'object') {
      const status = candidate.status;
      if (isAgentReportStatus(status)) {
        return {
          status,
          reason: typeof candidate.reason === 'string' ? candidate.reason : '',
        };
      }
    }
  }

  return null;
}

function run(rawInput) {
  const input = JSON.parse(rawInput);
  const agentType = input.agent_type || '';
  const agentId = input.agent_id || '';
  const lastMsg = (input.last_assistant_message || '').slice(0, 500);
  const cwd = input.cwd || '';

  const active = findActiveFeature(cwd);

  const logDirName = active ? active.feature : '.harness-logs';
  const logDir = path.join(cwd, '.boss', logDirName, '.meta');

  try {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
  } catch (err) {
    process.stderr.write('[boss-skill] subagent-stop/mkdirSync: ' + err.message + '\n');
    return '';
  }

  const logFile = path.join(logDir, 'agent-log.jsonl');
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  const parsedStatus = readReportedStatus(input) || { status: '', reason: '' };
  const entry = JSON.stringify({
    timestamp: now,
    agentType,
    agentId,
    event: 'stop',
    summary: lastMsg,
    status: parsedStatus.status || '',
    reason: parsedStatus.reason || '',
  });

  try {
    fs.appendFileSync(logFile, entry + '\n', 'utf8');
  } catch (err) {
    process.stderr.write('[boss-skill] subagent-stop/appendLog: ' + err.message + '\n');
  }

  // Emit AgentCompleted/AgentFailed event if this is a known boss agent
  if (active && AGENT_STAGE_MAP[agentType]) {
    const execData = readExecJson(cwd, active.feature);
    if (execData) {
      let currentStage = '';
      const stages = execData.stages || {};
      for (const sKey of Object.keys(stages).sort((a, b) => Number(a) - Number(b))) {
        const stage = stages[sKey] || {};
        if (stage.status === 'running') {
          currentStage = sKey;
          break;
        }
      }

      // 未上报状态时不写入事件：状态的权威来源是 report-agent-status 命令。
      // 缺失应表现为「没推进」而非「失败」，否则会把未按协议上报的成功执行误记为失败。
      if (currentStage && parsedStatus.status) {
        const agentStatus = toPipelineAgentStatus(parsedStatus.status);

        emitProgress(cwd, active.feature, {
          type: 'agent-complete',
          data: { agent: agentType, stage: parseInt(currentStage, 10), status: agentStatus },
        });

        const failureReason = parsedStatus.reason || parsedStatus.status || '';
        try {
          runtime.updateAgent(active.feature, currentStage, agentType, agentStatus, {
            cwd,
            reason: agentStatus === 'failed' ? failureReason : '',
          });
        } catch (err) {
          process.stderr.write('[boss-skill] subagent-stop/update-agent: ' + err.message + '\n');
        }
      }
    }
  }

  return '';
}

export { readReportedStatus, run };
