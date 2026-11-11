import { enMessages } from "./locales/en.js";

export interface GoalProgressMessages {
  readonly phasePaused: string;
  readonly phaseCompleted: string;
  readonly phaseUsageLimit: string;
  readonly phaseBudgetLimit: string;
  readonly phaseNativeGoalBlocked: string;
  readonly phaseDetached: string;
  readonly phaseFinalVerification: string;
  readonly phaseTracking: string;
  readonly statusCompletedVerified: string;
  readonly statusCompleted: string;
  readonly statusActive: string;
  readonly statusBlocked: string;
  readonly statusPending: string;
  readonly visibleSuccess: string;
  readonly visibleWorking: string;
  readonly visiblePending: string;
  readonly visibleBlocked: string;
  readonly visiblePaused: string;
  readonly current: string;
  readonly currentPaused: string;
  readonly currentBlocked: string;
  readonly goalCompleted: string;
  readonly waitingNativeGoalRecovery: string;
  readonly completionCount: (completed: number, total: number) => string;
  readonly placementSettingsTriggerLabel: string;
  readonly placementSettingsLabel: string;
  readonly displaySettings: string;
  readonly versionSection: string;
  readonly effects: string;
  readonly animationEffects: string;
  readonly fixedDisplay: string;
  readonly floatingDisplay: string;
  readonly currentVersion: string;
  readonly checkUpdates: string;
  readonly upToDate: string;
  readonly checkingUpdates: string;
  readonly newVersion: string;
  readonly checkFailed: string;
  readonly restartPending: string;
  readonly viewUpdateNotes: string;
  readonly updateAvailable: string;
  readonly updateNow: string;
  readonly preparingUpdate: string;
  readonly downloading: string;
  readonly downloadingUnknown: string;
  readonly verifyingUpdate: string;
  readonly installingUpdate: string;
  readonly downloadFailed: string;
  readonly updateFailed: string;
  readonly restartReady: string;
  readonly restartingUpdate: string;
  readonly restartNow: string;
  readonly restartLater: string;
  readonly overallLabel: string;
  readonly overallProgress: string;
  readonly composerShorterAutoExpand: string;
  readonly spaceRestoredAutoExpand: string;
  readonly expandProgress: string;
  readonly collapseProgress: string;
  readonly expand: string;
  readonly collapse: string;
  readonly floatingProgress: string;
  readonly objectiveList: string;
  readonly optionalObjectives: string;
  readonly optional: string;
  readonly emptyObjectives: string;
  readonly objectiveProgress: (title: string) => string;
  readonly scopeUpdated: (reason: string) => string;
  readonly progressCorrected: (reason: string) => string;
  readonly preparingReadGoal: string;
  readonly preparingBaseline: string;
  readonly preparingObjectives: string;
  readonly preparingCopy: string;
  readonly unavailableTitle: string;
  readonly unavailableCopy: string;
  readonly retryProgress: string;
  readonly retry: string;
  readonly closeProgress: string;
  readonly tokenUnavailable: string;
  readonly tokenInputOutput: (input: string, output: string) => string;
  readonly tokenTotal: (total: string) => string;
}

export type SerializedGoalProgressMessages = {
  readonly [Key in keyof GoalProgressMessages]: string;
};

export interface GoalProgressLocaleCatalogPayload {
  readonly key: string;
  readonly messages: SerializedGoalProgressMessages;
}

export interface GoalProgressLocaleContext {
  readonly locale: string;
  readonly messages: GoalProgressMessages;
}

export const GOAL_PROGRESS_LOCALE_PLACEHOLDER_0 = "\uE000";
export const GOAL_PROGRESS_LOCALE_PLACEHOLDER_1 = "\uE001";

export const GOAL_PROGRESS_SUPPORTED_LOCALES = Object.freeze([
  "en-US",
  "am",
  "ar",
  "bg-BG",
  "bn-BD",
  "bs-BA",
  "ca-ES",
  "cs-CZ",
  "da-DK",
  "de-DE",
  "el-GR",
  "es-419",
  "es-ES",
  "et-EE",
  "fa",
  "fi-FI",
  "fr-CA",
  "fr-FR",
  "gu-IN",
  "hi-IN",
  "hr-HR",
  "hu-HU",
  "hy-AM",
  "id-ID",
  "is-IS",
  "it-IT",
  "ja-JP",
  "ka-GE",
  "kk",
  "kn-IN",
  "ko-KR",
  "lt",
  "lv-LV",
  "mk-MK",
  "ml",
  "mn",
  "mr-IN",
  "ms-MY",
  "my-MM",
  "nb-NO",
  "nl-NL",
  "pa",
  "pl-PL",
  "pt-BR",
  "pt-PT",
  "ro-RO",
  "ru-RU",
  "sk-SK",
  "sl-SI",
  "so-SO",
  "sq-AL",
  "sr-RS",
  "sv-SE",
  "sw-TZ",
  "ta-IN",
  "te-IN",
  "th-TH",
  "tl",
  "tr-TR",
  "uk-UA",
  "ur",
  "vi-VN",
  "zh-CN",
  "zh-HK",
  "zh-TW",
] as const);

const supportedLocaleSet = new Set<string>(GOAL_PROGRESS_SUPPORTED_LOCALES);
const messageKeys = Object.freeze(Object.keys(enMessages) as Array<keyof GoalProgressMessages>);
const registeredCatalogs = new Map<string, GoalProgressMessages>([["en-US", enMessages]]);
const localeListeners = new Set<() => void>();

const baseCatalogKeys = new Map<string, string>();
for (const locale of GOAL_PROGRESS_SUPPORTED_LOCALES) {
  const language = new Intl.Locale(locale).language;
  if (!baseCatalogKeys.has(language)) {
    baseCatalogKeys.set(language, locale);
  }
}

function canonicalLocale(rawLocale: string): string | null {
  const requested = rawLocale.trim();
  if (!requested) {
    return null;
  }
  try {
    return Intl.getCanonicalLocales(requested)[0] ?? null;
  } catch {
    return null;
  }
}

function catalogKeyForCanonicalLocale(locale: string): string | null {
  if (supportedLocaleSet.has(locale)) {
    return locale;
  }
  const parsed = new Intl.Locale(locale);
  const { language, region } = parsed;
  if (language === "en") {
    return "en-US";
  }
  if (language === "zh") {
    const maximized = parsed.maximize();
    if (maximized.script === "Hans") {
      return "zh-CN";
    }
    return maximized.region === "HK" || maximized.region === "MO" ? "zh-HK" : "zh-TW";
  }
  if (language === "es") {
    return region && region !== "ES" ? "es-419" : "es-ES";
  }
  if (language === "fr") {
    return region === "CA" ? "fr-CA" : "fr-FR";
  }
  if (language === "pt") {
    return region === "BR" ? "pt-BR" : "pt-PT";
  }
  if (language === "no") {
    return "nb-NO";
  }
  return baseCatalogKeys.get(language) ?? null;
}

function isSerializedMessagesRecord(value: unknown): value is SerializedGoalProgressMessages {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const record = value as Record<string, unknown>;
  if (Object.keys(record).length !== messageKeys.length) {
    return false;
  }
  for (const key of messageKeys) {
    const field = record[key];
    if (typeof field !== "string" || field.length === 0 || field.length > 500) {
      return false;
    }
  }
  return true;
}

export function isGoalProgressLocaleCatalogPayload(
  value: unknown,
): value is GoalProgressLocaleCatalogPayload {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.key === "string" &&
    supportedLocaleSet.has(candidate.key) &&
    isSerializedMessagesRecord(candidate.messages)
  );
}

function deserializeMessages(raw: SerializedGoalProgressMessages): GoalProgressMessages {
  return Object.freeze({
    ...raw,
    completionCount: (completed: number, total: number) =>
      raw.completionCount
        .replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, String(completed))
        .replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_1, String(total)),
    objectiveProgress: (title: string) =>
      raw.objectiveProgress.replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, title),
    scopeUpdated: (reason: string) =>
      raw.scopeUpdated.replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, reason),
    progressCorrected: (reason: string) =>
      raw.progressCorrected.replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, reason),
    tokenInputOutput: (input: string, output: string) =>
      raw.tokenInputOutput
        .replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, input)
        .replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_1, output),
    tokenTotal: (total: string) =>
      raw.tokenTotal.replaceAll(GOAL_PROGRESS_LOCALE_PLACEHOLDER_0, total),
  });
}

export function registerGoalProgressLocaleCatalog(
  catalogKey: string,
  messagesInput: GoalProgressMessages | SerializedGoalProgressMessages,
): boolean {
  if (!supportedLocaleSet.has(catalogKey)) {
    return false;
  }
  const messages =
    typeof messagesInput.completionCount === "function"
      ? (messagesInput as GoalProgressMessages)
      : isSerializedMessagesRecord(messagesInput)
        ? deserializeMessages(messagesInput)
        : null;
  if (!messages) {
    return false;
  }
  registeredCatalogs.set(catalogKey, messages);
  for (const listener of localeListeners) {
    listener();
  }
  return true;
}

export function hasGoalProgressLocaleCatalog(catalogKey: string): boolean {
  return registeredCatalogs.has(catalogKey);
}

export function onGoalProgressLocaleCatalogRegistered(listener: () => void): () => void {
  localeListeners.add(listener);
  return () => {
    localeListeners.delete(listener);
  };
}

export function resolveGoalProgressLocaleCatalogKey(rawLocale: string): string | null {
  const locale = canonicalLocale(rawLocale);
  return locale ? catalogKeyForCanonicalLocale(locale) : null;
}

export function resolveGoalProgressLocale(rawLocale: string): GoalProgressLocaleContext {
  const locale = canonicalLocale(rawLocale);
  const catalogKey = locale ? catalogKeyForCanonicalLocale(locale) : null;
  if (!locale || !catalogKey) {
    return {
      locale: "en",
      messages: enMessages,
    };
  }
  return {
    locale,
    messages: registeredCatalogs.get(catalogKey) ?? enMessages,
  };
}

if (typeof globalThis !== "undefined") {
  const initialLocales = (
    globalThis as {
      __CODEX_GOAL_PROGRESS_INITIAL_LOCALES__?: unknown;
    }
  ).__CODEX_GOAL_PROGRESS_INITIAL_LOCALES__;
  if (Array.isArray(initialLocales)) {
    for (const entry of initialLocales) {
      if (isGoalProgressLocaleCatalogPayload(entry)) {
        registerGoalProgressLocaleCatalog(entry.key, entry.messages);
      }
    }
  }
}
