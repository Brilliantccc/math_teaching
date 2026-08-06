<script setup lang="ts">
import { computed } from 'vue'
import LatexText from '@/components/display/LatexText.vue'

interface ChoiceOption {
  key: string
  content: string
  image?: string
}

const props = defineProps<{
  content: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const modelValue = defineModel<string>({ default: '' })

// 从题目内容中解析选项
const options = computed<ChoiceOption[]>(() => {
  const optionRegex = /([A-D])[.、．]\s*([^\n]*)/g
  const result: ChoiceOption[] = []
  let match

  while ((match = optionRegex.exec(props.content)) !== null) {
    result.push({
      key: match[1],
      content: match[2].trim()
    })
  }

  // 如果没有找到选项，返回默认选项
  if (result.length === 0) {
    return [
      { key: 'A', content: '选项A' },
      { key: 'B', content: '选项B' },
      { key: 'C', content: '选项C' },
      { key: 'D', content: '选项D' }
    ]
  }

  return result
})

// 题目正文（不含选项）
const questionBody = computed(() => {
  const lines = props.content.split('\n')
  const bodyLines: string[] = []

  for (const line of lines) {
    // 跳过以 A. B. C. D. 开头的行
    if (/^[A-D][.、．]/.test(line.trim())) {
      continue
    }
    bodyLines.push(line)
  }

  return bodyLines.join('\n').trim()
})

function selectOption(key: string) {
  if (props.disabled) return
  modelValue.value = key
}
</script>

<template>
  <div class="choice-question">
    <div v-if="questionBody" class="question-body">
      <LatexText :content="questionBody" />
    </div>

    <div class="options-list">
      <div
        v-for="option in options"
        :key="option.key"
        class="option-item"
        :class="{
          selected: modelValue === option.key,
          disabled: disabled
        }"
        @click="selectOption(option.key)"
      >
        <div class="option-radio">
          <div class="radio-inner" />
        </div>
        <span class="option-label">{{ option.key }}</span>
        <span class="option-content">
          <LatexText :content="option.content" />
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.choice-question {
  margin-top: 16px;
}

.question-body {
  margin-bottom: 20px;
  font-size: 16px;
  line-height: 1.8;
  color: var(--color-text-body);
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-bg-card);
}

.option-item:hover:not(.disabled) {
  border-color: var(--color-primary);
  background: var(--color-bg-hover);
}

.option-item.selected {
  border-color: var(--color-primary);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.option-item.disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.option-radio {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.option-item.selected .option-radio {
  border-color: var(--color-primary);
  background: var(--color-primary);
}

.radio-inner {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
  transition: all 0.2s ease;
}

.option-item.selected .radio-inner {
  background: white;
}

.option-label {
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 24px;
}

.option-content {
  flex: 1;
  color: var(--color-text-body);
  line-height: 1.6;
}
</style>
