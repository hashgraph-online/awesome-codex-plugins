import { GOAL_PROGRESS_SUPPORTED_LOCALES, goalProgressCatalogs } from "./locales/index.js";

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

export { GOAL_PROGRESS_SUPPORTED_LOCALES };

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

function catalogKeyForLocale(locale: string): string | null {
  if (goalProgressCatalogs.has(locale)) {
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

export interface GoalProgressLocaleContext {
  readonly locale: string;
  readonly messages: GoalProgressMessages;
}

export function resolveGoalProgressLocale(rawLocale: string): GoalProgressLocaleContext {
  const locale = canonicalLocale(rawLocale);
  const catalogKey = locale ? catalogKeyForLocale(locale) : null;
  if (!locale || !catalogKey) {
    return {
      locale: "en",
      messages: goalProgressCatalogs.get("en-US") as GoalProgressMessages,
    };
  }
  return {
    locale,
    messages: goalProgressCatalogs.get(catalogKey) as GoalProgressMessages,
  };
}
