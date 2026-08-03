<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { renderMathText } from '@/utils/math-render'

const props = withDefaults(defineProps<{
  modelValue: string
  images?: string[]
  rows?: number
  placeholder?: string
}>(), {
  rows: 4,
  placeholder: '输入内容（公式用 $...$ 包裹，中文用 \\text{中文}）',
  images: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const activeTab = ref<'edit' | 'preview'>('edit')

const previewHtml = computed(() => {
  if (!props.modelValue) {
    return '在编辑区输入内容，这里会实时显示渲染结果'
  }
  return renderMathText(props.modelValue, props.images)
})

function insertSymbol(before: string, after?: string) {
  const el = textareaRef.value
  if (!el) return

  const start = el.selectionStart
  const end = el.selectionEnd
  const selected = props.modelValue.substring(start, end)
  const afterStr = after || ''
  const newValue = props.modelValue.substring(0, start) + before + selected + afterStr + props.modelValue.substring(end)

  emit('update:modelValue', newValue)

  nextTick(() => {
    el.focus()
    const cursorPos = start + before.length + selected.length
    el.setSelectionRange(cursorPos, cursorPos)
  })
}

function handleInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLTextAreaElement).value)
}
</script>

<template>
  <div class="latex-editor">
    <div class="editor-header">
      <div class="editor-tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'edit' }"
          @click="activeTab = 'edit'"
        >
          ✏️ 编辑
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'preview' }"
          @click="activeTab = 'preview'"
        >
          👁️ 预览
        </button>
      </div>
      <div class="editor-toolbar">
        <a-button-group size="small">
          <a-button @click="insertSymbol('$', '$')">$ 公式 $</a-button>
          <a-button @click="insertSymbol('\\text{', '}')">\\text{}</a-button>
          <a-button @click="insertSymbol('\\frac{', '}{}')">分数</a-button>
          <a-button @click="insertSymbol('\\sqrt{', '}')">根号</a-button>
          <a-button @click="insertSymbol('^{', '}')">上标</a-button>
          <a-button @click="insertSymbol('_{', '}')">下标</a-button>
          <a-button @click="insertSymbol('\\times')">× 乘号</a-button>
          <a-button @click="insertSymbol('\\div')">÷ 除号</a-button>
          <a-button @click="insertSymbol('\\pm')">± 正负</a-button>
          <a-button @click="insertSymbol('\\leq')">≤</a-button>
          <a-button @click="insertSymbol('\\geq')">≥</a-button>
          <a-button @click="insertSymbol('\\neq')">≠</a-button>
        </a-button-group>
      </div>
    </div>

    <div class="editor-body">
      <!-- 编辑面板 -->
      <div class="edit-pane" :class="{ hidden: activeTab !== 'edit' }">
        <textarea
          ref="textareaRef"
          :value="modelValue"
          @input="handleInput"
          :rows="rows"
          :placeholder="placeholder"
          class="code-textarea"
        />
      </div>

      <!-- 预览面板 -->
      <div class="preview-pane" :class="{ hidden: activeTab !== 'preview' }">
        <div class="preview-content" v-html="previewHtml" />
      </div>
    </div>

    <div class="editor-footer">
      <span class="hint">提示：用 <code>$...$</code> 包裹公式，中文用 <code>\text{中文}</code></span>
    </div>
  </div>
</template>

<style scoped>
.latex-editor {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-bg-card);
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--color-bg-hover);
  border-bottom: 1px solid var(--color-border);
  gap: 8px;
  flex-wrap: wrap;
}

.editor-tabs {
  display: flex;
  gap: 2px;
}

.tab-btn {
  padding: 4px 12px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.tab-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-active);
}

.tab-btn.active {
  color: var(--color-primary);
  background: var(--color-bg-card);
  font-weight: 500;
}

.editor-toolbar {
  flex-shrink: 0;
}

.editor-toolbar .ant-btn {
  font-size: 12px;
  padding: 0 6px;
  height: 24px;
}

.editor-body {
  min-height: 0;
}

.edit-pane,
.preview-pane {
  min-height: 80px;
}

.edit-pane.hidden,
.preview-pane.hidden {
  display: none;
}

.code-textarea {
  border: none;
  outline: none;
  resize: vertical;
  padding: 10px 12px;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 80px;
  width: 100%;
  box-sizing: border-box;
  background: var(--color-bg-card);
  color: var(--color-text-body);
}

.code-textarea::placeholder {
  color: var(--color-text-placeholder);
}

.code-textarea:focus {
  box-shadow: none;
}

.preview-content {
  padding: 12px;
  min-height: 80px;
  line-height: 1.8;
  overflow: visible;
  background: var(--color-bg-card);
  color: var(--color-text-body);
}

.editor-footer {
  padding: 6px 12px;
  background: var(--color-bg-hover);
  border-top: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--color-text-muted);
}

.hint code {
  background: var(--color-bg-elevated);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
}
</style>
