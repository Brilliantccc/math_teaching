<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, getLLMStatus, extractFromImage, analyzeQuestion } from '@/api'
import { useGradeStore } from '@/stores'
import { message } from 'ant-design-vue'
import LatexEditor from '@/components/LatexEditor.vue'

const router = useRouter()
const gradeStore = useGradeStore()

const formState = reactive({
  stem: '',
  answer: '',
  analysis: '',
  grade: gradeStore.currentGrade,
  category: '',
  difficulty: 1
})
const fileList = ref<any[]>([])
const loading = ref(false)
const aiExtractLoading = ref(false)
const aiAnalyzeLoading = ref(false)
const llmConfigured = ref(false)

onMounted(async () => {
  try {
    const status = await getLLMStatus()
    llmConfigured.value = status.configured
  } catch {
    // LLM 未配置或未登录，静默处理
  }
})

async function handleAIExtract() {
  if (!fileList.value.length) {
    message.warning('请先选择一张图片')
    return
  }

  aiExtractLoading.value = true
  try {
    const file = fileList.value[0].originFileObj || fileList.value[0]
    const result = await extractFromImage(file)
    if (result.success && result.data) {
      const data = result.data
      // 合并 title 和 content 到 stem
      const stemParts = [data.title, data.content].filter(Boolean)
      if (stemParts.length) formState.stem = stemParts.join('\n')
      if (data.answer) formState.answer = data.answer
      if (data.analysis) formState.analysis = data.analysis
      if (data.difficulty) formState.difficulty = data.difficulty
      if (data.category) formState.category = data.category
      message.success('AI 识别完成，已自动填充表单')
    } else {
      message.error('AI 识别失败，请重试')
    }
  } catch (error: any) {
    message.error(error?.response?.data?.detail || 'AI 识别失败')
  } finally {
    aiExtractLoading.value = false
  }
}

async function handleAIAnalyze() {
  if (!formState.stem) {
    message.warning('请先输入题目题干')
    return
  }

  aiAnalyzeLoading.value = true
  try {
    const result = await analyzeQuestion(formState.stem)
    if (result.success && result.data) {
      if (result.data.answer) formState.answer = result.data.answer
      if (result.data.analysis) formState.analysis = result.data.analysis
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

async function handleSubmit() {
  if (!formState.stem) {
    message.warning('请输入题目题干')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    // 将 stem 同时作为 title 和 content 发送
    formData.append('title', formState.stem.split('\n')[0])
    formData.append('content', formState.stem)
    formData.append('answer', formState.answer)
    formData.append('analysis', formState.analysis)
    formData.append('grade', formState.grade)
    formData.append('category', formState.category)
    formData.append('difficulty', String(formState.difficulty))
    if (fileList.value.length > 0) {
      formData.append('image', fileList.value[0].originFileObj)
    }

    await api.post('/api/questions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    message.success('上传成功')
    router.push('/manage')
  } catch (error) {
    console.error('Failed to upload:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="upload">
    <h2>上传题目</h2>

    <a-form layout="vertical" style="max-width: 800px">
      <a-form-item label="题干（支持 LaTeX）">
        <LatexEditor v-model="formState.stem" :rows="6" placeholder="输入题目题干（用 $...$ 行内公式，$$...$$ 块级公式）" />
      </a-form-item>

      <a-form-item label="图片">
        <a-upload
          v-model:file-list="fileList"
          :before-upload="() => false"
          list-type="picture"
          :max-count="1"
        >
          <a-button>选择图片</a-button>
        </a-upload>
      </a-form-item>

      <a-form-item>
        <a-button
          type="dashed"
          :loading="aiExtractLoading"
          :disabled="!fileList.length || !llmConfigured"
          @click="handleAIExtract"
        >
          <template #icon><span>🤖</span></template>
          AI 识别图片并生成题目
        </a-button>
        <div v-if="llmConfigured" class="ai-hint">上传图片后点击，AI 将自动识别图片中的题目并填充表单</div>
        <a-alert v-else type="warning" show-icon style="margin-top: 8px">
          <template #message>
            AI 功能未配置
          </template>
          <template #description>
            请在后端 .env 中配置 LLM_MODEL_ID、LLM_API_KEY、LLM_BASE_URL 以启用 AI 识别功能
          </template>
        </a-alert>
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
          :disabled="!formState.stem || !llmConfigured"
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

      <a-form-item label="年级">
        <a-select v-model:value="formState.grade" style="width: 100%">
          <a-select-option v-for="g in gradeStore.grades" :key="g" :value="g">{{ g }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="难度">
        <a-radio-group v-model:value="formState.difficulty">
          <a-radio :value="1">简单</a-radio>
          <a-radio :value="2">中等</a-radio>
          <a-radio :value="3">困难</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item>
        <a-button type="primary" :loading="loading" @click="handleSubmit">
          提交
        </a-button>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.upload {
  max-width: 900px;
  margin: 0 auto;
}

.ai-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
