export const DASHSCOPE_VISION_DOCS_URL = "https://help.aliyun.com/zh/model-studio/vision-model";

export const DASHSCOPE_FALLBACK_MODELS = [
  { model: "qwen3.6-plus" },
  { model: "qwen3.6-plus-2026-04-02" },
  { model: "qwen3.6-flash" },
  { model: "qwen-vl-ocr" }
];

export async function fetchDashScopeCatalog({
  fetchImpl = fetch,
  fetchedAt = new Date().toISOString()
} = {}) {
  const response = await fetchImpl(DASHSCOPE_VISION_DOCS_URL);
  if (!response.ok) {
    throw new Error(`DashScope catalog request failed with status ${response.status}.`);
  }

  const html = await response.text();
  const parsed = parseDashScopeVisionModels(html, { fetchedAt });
  if (parsed.length > 0) {
    return parsed;
  }

  return DASHSCOPE_FALLBACK_MODELS.map((entry) => ({
    provider: "dashscope",
    model: entry.model,
    source: "dashscope_fallback",
    fetchedAt,
    supportsVision: true
  }));
}

export function parseDashScopeVisionModels(html, { fetchedAt }) {
  const matches = html.matchAll(/<code[^>]*>([^<]+)<\/code>/giu);
  const seen = new Set();
  const models = [];

  for (const match of matches) {
    const model = match[1].trim();
    if (!isDashScopeVisionModel(model) || seen.has(model)) {
      continue;
    }
    seen.add(model);
    models.push({
      provider: "dashscope",
      model,
      source: DASHSCOPE_VISION_DOCS_URL,
      fetchedAt,
      supportsVision: true
    });
  }

  return models;
}

function isDashScopeVisionModel(model) {
  return /^(qwen3\.6-(plus|flash)(-\d{4}-\d{2}-\d{2})?|qwen-vl-ocr)$/u.test(model);
}
