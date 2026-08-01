<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, getLLMStatus, analyzeQuestion } from '@/api'
import { message } from 'ant-design-vue'
import LatexEditor from '@/components/LatexEditor.vue'

const route = useRoute()
const router = useRouter()

const formState = ref({
  title: '',
  content: '',
  answer: '',
  analysis: '',
  grade: '初一',
  difficulty: 1
})

// 题干 = title + content 合并显示
const stem = computed({
  get: () => {
    const parts = [formState.value.title, formState.value.content].filter(Boolean)
    return parts.join('\n')
  },
  set: (val: string) => {
    // 第一行作为 title，全部作为 content
    const lines = val.split('\n')
    formState.value.title = lines[0] || ''
    formState.value.content = val
  }
})

const loading = ref(false)
const aiAnalyzeLoading = ref(false)
const llmConfigured = ref(false)

async function loadQuestion() {
  try {
    const response = await api.get(`/api/questions/${route.params.id}`)
    formState.value = response.data
  } catch (error) {
    console.error('Failed to load question:', error)
  }
}

async function handleAIAnalyze() {
  if (!formState.value.content) {
    message.warning('请先输入题目题干')
    return
  }

  aiAnalyzeLoading.value = true
  try {
    const result = await analyzeQuestion(formState.value.content)
    if (result.success && result.data) {
      if (result.data.answer) formState.value.answer = result.data.answer
      if (result.data.analysis) formState.value.analysis = result.data.analysis
      message.success('AI 生成完成')
    } else {
      message.error('AI 生成失败，请重试')
    }
  } catch (error: any) {
    message.error(error?.response?.data?.detail || 'AI 生成失败')
  } finally {
    aiAnalyzeLoading.value = false
  }
}

async function handleSave() {
  loading.value = true
  try {
    await api.put(`/api/questions/${route.params.id}`, formState.value)
    message.success('保存成功')
    router.push('/manage')
  } catch (error) {
    console.error('Failed to save:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadQuestion()
  try {
    const status = await getLLMStatus()
    llmConfigured.value = status.configured
  } catch {
    // 静默处理
  }
})
</script>

<template>
  <div class="question-edit">
    <h2>编辑题目</h2>

    <a-form layout="vertical" style="max-width: 800px">
      <a-form-item label="题干（支持 LaTeX）">
        <LatexEditor v-model="stem" :rows="6" placeholder="输入题目题干（支持 LaTeX）" />
      </a-form-item>

      <a-form-item label="答案（支持 LaTeX）">
        <LatexEditor v-model="formState.answer" :rows="2" placeholder="答案（支持 LaTeX）" />
      </a-form-item>

      <a-form-item label="解析（支持 LaTeX）">
        <LatexEditor v-model="formState.analysis" :rows="3" placeholder="解析（支持 LaTeX）" />
      </a-form-item>

      <a-form-item>
        <a-button
          type="dashed"
          :loading="aiAnalyzeLoading"
          :disabled="!formState.content || !llmConfigured"
          @click="handleAIAnalyze"
        >
          <template #icon><span>🤖</span></template>
          AI 生成答案和解析
        </a-button>
        <div v-if="llmConfigured" class="ai-hint">根据题干内容，AI 自动生成答案和详细解析</div>
        <a-alert v-else type="warning" show-icon style="margin-top: 8px">
          <template #message>
            AI 功能未配置
          </template>
          <template #description>
            请在后端 .env 中配置 LLM 相关参数以启用 AI 生成功能
          </template>
        </a-alert>
      </a-form-item>

      <a-form-item label="难度">
        <a-radio-group v-model:value="formState.difficulty">
          <a-radio :value="1">简单</a-radio>
          <a-radio :value="2">中等</a-radio>
          <a-radio :value="3">困难</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item>
        <a-space>
          <a-button type="primary" :loading="loading" @click="handleSave">
            保存
          </a-button>
          <a-button @click="router.back()">取消</a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.question-edit {
  max-width: 900px;
  margin: 0 auto;
}

.ai-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
