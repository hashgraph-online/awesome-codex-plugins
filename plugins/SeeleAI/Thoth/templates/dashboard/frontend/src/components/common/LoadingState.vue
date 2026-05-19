<script setup lang="ts">
withDefaults(defineProps<{
  text?: string
}>(), {
  text: '加载中...',
})
</script>

<template>
  <div class="loading-state">
    <div class="spinner" />
    <span class="loading-text">{{ text }}</span>
  </div>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--bg-secondary, #f0ebe4);
  border-top-color: var(--accent, #CC8B3A);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary, #6b5b4e);
}
</style>
