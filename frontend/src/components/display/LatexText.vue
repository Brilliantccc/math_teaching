<script setup lang="ts">
import { computed } from 'vue'
import { renderMathText } from '@/utils/math-render'

const props = defineProps<{
  content: string
  images?: string[]
}>()

const html = computed(() => renderMathText(props.content, props.images))
</script>

<template>
  <span class="latex-text" v-html="html" />
</template>

<style scoped>
.latex-text :deep(.inline-image) {
  display: inline-block;
  max-height: 200px;
  max-width: 100%;
  vertical-align: middle;
  margin: 0 6px;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
  background: #fafafa;
  object-fit: contain;
}

.latex-text :deep(.inline-image:hover) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
  transition: all 0.2s ease;
}

.latex-text :deep(.image-reference) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3px 10px;
  border-radius: 14px;
  font-size: 11px;
  font-weight: 500;
  margin: 0 6px;
  vertical-align: middle;
  cursor: default;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.latex-text :deep(.image-reference:hover) {
  transform: scale(1.05);
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.4);
}

.latex-text :deep(.image-reference::before) {
  content: "📷";
  font-size: 12px;
}
</style>
