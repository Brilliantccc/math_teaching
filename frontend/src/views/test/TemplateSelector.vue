<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { api } from '@/api'
import { FileTextOutlined } from '@ant-design/icons-vue'

interface Template {
  id: string
  name: string
  description: string
}

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const templates = ref<Template[]>([])
const loading = ref(false)
const selectedTemplate = ref(props.modelValue || 'standard')

// 加载模板列表
async function loadTemplates() {
  loading.value = true
  try {
    const response = await api.get('/api/tests/templates')
    templates.value = response.data.templates
  } catch (error) {
    console.error('Failed to load templates:', error)
    // 使用默认模板列表
    templates.value = [
      { id: 'standard', name: '标准试卷', description: '经典试卷格式，适合日常测试' },
      { id: 'concise', name: '简洁版', description: '紧凑排版，节省纸张' },
      { id: 'detailed', name: '详解版', description: '包含答案和详细解析' },
      { id: 'professional', name: '专业版', description: '正式考试格式，带题型分组' },
    ]
  } finally {
    loading.value = false
  }
}

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    selectedTemplate.value = newVal
  }
})

// 更新选择
function onSelect(templateId: string) {
  selectedTemplate.value = templateId
  emit('update:modelValue', templateId)
}

onMounted(() => {
  loadTemplates()
})
</script>

<template>
  <div class="template-selector">
    <div class="selector-label">
      <FileTextOutlined /> 试卷模板
    </div>
    <a-spin :spinning="loading">
      <div class="template-grid">
        <div
          v-for="template in templates"
          :key="template.id"
          class="template-card"
          :class="{ active: selectedTemplate === template.id }"
          @click="onSelect(template.id)"
        >
          <div class="template-name">{{ template.name }}</div>
          <div class="template-desc">{{ template.description }}</div>
          <div v-if="selectedTemplate === template.id" class="template-check">✓</div>
        </div>
      </div>
    </a-spin>
  </div>
</template>

<style scoped>
.template-selector {
  margin-bottom: 16px;
}

.selector-label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.template-card {
  position: relative;
  padding: 12px;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.template-card:hover {
  border-color: #1890ff;
  background: #f0f5ff;
}

.template-card.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.template-name {
  font-weight: 500;
  margin-bottom: 4px;
  color: #333;
}

.template-desc {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.template-check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
</style>
