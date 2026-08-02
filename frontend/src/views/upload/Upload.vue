<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, getLLMStatus, extractFromImage, analyzeQuestion } from '@/api'
import { useGradeStore } from '@/stores'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import LatexEditor from '@/components/editor/LatexEditor.vue'
import LatexText from '@/components/display/LatexText.vue'

const router = useRouter()
const gradeStore = useGradeStore()

// 模式切换
const mode = ref<'single' | 'batch'>('single')

// 单题模式
const formState = reactive({
  stem: '',
  answer_analysis: '',
  grade: gradeStore.currentGrade,
  category: '',
  difficulty: 1
})
const fileList = ref<any[]>([])

// 批量模式
const batchFileList = ref<any[]>([])
const batchQuestions = ref<Array<{
  content: string
  answer_analysis: string
  grade: string
  category: string
  difficulty: number
  imageFile?: File
  imagePreview?: string
}>>([])
const editingIndex = ref<number | null>(null)

// 通用状态
const loading = ref(false)
const aiExtractLoading = ref(false)
const aiAnalyzeLoading = ref(false)
const llmConfigured = ref(false)
const batchProgress = ref('')
const singleProgress = ref('')
const analyzeProgress = ref('')

onMounted(async () => {
  try {
    const status = await getLLMStatus()
    llmConfigured.value = status.configured
  } catch {
    // LLM 未配置或未登录，静默处理
  }
})

// ========== 单题模式 ==========

async function handleAIExtract() {
  if (!fileList.value.length) {
    message.warning('请先选择一张图片')
    return
  }

  aiExtractLoading.value = true
  singleProgress.value = '正在上传图片...'
  try {
    const fileObj = fileList.value[0]
    const file = fileObj.originFileObj || fileObj

    // 验证文件
    if (!file || !(file instanceof File)) {
      throw new Error('无效的文件对象')
    }

    console.log('[Upload] File:', file.name, file.size, file.type)
    singleProgress.value = 'AI 正在识别题目...'
    const result = await extractFromImage(file)
    if (result.success && result.data) {
      singleProgress.value = '识别成功，正在填充表单...'
      const items = Array.isArray(result.data) ? result.data : [result.data]
      if (items.length === 1) {
        // 单题：直接填充表单
        const data = items[0]
        if (data.content) formState.stem = data.content
        if (data.answer_analysis) formState.answer_analysis = data.answer_analysis
        if (data.difficulty) formState.difficulty = data.difficulty
        if (data.category) formState.category = data.category
        singleProgress.value = ''
        message.success('AI 识别完成，已自动填充表单')
      } else {
        // 多题：添加到批量列表并切换模式
        items.forEach((data: any) => {
          batchQuestions.value.push({
            content: data.content || '',
            answer_analysis: data.answer_analysis || '',
            grade: formState.grade,
            category: data.category || '',
            difficulty: data.difficulty || 1
          })
        })
        mode.value = 'batch'
        singleProgress.value = ''
        message.success(`AI 识别到 ${items.length} 道题目，已添加到批量列表`)
      }
    } else {
      singleProgress.value = ''
      message.error('AI 识别失败，请重试')
    }
  } catch (error: any) {
    console.error('[Upload] AI extract error:', error)
    singleProgress.value = ''
    const detail = error?.response?.data?.detail || error.message || 'AI 识别失败'
    message.error(detail)
  } finally {
    aiExtractLoading.value = false
  }
}

async function handleAIAnalyze() {
  if (!formState.stem) {
    message.warning('请先输入题目内容')
    return
  }

  aiAnalyzeLoading.value = true
  analyzeProgress.value = 'AI 正在分析题目...'
  try {
    const result = await analyzeQuestion(formState.stem)
    if (result.success && result.data) {
      analyzeProgress.value = '生成完成，正在填充...'
      if (result.data.answer_analysis) formState.answer_analysis = result.data.answer_analysis
      analyzeProgress.value = ''
      message.success('AI 生成完成')
    } else {
      analyzeProgress.value = ''
      message.error('AI 生成失败，请重试')
    }
  } catch (error: any) {
    analyzeProgress.value = ''
    message.error(error?.response?.data?.detail || 'AI 生成失败')
  } finally {
    aiAnalyzeLoading.value = false
  }
}

async function handleSubmit() {
  if (!formState.stem) {
    message.warning('请输入题目内容')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('content', formState.stem)
    formData.append('answer_analysis', formState.answer_analysis)
    formData.append('grade', formState.grade)
    formData.append('category', formState.category)
    formData.append('difficulty', String(formState.difficulty))
    if (fileList.value.length > 0) {
      formData.append('image', fileList.value[0].originFileObj)
    }

    const response = await api.post('/api/questions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.duplicate) {
      message.warning('已存在相同题目，未重复添加')
    } else {
      message.success('上传成功')
    }
    router.push('/manage')
  } catch (error) {
    console.error('Failed to upload:', error)
  } finally {
    loading.value = false
  }
}

// ========== 批量模式 ==========

async function handleBatchAIExtract() {
  if (!batchFileList.value.length) {
    message.warning('请先选择图片')
    return
  }

  aiExtractLoading.value = true
  batchProgress.value = '准备中...'
  const files = batchFileList.value.map(f => f.originFileObj || f)
  const newQuestions: typeof batchQuestions.value = []
  let successCount = 0
  let failCount = 0

  for (let idx = 0; idx < files.length; idx++) {
    batchProgress.value = `正在识别第 ${idx + 1}/${files.length} 张图片...`
    try {
      const result = await extractFromImage(files[idx])
      if (result.success && result.data) {
        const items = Array.isArray(result.data) ? result.data : [result.data]
        items.forEach((data: any) => {
          newQuestions.push({
            content: data?.content || '',
            answer_analysis: data?.answer_analysis || '',
            grade: formState.grade,
            category: data?.category || '',
            difficulty: data?.difficulty || 1,
            imageFile: files[idx],
            imagePreview: URL.createObjectURL(files[idx])
          })
        })
        successCount++
        batchProgress.value = `第 ${idx + 1}/${files.length} 张识别成功，已提取 ${items.length} 道题`
      } else {
        failCount++
        batchProgress.value = `第 ${idx + 1}/${files.length} 张识别失败`
      }
    } catch {
      failCount++
      batchProgress.value = `第 ${idx + 1}/${files.length} 张识别出错`
    }
  }

  if (newQuestions.length > 0) {
    batchQuestions.value = newQuestions
    batchProgress.value = `识别完成，共提取 ${newQuestions.length} 道题目`
    message.success(`AI 识别完成，共提取 ${newQuestions.length} 道题目`)
  } else {
    batchProgress.value = '识别失败'
    message.error('AI 识别失败，请重试')
  }
  if (failCount > 0) {
    message.warning(`${failCount} 张图片识别失败`)
  }

  aiExtractLoading.value = false
}

function addBatchQuestion() {
  batchQuestions.value.push({
    content: '',
    answer_analysis: '',
    grade: formState.grade,
    category: '',
    difficulty: 1
  })
  editingIndex.value = batchQuestions.value.length - 1
}

function removeBatchQuestion(index: number) {
  batchQuestions.value.splice(index, 1)
  if (editingIndex.value === index) {
    editingIndex.value = null
  }
}

function editBatchQuestion(index: number) {
  editingIndex.value = editingIndex.value === index ? null : index
}

async function handleBatchAIAnalyze(index: number) {
  const q = batchQuestions.value[index]
  if (!q.content) {
    message.warning('请先输入题目内容')
    return
  }

  aiAnalyzeLoading.value = true
  batchProgress.value = `正在为第 ${index + 1} 题生成答案解析...`
  try {
    const result = await analyzeQuestion(q.content)
    if (result.success && result.data) {
      if (result.data.answer_analysis) q.answer_analysis = result.data.answer_analysis
      batchProgress.value = ''
      message.success('AI 生成完成')
    } else {
      batchProgress.value = ''
      message.error('AI 生成失败，请重试')
    }
  } catch (error: any) {
    batchProgress.value = ''
    message.error(error?.response?.data?.detail || 'AI 生成失败')
  } finally {
    aiAnalyzeLoading.value = false
  }
}

async function handleBatchSave() {
  const validQuestions = batchQuestions.value.filter(q => q.content.trim())
  if (!validQuestions.length) {
    message.warning('没有有效的题目可保存')
    return
  }

  loading.value = true
  let successCount = 0
  let duplicateCount = 0
  try {
    // 逐个上传（支持图片）
    for (const q of validQuestions) {
      const formData = new FormData()
      formData.append('content', q.content)
      formData.append('answer_analysis', q.answer_analysis)
      formData.append('grade', q.grade)
      formData.append('category', q.category)
      formData.append('difficulty', String(q.difficulty))
      if (q.imageFile) {
        formData.append('image', q.imageFile)
      }
      const response = await api.post('/api/questions', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (response.data.duplicate) {
        duplicateCount++
      } else {
        successCount++
      }
    }

    let msg = `成功保存 ${successCount} 道题目`
    if (duplicateCount > 0) {
      msg += `，跳过 ${duplicateCount} 道重复题目`
    }
    message.success(msg)
    router.push('/manage')
  } catch (error: any) {
    if (successCount > 0) {
      message.warning(`已保存 ${successCount} 道题目，剩余保存失败`)
      router.push('/manage')
    } else {
      message.error(error?.response?.data?.detail || '保存失败')
    }
  } finally {
    loading.value = false
  }
}

const hasBatchContent = computed(() => batchQuestions.value.some(q => q.content.trim()))
</script>

<template>
  <div class="upload">
    <div class="upload-header">
      <h2>上传题目</h2>
      <a-radio-group v-model:value="mode" button-style="solid">
        <a-radio-button value="single">单题上传</a-radio-button>
        <a-radio-button value="batch">批量上传</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 单题模式 -->
    <template v-if="mode === 'single'">
      <a-form layout="vertical" style="max-width: 800px">
        <a-form-item label="题目内容（支持LaTeX）">
          <LatexEditor
            v-model="formState.stem"
            :rows="6"
            placeholder="输入题目内容（中文用 \text{中文}，公式用 $公式$）"
          />
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
            AI 识别图片并生成题目
          </a-button>
          <div v-if="singleProgress" class="single-progress">
            <a-spin size="small" />
            <span>{{ singleProgress }}</span>
          </div>
          <div v-else-if="llmConfigured" class="ai-hint">上传图片后点击，AI 自动识别题目。如检测到多道题，将自动切换到批量模式</div>
          <a-alert v-else type="warning" show-icon style="margin-top: 8px">
            <template #message>AI 功能未配置</template>
            <template #description>
              请在后端 .env 中配置 LLM_MODEL_ID、LLM_API_KEY、LLM_BASE_URL 以启用 AI 识别功能
            </template>
          </a-alert>
        </a-form-item>

        <a-form-item label="答案与解析（支持LaTeX）">
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
            :disabled="!formState.stem || !llmConfigured"
            @click="handleAIAnalyze"
          >
            AI 生成答案和解析
          </a-button>
          <div v-if="analyzeProgress" class="single-progress">
            <a-spin size="small" />
            <span>{{ analyzeProgress }}</span>
          </div>
          <div v-else-if="llmConfigured" class="ai-hint">根据题目内容，AI 自动生成答案和详细解析</div>
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
    </template>

    <!-- 批量模式 -->
    <template v-else>
      <div class="batch-section">
        <a-form layout="vertical" style="max-width: 800px">
          <a-form-item label="选择图片（支持单张多题或多张单题）">
            <a-upload
              v-model:file-list="batchFileList"
              :before-upload="() => false"
              list-type="picture-card"
              :multiple="true"
            >
              <div v-if="batchFileList.length < 20">
                <plus-outlined />
                <div style="margin-top: 8px">上传图片</div>
              </div>
            </a-upload>
          </a-form-item>

          <a-form-item label="默认年级">
            <a-select v-model:value="formState.grade" style="width: 100%">
              <a-select-option v-for="g in gradeStore.grades" :key="g" :value="g">{{ g }}</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              :loading="aiExtractLoading"
              :disabled="!batchFileList.length || !llmConfigured"
              @click="handleBatchAIExtract"
            >
              AI 批量识别图片
            </a-button>
            <a-button
              style="margin-left: 8px"
              :disabled="batchQuestions.length >= 20"
              @click="addBatchQuestion"
            >
              手动添加题目
            </a-button>
            <div v-if="batchProgress" class="batch-progress">
              <a-spin v-if="aiExtractLoading" size="small" />
              <span>{{ batchProgress }}</span>
            </div>
            <div v-else-if="llmConfigured" class="ai-hint">选择图片后点击，AI 自动识别所有题目（单张图片可识别多题）</div>
            <a-alert v-else type="warning" show-icon style="margin-top: 8px">
              <template #message>AI 功能未配置</template>
              <template #description>
                请在后端 .env 中配置 LLM 相关参数以启用 AI 批量识别功能
              </template>
            </a-alert>
          </a-form-item>
        </a-form>

        <!-- 识别出的题目列表 -->
        <div v-if="batchQuestions.length" class="batch-list">
          <h3>识别结果（共 {{ batchQuestions.length }} 道题）</h3>
          <div class="batch-tip">点击题目可展开编辑，支持修改内容、答案解析、年级、难度等</div>

          <div v-for="(q, index) in batchQuestions" :key="index" class="batch-item">
            <div class="batch-item-header" @click="editBatchQuestion(index)">
              <div class="batch-item-info">
                <span class="batch-item-index">{{ index + 1 }}.</span>
                <img v-if="q.imagePreview" :src="q.imagePreview" class="batch-item-thumb" />
                <span class="batch-item-content">
                  <LatexText :content="q.content || '（未识别到内容）'" />
                </span>
              </div>
              <div class="batch-item-actions">
                <a-tag :color="q.difficulty === 1 ? 'green' : q.difficulty === 2 ? 'orange' : 'red'">
                  {{ q.difficulty === 1 ? '简单' : q.difficulty === 2 ? '中等' : '困难' }}
                </a-tag>
                <a-button type="link" size="small" @click.stop="removeBatchQuestion(index)">
                  删除
                </a-button>
              </div>
            </div>

            <!-- 展开编辑区 -->
            <div v-if="editingIndex === index" class="batch-item-edit">
              <a-form layout="vertical">
                <a-form-item label="题目内容">
                  <LatexEditor
                    v-model="q.content"
                    :rows="4"
                    placeholder="输入题目内容（中文用 \text{中文}，公式用 $公式$）"
                  />
                </a-form-item>
                <a-form-item label="答案与解析">
                  <LatexEditor
                    v-model="q.answer_analysis"
                    :rows="4"
                    placeholder="输入答案与解析"
                  />
                  <a-button
                    type="dashed"
                    size="small"
                    :loading="aiAnalyzeLoading"
                    :disabled="!q.content || !llmConfigured"
                    @click="handleBatchAIAnalyze(index)"
                    style="margin-top: 4px"
                  >
                    AI 生成答案解析
                  </a-button>
                </a-form-item>
                <div class="batch-item-fields">
                  <a-form-item label="年级" style="flex: 1">
                    <a-select v-model:value="q.grade" size="small">
                      <a-select-option v-for="g in gradeStore.grades" :key="g" :value="g">{{ g }}</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="分类" style="flex: 1">
                    <a-input v-model:value="q.category" size="small" placeholder="如：代数、几何" />
                  </a-form-item>
                  <a-form-item label="难度" style="flex: 1">
                    <a-radio-group v-model:value="q.difficulty" size="small">
                      <a-radio :value="1">简单</a-radio>
                      <a-radio :value="2">中等</a-radio>
                      <a-radio :value="3">困难</a-radio>
                    </a-radio-group>
                  </a-form-item>
                </div>
              </a-form>
            </div>
          </div>

          <div class="batch-actions">
            <a-button
              type="primary"
              size="large"
              :loading="loading"
              :disabled="!hasBatchContent"
              @click="handleBatchSave"
            >
              批量保存（{{ batchQuestions.filter(q => q.content.trim()).length }} 道有效题目）
            </a-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.upload {
  max-width: 1000px;
  margin: 0 auto;
}

.upload-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.upload-header h2 {
  margin: 0;
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

.batch-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  font-size: 13px;
  color: #1890ff;
}

.single-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  font-size: 13px;
  color: #1890ff;
}

/* 批量模式样式 */
.batch-section {
  max-width: 900px;
}

.batch-list {
  margin-top: 24px;
}

.batch-list h3 {
  margin-bottom: 8px;
}

.batch-tip {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

.batch-item {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.batch-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.batch-item-header:hover {
  background: var(--color-bg-hover, #f5f5f5);
}

.batch-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.batch-item-index {
  font-weight: 600;
  color: var(--color-primary);
}

.batch-item-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.batch-item-content {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  white-space: nowrap;
}

.batch-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.batch-item-edit {
  padding: 0 16px 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-elevated, #fafafa);
}

.batch-item-fields {
  display: flex;
  gap: 16px;
}

.batch-actions {
  margin-top: 24px;
  text-align: center;
}
</style>
