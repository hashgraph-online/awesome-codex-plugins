import { getOrRefreshCatalog } from "../catalog/cache.mjs";
import { fetchDashScopeCatalog } from "../catalog/dashscope.mjs";
import { fetchModelScopeCatalog } from "../catalog/modelscope.mjs";

export async function loadRoutingCatalogs({
  provider,
  modelscopeCatalog = null,
  dashscopeCatalog = null,
  refresh = false,
  ttlSeconds = 3600,
  cacheDir = null,
  cacheCatalog = getOrRefreshCatalog,
  loadModelScopeCatalog = fetchModelScopeCatalog,
  loadDashScopeCatalog = fetchDashScopeCatalog
}) {
  let activeModelScopeCatalog = normalizeProvidedCatalog(modelscopeCatalog);
  let activeDashScopeCatalog = normalizeProvidedCatalog(dashscopeCatalog);

  if (shouldLoadModelScopeCatalog({ provider })) {
    activeModelScopeCatalog =
      activeModelScopeCatalog ??
      (await loadCatalog({
        cacheDir,
        cacheKey: "modelscope",
        ttlSeconds,
        refresh,
        cacheCatalog,
        loader: loadModelScopeCatalog
      }));
  } else {
    activeModelScopeCatalog ??= [];
  }

  if (shouldLoadDashScopeCatalog({ provider })) {
    activeDashScopeCatalog =
      activeDashScopeCatalog ??
      (await loadCatalog({
        cacheDir,
        cacheKey: "dashscope",
        ttlSeconds,
        refresh,
        cacheCatalog,
        loader: loadDashScopeCatalog
      }));
  } else {
    activeDashScopeCatalog ??= [];
  }

  return {
    modelscopeCatalog: activeModelScopeCatalog,
    dashscopeCatalog: activeDashScopeCatalog
  };
}

function shouldLoadModelScopeCatalog({ provider }) {
  return provider === "modelscope";
}

function shouldLoadDashScopeCatalog({ provider }) {
  return provider !== "modelscope";
}

async function loadCatalog({
  cacheDir,
  cacheKey,
  ttlSeconds,
  refresh,
  cacheCatalog,
  loader
}) {
  const loadFreshCatalog = async () => loader({ fetchedAt: new Date().toISOString() });

  if (!cacheDir) {
    return loadFreshCatalog();
  }

  const record = await cacheCatalog({
    cacheDir,
    cacheKey,
    ttlSeconds,
    refresh,
    loader: loadFreshCatalog
  });

  return record.items;
}

function normalizeProvidedCatalog(catalog) {
  return Array.isArray(catalog) ? catalog : null;
}
