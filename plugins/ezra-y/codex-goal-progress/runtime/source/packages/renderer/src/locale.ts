import {
  GOAL_PROGRESS_LOCALE_PLACEHOLDER_0,
  GOAL_PROGRESS_LOCALE_PLACEHOLDER_1,
  GOAL_PROGRESS_SUPPORTED_LOCALES,
  type GoalProgressLocaleCatalogPayload,
  type GoalProgressLocaleContext,
  type GoalProgressMessages,
  registerGoalProgressLocaleCatalog,
  resolveGoalProgressLocale,
  resolveGoalProgressLocaleCatalogKey,
  type SerializedGoalProgressMessages,
} from "./locale-core.js";
import { goalProgressCatalogs } from "./locales/index.js";

for (const [key, messages] of goalProgressCatalogs) {
  registerGoalProgressLocaleCatalog(key, messages);
}

const serializedCatalogCache = new Map<string, GoalProgressLocaleCatalogPayload>();

function serializeMessages(messages: GoalProgressMessages): SerializedGoalProgressMessages {
  const placeholderNumber0 = GOAL_PROGRESS_LOCALE_PLACEHOLDER_0 as unknown as number;
  const placeholderNumber1 = GOAL_PROGRESS_LOCALE_PLACEHOLDER_1 as unknown as number;
  return Object.freeze({
    ...messages,
    completionCount: messages.completionCount(placeholderNumber0, placeholderNumber1),
    objectiveProgress: messages.objectiveProgress(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0),
    scopeUpdated: messages.scopeUpdated(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0),
    progressCorrected: messages.progressCorrected(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0),
    tokenInputOutput: messages.tokenInputOutput(
      GOAL_PROGRESS_LOCALE_PLACEHOLDER_0,
      GOAL_PROGRESS_LOCALE_PLACEHOLDER_1,
    ),
    tokenTotal: messages.tokenTotal(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0),
  });
}

export function serializeGoalProgressLocaleCatalog(
  rawLocale: string,
): GoalProgressLocaleCatalogPayload | null {
  const key = resolveGoalProgressLocaleCatalogKey(rawLocale);
  if (!key) {
    return null;
  }
  const cached = serializedCatalogCache.get(key);
  if (cached) {
    return cached;
  }
  const messages = goalProgressCatalogs.get(key);
  if (!messages) {
    return null;
  }
  const payload = Object.freeze({
    key,
    messages: serializeMessages(messages),
  });
  serializedCatalogCache.set(key, payload);
  return payload;
}

export function serializeAllGoalProgressLocaleCatalogs(): readonly GoalProgressLocaleCatalogPayload[] {
  const payloads: GoalProgressLocaleCatalogPayload[] = [];
  for (const locale of GOAL_PROGRESS_SUPPORTED_LOCALES) {
    if (locale === "en-US") {
      continue;
    }
    const payload = serializeGoalProgressLocaleCatalog(locale);
    if (payload) {
      payloads.push(payload);
    }
  }
  return payloads;
}

export {
  GOAL_PROGRESS_SUPPORTED_LOCALES,
  type GoalProgressLocaleCatalogPayload,
  type GoalProgressLocaleContext,
  type GoalProgressMessages,
  resolveGoalProgressLocale,
  resolveGoalProgressLocaleCatalogKey,
  type SerializedGoalProgressMessages,
};
