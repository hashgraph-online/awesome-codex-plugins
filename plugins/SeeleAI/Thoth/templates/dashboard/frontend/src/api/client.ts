import type {
  ActivityEvent,
  DagData,
  GanttRow,
  OverviewSummary,
  ProgressData,
  ResearchConfig,
  RunDetail,
  RunEventPage,
  RunSummary,
  SystemStatus,
  WorkItem,
  WorkItemFilters,
  WorkItemListResponse,
  WorkItemRunsResponse,
  Milestone,
  TodoProject,
  TreeDirection,
} from '@/types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || body.error || `HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  getConfig: () => request<ResearchConfig>('/config'),
  getTree: () => request<TreeDirection[]>('/tree'),
  getProgress: () => request<ProgressData>('/progress'),
  getOverviewSummary: () => request<OverviewSummary>('/overview-summary'),
  getSystemStatus: () => request<SystemStatus>('/status'),

  getWorkItems: (filters?: WorkItemFilters) => {
    const params = new URLSearchParams()
    if (filters?.status) params.set('status', filters.status)
    if (filters?.module) params.set('module', filters.module)
    if (filters?.direction) params.set('direction', filters.direction)
    if (filters?.limit) params.set('limit', String(filters.limit))
    if (filters?.offset) params.set('offset', String(filters.offset))
    const query = params.toString()
    return request<WorkItemListResponse>(`/work-items${query ? `?${query}` : ''}`)
  },
  getWorkItem: (workId: string) => request<WorkItem>(`/work-items/${workId}`),
  getWorkItemActiveRun: (workId: string) =>
    request<RunSummary | null>(`/work-items/${workId}/active-run`),
  getWorkItemRuns: (workId: string) =>
    request<WorkItemRunsResponse>(`/work-items/${workId}/runs`),
  getRun: (runId: string) => request<RunDetail>(`/runs/${runId}`),
  getRunEvents: (runId: string, afterSeq?: number | null, limit = 100) => {
    const params = new URLSearchParams()
    if (afterSeq != null) params.set('after_seq', String(afterSeq))
    params.set('limit', String(limit))
    return request<RunEventPage>(`/runs/${runId}/events?${params.toString()}`)
  },

  getDag: () => request<DagData>('/dag'),
  getTimeline: () => request<GanttRow[]>('/timeline'),
  getGantt: () => request<GanttRow[]>('/gantt'),
  getMilestones: () => request<Milestone[]>('/milestones'),
  getActivity: (limit = 50) => request<ActivityEvent[]>(`/activity?limit=${limit}`),

  getTodo: () => request<TodoProject[]>('/todo'),
  addTodoProject: (name: string) =>
    request<{ id: number; name: string }>('/todo/projects', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  addTodoTask: (projectId: number, description: string, dueDate?: string) =>
    request<{ id: number; project_id: number; description: string }>(
      '/todo/tasks',
      {
        method: 'POST',
        body: JSON.stringify({
          project_id: projectId,
          description,
          due_date: dueDate ?? null,
        }),
      },
    ),
  updateTodoTask: (
    taskId: number,
    patch: { completed?: boolean; description?: string; due_date?: string },
  ) =>
    request<{ id: number; updated: boolean }>(`/todo/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),

  triggerValidate: () =>
    request<Record<string, unknown>>('/trigger/validate', { method: 'POST' }),
  triggerSync: () =>
    request<Record<string, unknown>>('/trigger/sync', { method: 'POST' }),
  triggerHealthCheck: () =>
    request<Record<string, unknown>>('/trigger/health-check', {
      method: 'POST',
    }),
}
