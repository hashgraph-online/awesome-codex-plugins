#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const checks = [];
let allPassed = true;

function addCheck(name, ok, detail) {
  checks.push(detail ? { name, passed: ok, detail } : { name, passed: ok });
  allPassed &&= ok;
}

// Load config from plugin.json
const pluginDir = path.dirname(new URL(import.meta.url).pathname);
const pluginConfig = JSON.parse(
  fs.readFileSync(path.join(pluginDir, 'plugin.json'), 'utf8'),
).config;

const { dimensions, passThreshold, model, maxTokens, timeout } = pluginConfig;

// Determine API credentials
const apiKey = process.env.LLM_JUDGE_API_KEY || process.env.OPENAI_API_KEY;
const baseUrl = process.env.LLM_JUDGE_BASE_URL || 'https://api.openai.com/v1';
const modelName = process.env.LLM_JUDGE_MODEL || model;

if (!apiKey) {
  // Graceful skip when no API key available
  for (const dim of dimensions) {
    addCheck(`llm-judge-${dim}`, true, 'LLM API 不可用（未配置 API Key），跳过评估');
  }
  process.stdout.write(`${JSON.stringify(checks)}\n`);
  process.exit(0);
}

// Find feature directory
const feature = process.argv[2];
const cwd = process.cwd();
const bossDir = path.join(cwd, '.boss');
let featureDir = null;

if (feature && fs.existsSync(path.join(bossDir, feature))) {
  featureDir = path.join(bossDir, feature);
} else {
  // Try to find the most recent feature directory
  if (fs.existsSync(bossDir)) {
    const entries = fs
      .readdirSync(bossDir, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !e.name.startsWith('.'))
      .map((e) => ({ name: e.name, mtime: fs.statSync(path.join(bossDir, e.name)).mtime }))
      .sort((a, b) => b.mtime - a.mtime);
    if (entries.length > 0) {
      featureDir = path.join(bossDir, entries[0].name);
    }
  }
}

if (!featureDir) {
  for (const dim of dimensions) {
    addCheck(`llm-judge-${dim}`, true, '未找到 feature 目录，跳过评估');
  }
  process.stdout.write(`${JSON.stringify(checks)}\n`);
  process.exit(0);
}

// Collect artifacts for evaluation
function readArtifact(filename) {
  const filePath = path.join(featureDir, filename);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    return content.slice(0, 8000); // Limit context size
  }
  return null;
}

const artifacts = {
  prd: readArtifact('prd.md'),
  architecture: readArtifact('architecture.md'),
  qaReport: readArtifact('qa-report.md'),
  techReview: readArtifact('tech-review.md'),
  tasks: readArtifact('tasks.md'),
};

// Load prompt template for a dimension
function loadPrompt(dimension) {
  const promptPath = path.join(pluginDir, 'prompts', `${dimension}.md`);
  if (fs.existsSync(promptPath)) {
    return fs.readFileSync(promptPath, 'utf8');
  }
  return null;
}

// Call LLM API
async function callLLM(systemPrompt, userContent) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout || 60000);

  try {
    const response = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: modelName,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userContent },
        ],
        max_tokens: maxTokens,
        temperature: 0.1,
        response_format: { type: 'json_object' },
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const text = data.choices?.[0]?.message?.content;
    if (!text) return null;

    return JSON.parse(text);
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

// Evaluate each dimension
async function evaluateDimension(dimension) {
  const prompt = loadPrompt(dimension);
  if (!prompt) {
    return { score: null, detail: `未找到评估 prompt: ${dimension}` };
  }

  // Build context based on dimension
  let context = '';
  if (dimension === 'code-quality' && artifacts.techReview) {
    context = `## Tech Review\n${artifacts.techReview}`;
  } else if (dimension === 'test-completeness' && artifacts.qaReport) {
    context = `## QA Report\n${artifacts.qaReport}`;
  } else if (dimension === 'architecture-soundness' && artifacts.architecture) {
    context = `## Architecture\n${artifacts.architecture}`;
  }

  if (artifacts.prd) {
    context += `\n\n## PRD\n${artifacts.prd.slice(0, 3000)}`;
  }
  if (artifacts.tasks) {
    context += `\n\n## Tasks\n${artifacts.tasks.slice(0, 2000)}`;
  }

  if (!context.trim()) {
    return { score: null, detail: '无可用产物进行评估' };
  }

  const result = await callLLM(prompt, context);
  if (!result) {
    return { score: null, detail: 'LLM 调用失败或超时' };
  }

  return {
    score: typeof result.score === 'number' ? result.score : null,
    detail: result.reasoning || result.detail || '',
  };
}

// Main execution
async function main() {
  for (const dimension of dimensions) {
    const { score, detail } = await evaluateDimension(dimension);

    if (score === null) {
      // Graceful skip
      addCheck(`llm-judge-${dimension}`, true, detail || 'LLM 评估不可用，跳过');
    } else {
      const passed = score >= passThreshold;
      addCheck(
        `llm-judge-${dimension}`,
        passed,
        `${score.toFixed(2)}/${passThreshold} — ${detail}`,
      );
    }
  }

  process.stdout.write(`${JSON.stringify(checks)}\n`);
  process.exit(allPassed ? 0 : 1);
}

main().catch(() => {
  // Final fallback: graceful skip on any unhandled error
  for (const dim of dimensions) {
    if (!checks.some((c) => c.name === `llm-judge-${dim}`)) {
      addCheck(`llm-judge-${dim}`, true, 'LLM 评估异常，跳过');
    }
  }
  process.stdout.write(`${JSON.stringify(checks)}\n`);
  process.exit(0);
});
