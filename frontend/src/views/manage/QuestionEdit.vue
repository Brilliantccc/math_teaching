<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, getLLMStatus, analyzeQuestion } from '@/api'
import { message } from 'ant-design-vue'
import LatexEditor from '@/components/editor/LatexEditor.vue'
import { GRADES } from '@/stores/grade'

// 年级选项（排除"全部"）
const gradeOptions = GRADES.filter(g => g !== '全部')

const route = useRoute()
const router = useRouter()

const formState = ref({
  content: '',
  answer_analysis: '',
  grade: '初一',
  difficulty: 1
})

const loading = ref(false)
const aiAnalyzeLoading = ref(false)
const llmConfigured = ref(false)

// 图片相关状态
const fileList = ref<any[]>([])
const existingImages = ref<string[]>([])

// 解析图片JSON数组
function parseImages(imagesJson: string): string[] {
  try {
    return JSON.parse(imagesJson || '[]')
  } catch {
    return []
  }
}

// 图片URL处理
function getImageUrl(imgPath: string): string {
  if (imgPath.startsWith('http')) return imgPath
  return `${api.defaults.baseURL}/${imgPath}`
}

async function loadQuestion() {
  try {
    const response = await api.get(`/api/questions/${route.params.id}`)
    formState.value = response.data
    // 解析已有图片
    existingImages.value = parseImages(response.data.images)
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
      if (result.data.answer_analysis) formState.value.answer_analysis = result.data.answer_analysis
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
    const formData = new FormData()
    formData.append('content', formState.value.content)
    formData.append('answer_analysis', formState.value.answer_analysis)
    formData.append('grade', formState.value.grade)
    formData.append('difficulty', String(formState.value.difficulty))

    // 处理图片
    if (fileList.value.length > 0) {
      // 有新上传的图片
      fileList.value.forEach(fileObj => {
        const file = fileObj.originFileObj || fileObj
        if (file instanceof File) {
          formData.append('images', file)
        }
      })
    } else if (existingImages.value.length > 0) {
      // 保留已有图片
      formData.append('existing_images', JSON.stringify(existingImages.value))
    }

    await api.put(`/api/questions/${route.params.id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
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
      <a-form-item label="图片">
        <!-- 显示已有图片 -->
        <div v-if="existingImages.length > 0" class="existing-images">
          <img
            v-for="(img, index) in existingImages"
            :key="index"
            :src="getImageUrl(img)"
            class="existing-image"
          />
        </div>

        <!-- 上传新图片 -->
        <a-upload
          v-model:file-list="fileList"
          :before-upload="() => false"
          list-type="picture"
          :max-count="5"
        >
          <a-button>选择图片</a-button>
        </a-upload>
        <div class="upload-hint">可上传多张图片，如几何图形、函数图像等</div>
      </a-form-item>

      <a-form-item label="题干（支持 LaTeX）">
        <LatexEditor
          v-model="formState.content"
          :images="existingImages"
          :rows="6"
          placeholder="输入题目题干（中文用 \text{中文}，公式用 $公式$）"
        />
      </a-form-item>

      <a-form-item label="答案与解析（支持 LaTeX）">
        <LatexEditor
          v-model="formState.answer_analysis"
          :rows="6"
          placeholder="输入答案与解析（用 ---解析--- 分隔答案和解析部分）"
        />
        <div class="aa-hint">格式：先写答案，然后写 ---解析---，再写解析内容。中文用 \text{中文}</div>
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

      <a-form-item label="年级">
        <a-select v-model:value="formState.grade" placeholder="选择年级" style="width: 120px">
          <a-select-option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</a-select-option>
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
  color: var(--color-text-muted);
  margin-top: 4px;
}

.aa-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.existing-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.existing-image {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}
</style>
