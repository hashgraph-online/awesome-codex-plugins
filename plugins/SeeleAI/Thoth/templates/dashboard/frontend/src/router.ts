import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import type { WorkbenchTab } from '@/types'

const WorkbenchView = () => import('@/views/WorkbenchView.vue')

interface RouteMetaShape {
  tab: WorkbenchTab
  section?: 'milestones' | 'overview'
}

const routes: Array<RouteRecordRaw & { meta: RouteMetaShape }> = [
  {
    path: '/',
    redirect: '/overview',
    meta: { tab: 'overview' },
  },
  {
    path: '/overview',
    name: 'overview',
    component: WorkbenchView,
    meta: { tab: 'overview', section: 'overview' },
  },
  {
    path: '/work-items',
    name: 'work-items',
    component: WorkbenchView,
    meta: { tab: 'detail' },
  },
  {
    path: '/milestones',
    name: 'milestones',
    component: WorkbenchView,
    meta: { tab: 'overview', section: 'milestones' },
  },
  {
    path: '/dag',
    name: 'dag',
    component: WorkbenchView,
    meta: { tab: 'dag' },
  },
  {
    path: '/timeline',
    name: 'timeline',
    component: WorkbenchView,
    meta: { tab: 'gantt' },
  },
  {
    path: '/todo',
    name: 'todo',
    component: WorkbenchView,
    meta: { tab: 'todo' },
  },
  {
    path: '/activity',
    name: 'activity',
    component: WorkbenchView,
    meta: { tab: 'activity' },
  },
  {
    path: '/system',
    name: 'system',
    component: WorkbenchView,
    meta: { tab: 'system' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
