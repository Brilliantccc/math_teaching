<script setup lang="ts">
import { computed } from 'vue'
import LatexText from '@/components/display/LatexText.vue'

const props = defineProps<{
  content: string
  disabled?: boolean
}>()

const modelValue = defineModel<string>({ default: '' })

// 题目正文
const questionBody = computed(() => {
  return props.content.trim()
})

function selectAnswer(value: string) {
  if (props.disabled) return
  modelValue.value = value
}
</script>

<template>
  <div class="judge-question">
    <div class="question-body">
      <LatexText :content="questionBody" />
    </div>

    <div class="judge-options">
      <div
        class="judge-btn true-btn"
        :class="{
          selected: modelValue === '对',
          disabled: disabled
        }"
        @click="selectAnswer('对')"
      >
        <span class="judge-icon">✓</span>
        <span class="judge-text">对</span>
      </div>

      <div
        class="judge-btn false-btn"
        :class="{
          selected: modelValue === '错',
          disabled: disabled
        }"
        @click="selectAnswer('错')"
      >
        <span class="judge-icon">✗</span>
        <span class="judge-text">错</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.judge-question {
  margin-top: 16px;
}

.question-body {
  margin-bottom: 24px;
  font-size: 16px;
  line-height: 1.8;
  color: var(--color-text-body);
}

.judge-options {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.judge-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 100px;
  border: 3px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--color-bg-card);
}

.judge-btn:hover:not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.judge-btn.disabled {
  cursor: not-allowed;
  opacity: 0.8;
}

.judge-btn.true-btn:hover:not(.disabled),
.judge-btn.true-btn.selected {
  border-color: #52c41a;
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.1), rgba(82, 196, 26, 0.05));
}

.judge-btn.false-btn:hover:not(.disabled),
.judge-btn.false-btn.selected {
  border-color: #ff4d4f;
  background: linear-gradient(135deg, rgba(255, 77, 79, 0.1), rgba(255, 77, 79, 0.05));
}

.judge-icon {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
  transition: transform 0.2s ease;
}

.judge-btn.selected .judge-icon {
  transform: scale(1.2);
}

.true-btn .judge-icon {
  color: #52c41a;
}

.false-btn .judge-icon {
  color: #ff4d4f;
}

.judge-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.judge-btn.selected .judge-text {
  color: inherit;
}

.true-btn.selected .judge-text {
  color: #52c41a;
}

.false-btn.selected .judge-text {
  color: #ff4d4f;
}
</style>
