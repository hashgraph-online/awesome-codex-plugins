import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import type { ResearchConfig } from '@/types'

export const useAppStore = defineStore('app', () => {
  const config = ref<ResearchConfig | null>(null)
  const currentPanel = ref<string>('overview')
  const loading = ref(false)

  async function fetchConfig() {
    loading.value = true
    try {
      config.value = await api.getConfig()
    } catch (e) {
      console.error('Failed to load config:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    config,
    currentPanel,
    loading,
    fetchConfig,
  }
})
