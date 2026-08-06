<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import LatexText from '@/components/display/LatexText.vue'

const props = defineProps<{
  content: string
  disabled?: boolean
}>()

// 存储所有空的答案
const answers = ref<string[]>([])

// 统一输出格式：用逗号分隔各空答案
const modelValue = defineModel<string>({ default: '' })

// 解析题目中的空格数量
const blankCount = computed(() => {
  // 匹配 ___ 或 ______ 或 ( ) 等常见填空符号
  const blankRegex = /_{3,}|（\s*）|\(\s*\)/g
  const matches = props.content.match(blankRegex)
  return Math.max(matches?.length || 1, 1)
})

// 题目正文（替换空格为占位符）
const questionBody = computed(() => {
  let content = props.content
  // 将空格替换为序号标记，方便用户对应
  let index = 0
  content = content.replace(/_{3,}|（\s*）|\(\s*\)/g, () => {
    index++
    return `_____${index}_____`
  })
  return content
})

// 初始化答案数组
watch(blankCount, (newCount) => {
  while (answers.value.length < newCount) {
    answers.value.push('')
  }
  // 同步到 modelValue
  syncModelValue()
}, { immediate: true })

// 监听答案变化，同步到 modelValue
watch(answers, () => {
  syncModelValue()
}, { deep: true })

function syncModelValue() {
  modelValue.value = answers.value.join(',')
}

function updateAnswer(index: number, value: string) {
  if (props.disabled) return
  answers.value[index] = value
}

// 处理键盘事件
function handleKeydown(event: KeyboardEvent, index: number) {
  if (event.key === 'Enter') {
    event.preventDefault()
    // 移动到下一个输入框
    const nextInput = document.querySelector(`[data-blank-index="${index + 1}"]`) as HTMLInputElement
    if (nextInput) {
      nextInput.focus()
    }
  }
}
</script>

<template>
  <div class="fill-blank-question">
    <div class="question-body">
      <LatexText :content="questionBody" />
    </div>

    <div class="blanks-area">
      <div
        v-for="(_, index) in blankCount"
        :key="index"
        class="blank-item"
      >
        <label class="blank-label">第 {{ index + 1 }} 空：</label>
        <a-input
          :value="answers[index] || ''"
          :placeholder="`请输入第 ${index + 1} 空的答案`"
          :disabled="disabled"
          class="blank-input"
          data-blank-index="index"
          @input="(e) => updateAnswer(index, e.target.value)"
          @keydown="(e) => handleKeydown(e, index)"
        />
      </div>
    </div>

    <div class="input-hint">
      <a-alert
        type="info"
        show-icon
        :style="{ marginTop: '12px' }"
      >
        <template #message>
          <span>输入提示</span>
        </template>
        <template #description>
          <div class="hint-content">
            <p>支持的格式：</p>
            <ul>
              <li>分数：<code>1/2</code> 或 <code>\frac{1}{2}</code></li>
              <li>小数：<code>0.5</code></li>
              <li>百分数：<code>50%</code></li>
              <li>多个空用逗号分隔</li>
            </ul>
          </div>
        </template>
      </a-alert>
    </div>
  </div>
</template>

<style scoped>
.fill-blank-question {
  margin-top: 16px;
}

.question-body {
  margin-bottom: 24px;
  font-size: 16px;
  line-height: 1.8;
  color: var(--color-text-body);
}

.blanks-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.blank-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.blank-label {
  min-width: 70px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.blank-input {
  flex: 1;
  max-width: 400px;
}

.input-hint {
  margin-top: 16px;
}

.hint-content {
  font-size: 13px;
  line-height: 1.6;
}

.hint-content p {
  margin: 4px 0;
}

.hint-content ul {
  margin: 4px 0;
  padding-left: 20px;
}

.hint-content li {
  margin: 4px 0;
}

.hint-content code {
  background: var(--color-bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}
</style>
