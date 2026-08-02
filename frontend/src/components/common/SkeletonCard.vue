<script setup lang="ts">
defineProps<{
  rows?: number
  avatar?: boolean
}>()
</script>

<template>
  <div class="skeleton-card">
    <div v-if="avatar" class="skeleton-avatar"></div>
    <div class="skeleton-content">
      <div class="skeleton-title"></div>
      <div v-for="i in (rows || 3)" :key="i" class="skeleton-row" :style="{ width: `${80 + Math.random() * 20}%` }"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-bg-card);
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--color-bg-hover) 25%, var(--color-bg-active) 50%, var(--color-bg-hover) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  flex-shrink: 0;
}

.skeleton-content {
  flex: 1;
}

.skeleton-title {
  width: 40%;
  height: 20px;
  margin-bottom: 12px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg-hover) 25%, var(--color-bg-active) 50%, var(--color-bg-hover) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-row {
  height: 14px;
  margin-bottom: 8px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg-hover) 25%, var(--color-bg-active) 50%, var(--color-bg-hover) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-row:last-child {
  margin-bottom: 0;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
