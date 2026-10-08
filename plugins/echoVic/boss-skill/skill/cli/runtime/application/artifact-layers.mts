/**
 * 产物按生命周期分层。
 *
 * 一次运行会在 `.boss/<feature>/` 顶层留下十余个文件，但它们的寿命完全不同：
 * prd / architecture / ui-spec 描述产品本身，跨迭代持续维护；tasks / qa-report /
 * deploy-report 描述某一次执行，跑完即过期；`.html` 是从 Markdown 生成的视图。
 * 平铺在一起时，第二次迭代的人分不清哪些还作数——这正是「只保留结果，不保留
 * 执行过程噪音」要解决的问题。
 *
 * 这里只做分类与陈旧判定，不移动任何文件：产物路径写在 50 个文件里（agent 提示词、
 * 模板、hook、DAG、文档），挪目录的风险远大于收益。
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { readRuntimeEvents } from './pipeline-dag.mts';
import { ensureFeatureName } from './state.mts';

export type ArtifactLayerId = 'product' | 'run' | 'derived';

export interface ArtifactLayer {
  id: ArtifactLayerId;
  title: string;
  hint: string;
}

/** 渲染顺序固定：产品资产在前，执行痕迹在后。 */
export const ARTIFACT_LAYERS: ArtifactLayer[] = [
  {
    id: 'product',
    title: '产品资产',
    hint: '描述产品本身，跨迭代持续维护',
  },
  {
    id: 'run',
    title: '本轮记录',
    hint: '描述这一次执行，下一轮会被取代',
  },
  {
    id: 'derived',
    title: '派生视图',
    hint: '从 Markdown 生成，可随时重建',
  },
];

const PRODUCT_ARTIFACTS = new Set([
  'prd.md',
  'architecture.md',
  'ui-spec.md',
  'ui-design.json',
  'ui-design-variants.json',
  'design-brief',
]);

/**
 * 未知产物归入 `run`：宁可让它随迭代过期，也不要把它当成需要长期维护的产品资产。
 * 自定义 pack 可以新增产物，默认按保守的一侧分类。
 */
export function artifactLayer(artifact: string): ArtifactLayerId {
  if (artifact.endsWith('.html')) return 'derived';
  if (PRODUCT_ARTIFACTS.has(artifact)) return 'product';
  return 'run';
}

export interface StaleRunArtifact {
  artifact: string;
  /** 让它过期的那个上游产品资产。 */
  supersededBy: string;
}

/**
 * 找出「上游产品资产已经重做，自己却还停在上一轮」的执行痕迹。
 *
 * 判定依据是事件流的顺序而非时间戳：某个 run 层产物最后一次被记录之后，若又有
 * 产品资产被记录，说明需求或架构已经变了，那份任务清单 / 测试报告不再对应当前状态。
 */
export function findStaleRunArtifacts(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): StaleRunArtifact[] {
  ensureFeatureName(feature);
  const events = readRuntimeEvents(cwd, feature).filter(
    (event) => event.type === EVENT_TYPES.ARTIFACT_RECORDED,
  );

  const lastSeenAt = new Map<string, number>();
  events.forEach((event, index) => {
    const artifact = String(event.data.artifact ?? '');
    if (artifact) lastSeenAt.set(artifact, index);
  });

  const stale: StaleRunArtifact[] = [];
  for (const [artifact, index] of lastSeenAt) {
    if (artifactLayer(artifact) !== 'run') continue;
    const superseding = events
      .slice(index + 1)
      .map((event) => String(event.data.artifact ?? ''))
      .find((name) => name && artifactLayer(name) === 'product');
    if (superseding) stale.push({ artifact, supersededBy: superseding });
  }
  return stale.sort((left, right) => left.artifact.localeCompare(right.artifact));
}
