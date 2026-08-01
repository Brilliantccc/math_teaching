<script setup lang="ts">
import { computed } from 'vue'
import { renderMathText } from '@/utils/katex'

const props = defineProps<{ content: string }>()

const html = computed(() => renderMathText(props.content))
</script>

<template>
  <span class="latex-text" v-html="html" />
</template>
