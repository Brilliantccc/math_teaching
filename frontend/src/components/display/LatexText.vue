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
