<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import type { TodoProject, TodoTask } from '@/types/index'
import LoadingState from '@/components/common/LoadingState.vue'

const loading = ref(true)
const error = ref('')
const projects = ref<TodoProject[]>([])
const collapsed = ref<Set<number>>(new Set())

/* New project */
const newProjectName = ref('')
const addingProject = ref(false)

/* New task (per project) */
const newTaskDesc = ref<Record<number, string>>({})
const newTaskDue = ref<Record<number, string>>({})
const addingTask = ref<number | null>(null)

/* Inline editing */
const editingTask = ref<number | null>(null)
const editBuffer = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await api.getTodo()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function toggleCollapse(pid: number) {
  if (collapsed.value.has(pid)) collapsed.value.delete(pid)
  else collapsed.value.add(pid)
}

async function addProject() {
  const name = newProjectName.value.trim()
  if (!name) return
  addingProject.value = true
  try {
    const res = await api.addTodoProject(name)
    projects.value.push({ id: res.id, name: res.name, created_at: '', tasks: [] })
    newProjectName.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '添加失败'
  } finally {
    addingProject.value = false
  }
}

async function addTask(pid: number) {
  const desc = (newTaskDesc.value[pid] ?? '').trim()
  if (!desc) return
  addingTask.value = pid
  try {
    const due = newTaskDue.value[pid] || undefined
    const res = await api.addTodoTask(pid, desc, due)
    const proj = projects.value.find(p => p.id === pid)
    if (proj) {
      proj.tasks.push({
        id: res.id,
        project_id: pid,
        description: desc,
        due_label: null,
        due_date: due ?? null,
        completed: 0,
        completed_at: null,
        created_at: '',
      })
    }
    newTaskDesc.value[pid] = ''
    newTaskDue.value[pid] = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '添加失败'
  } finally {
    addingTask.value = null
  }
}

async function toggleComplete(task: TodoTask) {
  const newVal = !task.completed
  try {
    await api.updateTodoTask(task.id, { completed: newVal })
    task.completed = newVal ? 1 : 0
  } catch {
    /* revert silently */
  }
}

function startEdit(task: TodoTask) {
  editingTask.value = task.id
  editBuffer.value = task.description
}

async function saveEdit(task: TodoTask) {
  const text = editBuffer.value.trim()
  if (!text || text === task.description) {
    editingTask.value = null
    return
  }
  try {
    await api.updateTodoTask(task.id, { description: text })
    task.description = text
  } catch {
    /* keep old */
  } finally {
    editingTask.value = null
  }
}

onMounted(load)
defineExpose({ reload: load })
</script>

<template>
  <div class="todo-panel">
    <LoadingState v-if="loading" />
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else>
      <!-- Add project -->
      <div class="add-project-bar">
        <input
          v-model="newProjectName"
          class="input"
          placeholder="新建项目名称..."
          @keyup.enter="addProject"
        />
        <button class="btn-primary" :disabled="addingProject || !newProjectName.trim()" @click="addProject">
          添加项目
        </button>
      </div>

      <div v-if="!projects.length" class="empty-hint">暂无待办项目</div>

      <!-- Project list -->
      <div class="project-list">
        <div v-for="proj in projects" :key="proj.id" class="project-group">
          <div class="project-header" @click="toggleCollapse(proj.id)">
            <span class="collapse-icon" :class="{ open: !collapsed.has(proj.id) }">&#9656;</span>
            <h3 class="project-name">{{ proj.name }}</h3>
            <span class="task-count">{{ proj.tasks.length }} 项</span>
          </div>

          <div v-if="!collapsed.has(proj.id)" class="project-body">
            <!-- Tasks -->
            <div v-for="task in proj.tasks" :key="task.id" class="todo-item" :class="{ done: task.completed }">
              <input
                type="checkbox"
                class="todo-check"
                :checked="!!task.completed"
                @change="toggleComplete(task)"
              />
              <template v-if="editingTask === task.id">
                <input
                  v-model="editBuffer"
                  class="edit-input"
                  @keyup.enter="saveEdit(task)"
                  @blur="saveEdit(task)"
                  @keyup.escape="editingTask = null"
                />
              </template>
              <template v-else>
                <span class="todo-desc" @dblclick="startEdit(task)">{{ task.description }}</span>
              </template>
              <span v-if="task.due_date" class="due-label">{{ task.due_date }}</span>
            </div>

            <!-- Add task row -->
            <div class="add-task-row">
              <input
                v-model="newTaskDesc[proj.id]"
                class="input small"
                placeholder="新建任务..."
                @keyup.enter="addTask(proj.id)"
              />
              <input
                v-model="newTaskDue[proj.id]"
                type="date"
                class="input small date-input"
              />
              <button
                class="btn-small"
                :disabled="addingTask === proj.id || !(newTaskDesc[proj.id] ?? '').trim()"
                @click="addTask(proj.id)"
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.todo-panel {
  padding: 24px;
  max-width: 800px;
}

.error-msg {
  color: #a4262c;
  text-align: center;
  padding: 40px;
}
.empty-hint {
  color: var(--text-secondary, #6b5b4e);
  text-align: center;
  padding: 40px;
  font-size: 14px;
}

/* ── Add project ─── */
.add-project-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.input {
  padding: 8px 12px;
  border: 1px solid var(--border, #e8e0d6);
  border-radius: 8px;
  font-size: 13px;
  background: var(--bg-card, #ffffff);
  color: var(--text-primary, #2C1810);
  outline: none;
  flex: 1;
}
.input:focus {
  border-color: var(--accent, #CC8B3A);
}
.input.small {
  padding: 6px 10px;
  font-size: 12px;
}
.date-input {
  flex: 0 0 130px;
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--accent, #CC8B3A);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn-small {
  width: 30px;
  height: 30px;
  border: 1px solid var(--border, #e8e0d6);
  border-radius: 8px;
  background: transparent;
  color: var(--accent, #CC8B3A);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-small:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ── Project ─── */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-group {
  background: var(--bg-card, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(44, 24, 16, 0.06);
  overflow: hidden;
}

.project-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
}
.project-header:hover {
  background: var(--bg-secondary, #f0ebe4);
}

.collapse-icon {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
  transition: transform 0.2s;
}
.collapse-icon.open {
  transform: rotate(90deg);
}

.project-name {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #2C1810);
  flex: 1;
}

.task-count {
  font-size: 12px;
  color: var(--text-secondary, #6b5b4e);
}

.project-body {
  padding: 0 18px 14px;
}

/* ── Todo items ─── */
.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--bg-secondary, #f0ebe4);
}
.todo-item:last-of-type {
  border-bottom: none;
}

.todo-check {
  width: 16px;
  height: 16px;
  accent-color: var(--accent, #CC8B3A);
  cursor: pointer;
  flex-shrink: 0;
}

.todo-desc {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary, #2C1810);
  cursor: text;
}
.todo-item.done .todo-desc {
  text-decoration: line-through;
  color: var(--text-secondary, #6b5b4e);
}

.edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--accent, #CC8B3A);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #fffdf8;
}

.due-label {
  font-size: 11px;
  color: var(--text-secondary, #6b5b4e);
  white-space: nowrap;
}

/* ── Add task row ─── */
.add-task-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
</style>
