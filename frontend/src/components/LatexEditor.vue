<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { renderMathText } from '@/utils/katex'

const props = withDefaults(defineProps<{
  modelValue: string
  rows?: number
  placeholder?: string
}>(), {
  rows: 4,
  placeholder: '输入内容（支持 LaTeX，用 $...$ 行内，$$...$$ 块级）'
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)
const previewHtml = computed(() => renderMathText(props.modelValue))

function insertSymbol(before: string, after: string) {
  const el = textareaRef.value
  if (!el) return

  const start = el.selectionStart
  const end = el.selectionEnd
  const selected = props.modelValue.substring(start, end)
  const newValue = props.modelValue.substring(0, start) + before + selected + after + props.modelValue.substring(end)

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
    <div class="editor-toolbar">
      <a-button-group size="small">
        <a-button @click="insertSymbol('$', '$')">行内 $</a-button>
        <a-button @click="insertSymbol('$$\n', '\n$$')">块级 $$</a-button>
        <a-button @click="insertSymbol('\\frac{', '}{}')">分数</a-button>
        <a-button @click="insertSymbol('\\sqrt{', '}')">根号</a-button>
        <a-button @click="insertSymbol('^{', '}')">上标</a-button>
        <a-button @click="insertSymbol('_{', '}')">下标</a-button>
        <a-button @click="insertSymbol('\\int_{', '}^{}')">积分</a-button>
        <a-button @click="insertSymbol('\\sum_{', '}^{}')">求和</a-button>
      </a-button-group>
    </div>
    <div class="editor-body">
      <div class="editor-pane">
        <div class="pane-label">LaTeX 输入</div>
        <textarea
          ref="textareaRef"
          :value="modelValue"
          @input="handleInput"
          :rows="rows"
          :placeholder="placeholder"
          class="code-textarea"
        />
      </div>
      <div class="preview-pane">
        <div class="pane-label">实时预览</div>
        <div class="preview-content latex-text" v-html="previewHtml" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.latex-editor {
  border: 1px solid var(--color-border, #d9d9d9);
  border-radius: 6px;
  overflow: hidden;
}

.editor-toolbar {
  padding: 6px 8px;
  background: #fafafa;
  border-bottom: 1px solid var(--color-border, #d9d9d9);
}

.editor-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

@media (max-width: 768px) {
  .editor-body {
    grid-template-columns: 1fr;
  }
}

.editor-pane {
  display: flex;
  flex-direction: column;
}

.pane-label {
  font-size: 12px;
  color: #999;
  padding: 4px 8px;
  background: #fafafa;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
}

.code-textarea {
  border: none;
  outline: none;
  resize: vertical;
  padding: 8px;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  min-height: 80px;
  width: 100%;
  box-sizing: border-box;
}

.code-textarea:focus {
  box-shadow: none;
}

.preview-pane {
  border-left: 1px solid var(--color-border, #f0f0f0);
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .preview-pane {
    border-left: none;
    border-top: 1px solid var(--color-border, #f0f0f0);
  }
}

.preview-content {
  padding: 8px;
  min-height: 80px;
  line-height: 1.8;
  overflow-x: auto;
}

.preview-content:empty::before {
  content: '预览区域';
  color: #ccc;
}
</style>
