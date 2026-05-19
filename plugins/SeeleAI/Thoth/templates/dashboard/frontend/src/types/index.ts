export type WorkItemStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'blocked'
  | 'ready'
  | 'invalid'
  | 'failed'

export type WorkbenchTab =
  | 'overview'
  | 'detail'
  | 'dag'
  | 'gantt'
  | 'todo'
  | 'activity'
  | 'system'

export interface Dependency {
  work_id: string
  type: 'hard' | 'soft'
  reason?: string
}

export interface Deliverable {
  path: string
  type: string
  description?: string
}

export interface PhaseCriteria {
  metric: string
  threshold: number
  current: number | null
}

export interface PhaseInfo {
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  criteria?: PhaseCriteria
  started_at?: string
  completed_at?: string
}

export interface Phases {
  survey?: PhaseInfo
  method_design?: PhaseInfo
  experiment?: PhaseInfo
  conclusion?: PhaseInfo
}

export interface RunSummary {
  run_id: string
  work_id: string | null
  title: string
  host?: string | null
  status: string
  phase?: string | null
  progress_pct: number
  executor?: string | null
  attachable?: boolean
  created_at?: string | null
  started_at?: string | null
  last_updated_at?: string | null
  last_heartbeat_at?: string | null
  last_event_seq: number
  is_active: boolean
  is_stale: boolean
  stale?: boolean
  supervisor_state?: string | null
  latest_message?: string
  artifact_count: number
  events_path?: string | null
}

export interface RunEvent {
  seq: number
  ts?: string | null
  kind: string
  level: string
  message: string
  data?: Record<string, unknown>
}

export interface RunEventPage {
  run_id: string
  events: RunEvent[]
  next_after_seq?: number | null
  has_more: boolean
}

export interface RunDetail extends RunSummary {
  run: Record<string, unknown>
  state: Record<string, unknown>
  heartbeat: Record<string, unknown>
  artifacts: Record<string, unknown>
  result?: Record<string, unknown>
}

export interface WorkResult {
  work_id: string
  source?: string | null
  usable?: boolean | null
  meets_goal?: boolean | null
  failure_class?: string | null
  conclusion?: string | null
  current_summary?: string | null
  evidence_paths?: string[]
  updated_at?: string | null
  last_attempt_at?: string | null
  last_closure_at?: string | null
  metrics?: Record<string, unknown>
  latest_run?: Record<string, unknown>
  latest_review?: Record<string, unknown>
}

export interface WorkItem {
  id: string
  work_id?: string
  title: string
  type?: string
  direction: string
  module: string
  hypothesis?: string
  phases?: Phases
  deliverables?: Deliverable[]
  ready_state?: 'ready' | 'blocked' | 'invalid' | 'validated' | 'failed' | 'active' | 'draft' | 'abandoned'
  blocking_reason?: string
  goal_statement?: string
  decision_ids?: string[]
  candidate_method_id?: string
  implementation_recipe?: string[]
  eval_entrypoint?: Record<string, unknown> | null
  failure_classes?: string[]
  verdict?: Record<string, unknown> | string | null
  depends_on?: Dependency[]
  created_at?: string
  generated_at?: string
  estimated_total_hours?: number
  time_spent_hours?: number
  work_result?: WorkResult
  computed_status: WorkItemStatus
  computed_progress: number
  active_run?: RunSummary | null
  run_count?: number
}

export interface WorkItemListResponse {
  total: number
  offset: number
  limit: number
  work_items: WorkItem[]
}

export interface WorkItemRunsResponse {
  work_id: string
  runs: RunSummary[]
}

export interface TreeWorkItem {
  id: string
  title: string
  type: string
  status: WorkItemStatus
  progress: number
  hypothesis?: string
}

export interface TreeModule {
  id: string
  name: string
  scientific_question?: string
  work_item_count: number
  progress: number
  work_items: TreeWorkItem[]
  upstream: string[]
  downstream: string[]
}

export interface TreeDirection {
  direction: string
  label: string
  module_count: number
  progress: number
  modules: TreeModule[]
}

export interface BlockedWorkItem {
  id: string
  title: string
  blocked_by: string[]
}

export interface RuntimeOverview {
  active_run_count: number
  stale_run_count: number
  active_runs: RunSummary[]
  last_runtime_update?: string | null
  progress_source: string
  host_breakdown?: string[]
}

export interface ProgressData {
  overall_progress: number
  by_direction: Record<string, number>
  status_counts: {
    total: number
    pending: number
    in_progress: number
    completed: number
    blocked: number
    ready?: number
    invalid?: number
    failed?: number
  }
  blocked_work_items: BlockedWorkItem[]
  module_count: number
  estimation: {
    total_work_items: number
    completed_work_items: number
    elapsed_days: number
    rate_per_day?: number
    estimated_days_remaining: number | null
    message?: string
  } | null
  runtime: RuntimeOverview
  compiler?: Record<string, unknown>
}

export interface DagNode {
  id: string
  label: string
  type: 'module' | 'work_item'
  direction: string
  module?: string
  status?: WorkItemStatus
  progress: number
  work_item_count?: number
}

export interface DagEdge {
  source: string
  target: string
  type: 'hard' | 'soft'
  level: 'module' | 'work_item'
  reason?: string
}

export interface DagData {
  nodes: DagNode[]
  edges: DagEdge[]
}

export interface GanttRow {
  id: string
  title: string
  module: string
  direction: string
  status: string
  start_date: string | null
  end_date: string | null
  estimated_hours: number
  progress: number
  dependencies: string[]
}

export interface TimelineItem {
  id: string
  title: string
  module: string
  direction: string
  status: string
  progress: number
  start_date: string | null
  end_date: string | null
  estimated_hours: number
  spent_hours?: number
}

export interface Milestone {
  id: string
  name: string
  description: string
  progress: number
  work_item_count: number
}

export interface ActivityEvent {
  id: number
  work_id: string
  work_title: string
  module: string
  direction: string
  verdict: string
  conclusion_text: string | null
  created_at: string
}

export interface TodoTask {
  id: number
  project_id: number
  description: string
  due_label: string | null
  due_date: string | null
  completed: number
  completed_at: string | null
  created_at: string
}

export interface TodoProject {
  id: number
  name: string
  created_at: string
  tasks: TodoTask[]
}

export interface SystemStatus {
  last_updated: number | string
  work_item_count: number
  module_count: number
  cache_info: Record<string, unknown>
  runtime?: RuntimeOverview
  compiler?: Record<string, unknown>
}

export interface OverviewConclusion {
  work_id: string
  title: string
  module: string
  direction: string
  status: string
  updated_at?: string | null
  source?: string | null
  conclusion?: string | null
  evidence_paths: string[]
}

export interface TodoNextEntry {
  id: string
  status: string
  description: string
}

export interface OverviewSummary {
  project: {
    name?: string
    description?: string
    language?: string
  }
  headline: {
    total_work_items: number
    completed_work_items: number
    blocked_work_items: number
    ready_work_items: number
    overall_progress: number
    decision_queue_count: number
  }
  compiler_summary?: Record<string, unknown>
  runtime: RuntimeOverview
  milestones: Milestone[]
  recent_conclusions: OverviewConclusion[]
  recent_activity: string[]
  todo_next: TodoNextEntry[]
  blocked_work_items?: BlockedWorkItem[]
  healthy: boolean
  health_message: string
  active_run_count?: number
  gantt_preview?: GanttRow[]
}

export interface ResearchConfig {
  project?: {
    name?: string
    description?: string
    language?: string
  }
  research?: {
    directions?: Array<{
      id: string
      label_zh?: string
      label_en?: string
      color?: string
    }>
  }
  dashboard?: {
    port?: number
    theme?: string
  }
}

export interface WorkItemFilters {
  status?: WorkItemStatus | ''
  module?: string
  direction?: string
  limit?: number
  offset?: number
}
