import { DEFAULT_CATALOG_TTL_SECONDS } from "./config.mjs";
import { runLocalOcr } from "./ocr/local.mjs";
import { DASHSCOPE_DEFAULT_MODEL, isDeniedModel } from "./model-preferences.mjs";
import { runDashScopeVisionInference } from "./providers/dashscope.mjs";
import { runModelScopeVisionInference } from "./providers/modelscope.mjs";
import { loadRoutingCatalogs } from "./runtime/catalogs.mjs";

export function buildRoutePlan({
  profile,
  provider = null,
  model = null,
  modelscopeCatalog = [],
  dashscopeCatalog = []
}) {
  const activeModelScopeCatalog = Array.isArray(modelscopeCatalog) ? modelscopeCatalog : [];
  const activeDashScopeCatalog = Array.isArray(dashscopeCatalog) ? dashscopeCatalog : [];

  if (model && isDeniedModel(model)) {
    throw new Error(`Model ${model} is denylisted and cannot be selected.`);
  }

  if (!provider && isModelScopeStyleModel(model)) {
    throw new Error(
      `Model ${model} looks like a ModelScope id. Pass --provider=modelscope to use it explicitly.`
    );
  }

  const plan = [{ kind: "local_ocr" }];

  if (provider) {
    plan.push({
      kind: "remote",
      provider,
      model:
        model ??
        resolveProviderDefault(provider, {
          modelscopeCatalog: activeModelScopeCatalog,
          dashscopeCatalog: activeDashScopeCatalog
        })
    });
    return plan;
  }

  plan.push({
    kind: "remote",
    provider: "dashscope",
    model:
      model ??
      resolveProviderDefault("dashscope", {
        modelscopeCatalog: activeModelScopeCatalog,
        dashscopeCatalog: activeDashScopeCatalog
      })
  });
  return plan;
}

export async function runCaptchaRouter({
  profile,
  provider = null,
  model = null,
  inputPath,
  imageBuffer,
  modelscopeCatalog = null,
  dashscopeCatalog = null,
  refreshCatalog = false,
  catalogTtlSeconds = DEFAULT_CATALOG_TTL_SECONDS,
  catalogCacheDir = null,
  modelscopeConfig = {},
  dashscopeConfig = {},
  localOcr = runLocalOcr,
  modelscopeRunner = runModelScopeVisionInference,
  dashscopeRunner = runDashScopeVisionInference,
  catalogLoader = loadRoutingCatalogs
}) {
  const fallbackChain = [];
  let localConfidence = null;

  const localResult = await localOcr({ inputPath });
  localConfidence = localResult.confidence ?? null;
  if (localResult.success) {
    return {
      ...localResult,
      resolvedProvider: null,
      resolvedModel: null,
      fallbackChain,
      localConfidence
    };
  }

  fallbackChain.push({
    provider: "local_ocr",
    model: null,
    reason: localResult.reason ?? "local_failed"
  });

  const catalogs = await catalogLoader({
    provider,
    modelscopeCatalog,
    dashscopeCatalog,
    refresh: refreshCatalog,
    ttlSeconds: catalogTtlSeconds,
    cacheDir: catalogCacheDir
  });

  const plan = buildRoutePlan({
    profile,
    provider,
    model,
    modelscopeCatalog: catalogs.modelscopeCatalog,
    dashscopeCatalog: catalogs.dashscopeCatalog
  }).slice(1);

  for (const step of plan) {
    const runner = step.provider === "modelscope" ? modelscopeRunner : dashscopeRunner;
    const config = step.provider === "modelscope" ? modelscopeConfig : dashscopeConfig;
    const result = await runner({
      apiKey: config.apiKey,
      baseUrl: config.baseUrl,
      model: step.model,
      imageBuffer
    });

    if (result.success) {
      return {
        ...result,
        method: step.provider,
        fallbackChain,
        localConfidence
      };
    }

    fallbackChain.push({
      provider: step.provider,
      model: step.model,
      reason: result.reason ?? "remote_failed"
    });
  }

  return {
    success: false,
    text: null,
    method: "none",
    resolvedProvider: null,
    resolvedModel: null,
    fallbackChain,
    localConfidence
  };
}

function resolveProviderDefault(provider, { modelscopeCatalog, dashscopeCatalog }) {
  const activeModelScopeCatalog = Array.isArray(modelscopeCatalog) ? modelscopeCatalog : [];
  const activeDashScopeCatalog = Array.isArray(dashscopeCatalog) ? dashscopeCatalog : [];

  if (provider === "modelscope") {
    return activeModelScopeCatalog[0]?.model ?? null;
  }
  return activeDashScopeCatalog[0]?.model ?? DASHSCOPE_DEFAULT_MODEL;
}

function isModelScopeStyleModel(model) {
  return typeof model === "string" && model.includes("/");
}
