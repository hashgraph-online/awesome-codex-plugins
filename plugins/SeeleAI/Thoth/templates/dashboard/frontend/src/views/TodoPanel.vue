<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api } from '@/api/client'
import type { TodoProject, TodoTask } from '@/types'

const projects = ref<TodoProject[]>([])
const loading = ref(true)
const error = ref('')

const newProjectName = ref('')
const newTaskInputs = ref<Record<number, string>>({})

onMounted(async () => {
  await loadTodo()
})

async function loadTodo() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await api.getTodo()
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

async function addProject() {
  const name = newProjectName.value.trim()
  if (!name) return
  try {
    await api.addTodoProject(name)
    newProjectName.value = ''
    await loadTodo()
  } catch (e) {
    error.value = String(e)
  }
}

async function addTask(projectId: number) {
  const desc = (newTaskInputs.value[projectId] ?? '').trim()
  if (!desc) return
  try {
    await api.addTodoTask(projectId, desc)
    newTaskInputs.value[projectId] = ''
    await loadTodo()
  } catch (e) {
    error.value = String(e)
  }
}

async function toggleTask(task: TodoTask) {
  try {
    await api.updateTodoTask(task.id, { completed: !task.completed })
    await loadTodo()
  } catch (e) {
    error.value = String(e)
  }
}

const totalTasks = computed(() => {
  return projects.value.reduce((sum, p) => sum + p.tasks.length, 0)
})

const completedTasks = computed(() => {
  return projects.value.reduce(
    (sum, p) => sum + p.tasks.filter(t => t.completed).length,
    0
  )
})
</script>

<template>
  <div class="panel">
    <h2 class="panel-title">待办</h2>

    <div class="todo-summary">
      <span>{{ completedTasks }}/{{ totalTasks }} completed</span>
    </div>

    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else>
      <!-- Add project -->
      <div class="add-project card">
        <input
          v-model="newProjectName"
          placeholder="New project name..."
          class="input"
          @keydown.enter="addProject"
        />
        <button class="btn-primary" @click="addProject">Add Project</button>
      </div>

      <!-- Projects -->
      <div v-for="project in projects" :key="project.id" class="card project-card">
        <h3 class="project-name">{{ project.name }}</h3>

        <ul class="task-list">
          <li
            v-for="task in project.tasks"
            :key="task.id"
            class="task-item"
            :class="{ completed: task.completed }"
          >
            <label class="task-check">
              <input
                type="checkbox"
                :checked="!!task.completed"
                @change="toggleTask(task)"
              />
              <span class="task-desc">{{ task.description }}</span>
            </label>
            <span v-if="task.due_label" class="task-due">{{ task.due_label }}</span>
          </li>
        </ul>

        <!-- Add task -->
        <div class="add-task">
          <input
            v-model="newTaskInputs[project.id]"
            placeholder="Add a task..."
            class="input input-sm"
            @keydown.enter="addTask(project.id)"
          />
          <button class="btn-sm" @click="addTask(project.id)">+</button>
        </div>
      </div>

      <div v-if="projects.length === 0" class="empty-state">No projects yet. Create one above.</div>
    </template>
  </div>
</template>

<style scoped>
.panel {
  max-width: 720px;
}

.panel-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.todo-summary {
  font-size: 14px;
  color: var(--color-accent);
  font-weight: 600;
  margin-bottom: 20px;
}

.loading-state,
.error-state,
.empty-state {
  padding: 32px;
  text-align: center;
}

.error-state {
  color: #c0392b;
}

.card {
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px var(--color-card-shadow);
}

.add-project {
  display: flex;
  gap: 12px;
  align-items: center;
}

.input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  background: var(--color-bg);
}

.input-sm {
  padding: 6px 10px;
  font-size: 13px;
}

.btn-primary {
  padding: 8px 20px;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-sm {
  padding: 6px 12px;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
  font-size: 16px;
}

.project-name {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}

.task-list {
  list-style: none;
  margin-bottom: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border);
}

.task-item:last-child {
  border-bottom: none;
}

.task-item.completed .task-desc {
  text-decoration: line-through;
  opacity: 0.5;
}

.task-check {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
}

.task-check input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: var(--color-accent);
}

.task-desc {
  font-size: 14px;
}

.task-due {
  font-size: 12px;
  color: var(--color-accent);
  font-weight: 600;
  white-space: nowrap;
}

.add-task {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
