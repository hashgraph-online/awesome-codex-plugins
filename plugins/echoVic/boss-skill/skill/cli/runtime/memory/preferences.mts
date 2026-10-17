import type { PersistedMemoryRecord } from './store.mts';

/**
 * 用户选择的确定性偏好聚合。
 *
 * 取代已删除的 knowledge/preference-extractor：不再外挂第二个 LLM 去"抽取"，
 * 而是对事件流中的 `UserChoiceRecorded` 事件做一次纯函数 fold。
 * 因此偏好记录与其余 memory 记录一样，是可从 `events.jsonl` 完整重放的派生视图。
 */

export interface UserChoiceEventData {
  choiceType: 'design-variant' | 'review-decision' | 'config-preference' | 'gate-override' | string;
  selected: string;
  options?: string[];
  reason?: string;
  agent?: string | null;
  stage?: number | null;
}

/** 选择类型 → 偏好类别。 */
const CHOICE_TYPE_TO_CATEGORY: Record<string, string> = {
  'design-variant': 'design-style',
  'review-decision': 'review-preference',
  'config-preference': 'config-preference',
  'gate-override': 'quality-threshold',
};

// 置信度演化：同一选择重复 → 升；同类别的对立选择 → 降。
const CONFIDENCE_START = 0.5;
const CONFIDENCE_INCREMENT = 0.2;
const CONFIDENCE_DECREMENT = 0.2;
const CONFIDENCE_MAX = 0.95;
const CONFIDENCE_MIN = 0.1;
const DECAY_START = 5;
const DECAY_MAX = 20;
const DECAY_MIN = 1;

function categoryFor(choiceType: string): string {
  return CHOICE_TYPE_TO_CATEGORY[choiceType] ?? 'general-preference';
}

function preferenceId(category: string, subject: string): string {
  // 保留 subject 的可区分性：ASCII 字母数字与连字符原样保留（转小写），
  // 其余字符（含全部 CJK）编码为其 Unicode 码点，避免不同的非 ASCII subject
  // 被 `replace(/[^a-z0-9-]/g, '-')` 统一抹除后塌缩成同一 id、进而被误判为重复确认。
  const encode = (value: string): string =>
    [...value]
      .map((char) =>
        /[a-z0-9-]/.test(char.toLowerCase())
          ? char.toLowerCase()
          : `u${char.codePointAt(0)!.toString(36)}`,
      )
      .join('');
  return `pref-${encode(category)}-${encode(subject)}`;
}

function buildSummary(data: UserChoiceEventData, confirmations: number): string {
  const reason = data.reason ? `（原因: ${data.reason}）` : '';
  const repeat = confirmations > 1 ? `（已确认${confirmations}次）` : '';
  const selected = data.selected;
  switch (data.choiceType) {
    case 'design-variant':
      return `用户偏好设计方案「${selected}」${reason}${repeat}`;
    case 'review-decision':
      return `用户在评审中选择了「${selected}」${reason}${repeat}`;
    case 'config-preference':
      return `用户偏好配置「${selected}」${reason}${repeat}`;
    case 'gate-override':
      return `用户覆盖了门禁决策：「${selected}」${reason}${repeat}`;
    default:
      return `用户选择了「${selected}」${reason}${repeat}`;
  }
}

interface UserChoiceEvent {
  id: number;
  type: string;
  timestamp: string;
  data?: Record<string, unknown>;
}

function normalizeChoice(data: Record<string, unknown> | undefined): UserChoiceEventData | null {
  if (!data) return null;
  const selected = typeof data.selected === 'string' ? data.selected : '';
  const choiceType = typeof data.choiceType === 'string' ? data.choiceType : '';
  if (!selected || !choiceType) return null;
  return {
    choiceType,
    selected,
    options: Array.isArray(data.options)
      ? data.options.filter((o): o is string => typeof o === 'string')
      : undefined,
    reason: typeof data.reason === 'string' ? data.reason : undefined,
    agent: typeof data.agent === 'string' ? data.agent : null,
    stage: typeof data.stage === 'number' ? data.stage : null,
  };
}

interface PreferenceAccumulator {
  record: PersistedMemoryRecord;
  confirmations: number;
}

/**
 * 对 `UserChoiceRecorded` 事件序列做一次 fold，产出偏好类 memory 记录。
 *
 * 语义（与被删除的 knowledge 版一致）：
 * - 同一 (类别, 选择) 再次出现 → confidence 增、decayScore 增、evidence 追加；
 * - 同类别下的其它选择被"顶掉" → 其 confidence、decayScore 递减。
 *
 * 纯函数：给定同一事件序列必得同一结果，因此可随 rebuildFeatureMemory 反复重放。
 */
export function extractPreferenceMemories(
  feature: string,
  events: UserChoiceEvent[],
): PersistedMemoryRecord[] {
  // key = 偏好 id；同时按 category 索引以便处理对立选择
  const byId = new Map<string, PreferenceAccumulator>();

  for (const event of events) {
    if (event.type !== 'UserChoiceRecorded') continue;
    const choice = normalizeChoice(event.data);
    if (!choice) continue;

    const category = categoryFor(choice.choiceType);
    const id = preferenceId(category, choice.selected);
    const timestamp = event.timestamp;
    const evidenceRef = `${feature}/${choice.choiceType}/${event.id}`;

    const existing = byId.get(id);
    if (existing) {
      existing.confirmations += 1;
      existing.record = {
        ...existing.record,
        confidence: Math.min(CONFIDENCE_MAX, existing.record.confidence + CONFIDENCE_INCREMENT),
        decayScore: Math.min(DECAY_MAX, existing.record.decayScore + 2),
        lastSeenAt: timestamp,
        evidence: [...existing.record.evidence, { type: 'user-choice', ref: evidenceRef }],
        summary: buildSummary(choice, existing.confirmations),
      };
      continue;
    }

    // 新选择：先削弱同类别的其它偏好（对立选择）
    for (const acc of byId.values()) {
      if (acc.record.category === category) {
        acc.record = {
          ...acc.record,
          confidence: Math.max(CONFIDENCE_MIN, acc.record.confidence - CONFIDENCE_DECREMENT),
          decayScore: Math.max(DECAY_MIN, acc.record.decayScore - 1),
        };
      }
    }

    byId.set(id, {
      confirmations: 1,
      record: {
        id,
        scope: 'feature',
        kind: 'long_term',
        category,
        feature,
        stage: choice.stage ?? null,
        agent: choice.agent ?? null,
        summary: buildSummary(choice, 1),
        source: { type: 'user-choice', ref: `${feature}/${choice.choiceType}` },
        evidence: [{ type: 'user-choice', ref: evidenceRef }],
        tags: [category, choice.selected],
        confidence: CONFIDENCE_START,
        createdAt: timestamp,
        lastSeenAt: timestamp,
        expiresAt: null,
        decayScore: DECAY_START,
        influence: 'preference',
      },
    });
  }

  return [...byId.values()].map((acc) => acc.record);
}
