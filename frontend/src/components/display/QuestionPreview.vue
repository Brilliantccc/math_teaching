<script setup lang="ts">
import { computed } from 'vue'
import LatexText from './LatexText.vue'

const props = withDefaults(defineProps<{
  content: string
  images?: string[]
  showImages?: boolean
  compact?: boolean
}>(), {
  showImages: false,
  compact: false
})

const parsedImages = computed(() => {
  if (!props.images) return []
  try {
    return Array.isArray(props.images) ? props.images : JSON.parse(props.images)
  } catch {
    return []
  }
})
</script>

<template>
  <div class="question-preview" :class="{ compact }">
    <!-- 主内容区域 -->
    <div class="question-main">
      <!-- 题干文字 -->
      <div class="question-content" :class="{ compact }">
        <LatexText :content="content" :images="images" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.question-preview {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--color-bg-card);
  transition: box-shadow 0.2s;
}

.question-preview:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.question-preview.compact {
  border: none;
  border-radius: 0;
  background: transparent;
}

.question-preview.compact:hover {
  box-shadow: none;
}

.question-content {
  padding: 16px 20px;
  line-height: 1.8;
  font-size: 14px;
  color: var(--color-text-body);
}

.question-content.compact {
  padding: 10px 12px;
  line-height: 1.6;
  font-size: 13px;
}
</style>
