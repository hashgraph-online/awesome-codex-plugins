import {
  MODELSCOPE_DENYLIST,
  MODELSCOPE_PREFERRED_MODELS
} from "../model-preferences.mjs";

export const MODELSCOPE_MODELS_URL = "https://api-inference.modelscope.cn/v1/models";

export async function fetchModelScopeCatalog({
  fetchImpl = fetch,
  fetchedAt = new Date().toISOString()
} = {}) {
  const response = await fetchImpl(MODELSCOPE_MODELS_URL);
  if (!response.ok) {
    throw new Error(`ModelScope catalog request failed with status ${response.status}.`);
  }
  return normalizeModelScopeCatalogPayload(await response.json(), { fetchedAt });
}

export function normalizeModelScopeCatalogPayload(payload, { fetchedAt }) {
  const items = Array.isArray(payload?.data) ? payload.data : [];
  const entries = items
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => typeof item?.id === "string")
    .filter(({ item }) => !MODELSCOPE_DENYLIST.includes(item.id))
    .filter(({ item }) => isVisionCapableModel(item.id))
    .map(({ item, index }) => ({
      provider: "modelscope",
      model: item.id,
      source: MODELSCOPE_MODELS_URL,
      fetchedAt,
      supportsVision: true,
      created: item.created ?? null,
      ownedBy: item.owned_by ?? null,
      _rank: modelRank(item.id),
      _index: index
    }))
    .sort((left, right) => {
      if (left._rank !== right._rank) {
        return left._rank - right._rank;
      }
      return left._index - right._index;
    })
    .map(stripInternalFields);

  return entries;
}

function stripInternalFields(entry) {
  const { _rank, _index, ...publicEntry } = entry;
  return publicEntry;
}

function modelRank(modelId) {
  const preferredIndex = MODELSCOPE_PREFERRED_MODELS.indexOf(modelId);
  if (preferredIndex >= 0) {
    return preferredIndex;
  }
  return MODELSCOPE_PREFERRED_MODELS.length + 100;
}

function isVisionCapableModel(modelId) {
  if (MODELSCOPE_PREFERRED_MODELS.includes(modelId)) {
    return true;
  }

  return /(vl|vision|ocr|gui-owl|internvl|qvq|omni)/iu.test(modelId);
}
