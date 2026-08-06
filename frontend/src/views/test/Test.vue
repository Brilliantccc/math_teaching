<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { GRADES } from '@/stores/grade'
import { message, notification, Modal } from 'ant-design-vue'
import {
  SaveOutlined, ReloadOutlined, FileTextOutlined,
  EyeOutlined, EyeInvisibleOutlined, DownloadOutlined,
  DeleteOutlined, PlusOutlined, LoadingOutlined
} from '@ant-design/icons-vue'
import LatexText from '@/components/display/LatexText.vue'
import TemplateSelector from './TemplateSelector.vue'

const router = useRouter()
const gradeStore = useGradeStore()

const loading = ref(false)
const saving = ref(false)
const questions = ref<any[]>([])
const testId = ref<number | null>(null)
const showAnswer = ref(false)

// PDF导出状态
const exportingPdf = ref(false)
const exportProgress = ref(0)
const currentTaskId = ref<string | null>(null)

// 模板选择
const selectedTemplate = ref('standard')

// PDF预览
const previewVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)

// 分类列表（从数据库动态加载）
const categories = ref<string[]>([])

// 题型列表（从数据库动态加载）
const questionTypes = ref<{type: string, count: number, difficulty_counts?: Record<number, number>}[]>([])
const questionTypeLoading = ref(false)

// 每道题的分值：{question_id: score}
const questionScores = ref<Record<number, number>>({})

// 选中的题目（用于批量操作）
const selectedQuestionIds = ref<number[]>([])

// 按难度生成数量
const difficultyCount = ref({
  1: 5,   // 简单
  2: 5,   // 中等
  3: 5    // 困难
})

// 难度选项
const DIFFICULTY_OPTIONS = [
  { value: 1, label: '简单', color: 'green' },
  { value: 2, label: '中等', color: 'orange' },
  { value: 3, label: '困难', color: 'red' }
]

// 获取某题型某难度的可用数量
function getAvailableCount(type: string, difficulty: number): number {
  const qt = questionTypes.value.find(q => q.type === type)
  if (qt && qt.difficulty_counts) {
    return qt.difficulty_counts[difficulty] || 0
  }
  // 如果没有详细数据，返回总数作为上限
  return qt?.count || 0
}

// 按题型生成数量
const questionTypeCounts = ref<Record<string, number>>({})

// 按题型+难度配置数量
const questionTypeDifficultyCounts = ref<Record<string, Record<number, number>>>({})

const formState = ref({
  name: '',
  count: 10,
  tags: [] as string[],
  difficulties: [1, 2, 3],
  grade: gradeStore.currentGrade === '全部' ? '全部' : gradeStore.currentGrade
})

// 计算总分
const totalScore = computed(() => {
  return questions.value.reduce((sum, q) => {
    return sum + (questionScores.value[q.id] || 10)
  }, 0)
})

// 设置单道题的分值
function setQuestionScore(questionId: number, score: number) {
  questionScores.value[questionId] = score
}

// 删除单道题
function removeQuestion(questionId: number) {
  const index = questions.value.findIndex(q => q.id === questionId)
  if (index !== -1) {
    questions.value.splice(index, 1)
    delete questionScores.value[questionId]
    selectedQuestionIds.value = selectedQuestionIds.value.filter(id => id !== questionId)
  }
}

// 批量删除选中的题目
function removeSelectedQuestions() {
  if (selectedQuestionIds.value.length === 0) {
    message.warning('请先选择要删除的题目')
    return
  }
  questions.value = questions.value.filter(q => !selectedQuestionIds.value.includes(q.id))
  selectedQuestionIds.value.forEach(id => delete questionScores.value[id])
  selectedQuestionIds.value = []
  message.success('已删除选中的题目')
}

// 全选/取消全选
function toggleSelectAll() {
  if (selectedQuestionIds.value.length === questions.value.length) {
    selectedQuestionIds.value = []
  } else {
    selectedQuestionIds.value = questions.value.map(q => q.id)
  }
}

// 切换单题选中状态
function toggleQuestionSelect(questionId: number) {
  const index = selectedQuestionIds.value.indexOf(questionId)
  if (index === -1) {
    selectedQuestionIds.value.push(questionId)
  } else {
    selectedQuestionIds.value.splice(index, 1)
  }
}

// 解析images JSON字符串为数组
function parseImages(images: string | undefined): string[] {
  if (!images) return []
  try {
    const parsed = JSON.parse(images)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// 获取图片URL（处理相对路径）
function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http') || path.startsWith('data:')) return path
  return `http://localhost:8000/${path}`
}

// 清空所有题目
function clearAllQuestions() {
  questions.value = []
  questionScores.value = {}
  selectedQuestionIds.value = []
  testId.value = null
}

// 加载分类列表
async function loadCategories() {
  try {
    const response = await api.get('/api/questions/categories')
    categories.value = response.data.categories || []
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

// 加载题型列表
async function loadQuestionTypes() {
  questionTypeLoading.value = true
  try {
    const gradeParam = gradeStore.getGradeParam()
    const response = await api.get('/api/questions/question-types', {
      params: { grade: gradeParam }
    })
    questionTypes.value = response.data.question_types || []

    // 清空并重新初始化用户配置（从0开始）
    const newTypeCounts: Record<string, number> = {}
    const newTypeDifficultyCounts: Record<string, Record<number, number>> = {}

    for (const qt of questionTypes.value) {
      // 用户配置的生成数量从0开始
      newTypeCounts[qt.type] = 0
      newTypeDifficultyCounts[qt.type] = { 1: 0, 2: 0, 3: 0 }
    }

    questionTypeCounts.value = newTypeCounts
    questionTypeDifficultyCounts.value = newTypeDifficultyCounts

    // 注意：可用数量通过 questionTypes 数组中的 difficulty_counts 字段传递
    // 不需要额外存储，直接从 questionTypes 获取即可
  } catch (error) {
    console.error('Failed to load question types:', error)
  } finally {
    questionTypeLoading.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadQuestionTypes()
})

// 监听年级变化，重新加载题型统计
watch(() => formState.value.grade, (newGrade) => {
  gradeStore.setGrade(newGrade)
  loadQuestionTypes()
})

const testName = computed(() => formState.value.name || `${formState.value.grade}数学试卷`)

// 追加生成（在现有题目基础上添加）
async function appendGenerate() {
  loading.value = true
  try {
    // 获取年级参数（支持"全部"、"初中全部"、"高中全部"等）
    const gradeParam = gradeStore.getGradeParam()

    // 优先检查是否有配置题型+难度数量
    const hasTypeDifficultyConfig = Object.values(questionTypeDifficultyCounts.value).some(
      counts => Object.values(counts).some(count => count > 0)
    )

    // 其次检查是否有配置题型数量
    const hasTypeConfig = Object.values(questionTypeCounts.value).some(count => count > 0)

    let allNewIds: number[] = []

    if (hasTypeDifficultyConfig) {
      // 按题型+难度配置生成
      const response = await api.post('/api/tests/auto', {
        question_type_difficulty_counts: questionTypeDifficultyCounts.value,
        tags: formState.value.tags,
        grade: gradeParam
      })
      allNewIds = response.data.question_ids || []
    } else if (hasTypeConfig) {
      // 按题型配置生成
      const response = await api.post('/api/tests/auto', {
        question_type_counts: questionTypeCounts.value,
        tags: formState.value.tags,
        difficulties: formState.value.difficulties,
        grade: gradeParam
      })
      allNewIds = response.data.question_ids || []
    } else {
      // 按难度分别生成
      for (const [diff, count] of Object.entries(difficultyCount.value)) {
        if (count > 0) {
          const response = await api.post('/api/tests/auto', {
            count: count,
            tags: formState.value.tags,
            difficulties: [parseInt(diff)],
            grade: gradeParam
          })
          allNewIds.push(...response.data.question_ids)
        }
      }
    }

    if (allNewIds.length === 0) {
      message.warning('没有符合条件的题目')
      return
    }

    // 获取新题目的详情
    const detailResp = await api.get('/api/questions/batch', {
      params: { ids: allNewIds.join(',') }
    })
    const newQuestions = detailResp.data.questions

    // 追加到现有题目（避免重复）
    const existingIds = new Set(questions.value.map(q => q.id))
    let addedCount = 0
    for (const q of newQuestions) {
      if (!existingIds.has(q.id)) {
        questions.value.push(q)
        questionScores.value[q.id] = 10 // 默认分值
        addedCount++
      }
    }

    message.success(`已追加 ${addedCount} 道题目`)

    // 生成后刷新题型数据，更新可用数量
    await loadQuestionTypes()
  } catch (error) {
    console.error('Failed to generate test:', error)
  } finally {
    loading.value = false
  }
}

// 清空重来
async function regenerate() {
  clearAllQuestions()
  await appendGenerate()
}

// 开始生成（首次）
async function startGenerate() {
  clearAllQuestions()
  await appendGenerate()
}

// 获取题型对应的颜色
function getTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    '单项选择': 'blue',
    '多项选择': 'purple',
    '填空题': 'green',
    '解答题': 'orange',
    '判断题': 'purple',
    '计算题': 'cyan'
  }
  return colorMap[type] || 'default'
}

async function saveTest() {
  if (questions.value.length === 0) {
    message.warning('请先生成试卷')
    return
  }
  saving.value = true
  try {
    const response = await api.post('/api/tests', {
      name: testName.value,
      question_ids: questions.value.map(q => q.id),
      score_per_question: 10, // 保留默认值
      question_scores: questionScores.value
    })
    testId.value = response.data.id
    message.success('试卷已保存')
  } catch (error) {
    console.error('Failed to save test:', error)
  } finally {
    saving.value = false
  }
}

async function exportPdf() {
  if (!testId.value) {
    message.warning('请先保存试卷')
    return
  }

  exportingPdf.value = true
  exportProgress.value = 0

  try {
    const token = localStorage.getItem('token') || ''

    // 方式1：尝试异步导出（适合大量题目）
    if (questions.value.length > 20) {
      const taskResponse = await fetch(`http://localhost:8000/api/tests/async`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_ids: questions.value.map(q => q.id),
          title: testName.value,
          question_scores: questionScores.value
        })
      })

      if (taskResponse.ok) {
        const { task_id } = await taskResponse.json()
        currentTaskId.value = task_id

        // 轮询任务状态
        await pollTaskStatus(task_id, token)
        return
      }
    }

    // 方式2：同步导出（题目较少时直接下载）
    const response = await fetch(`http://localhost:8000/api/tests/${testId.value}/pdf`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (!response.ok) throw new Error('导出失败')

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${testName.value}.pdf`
    a.click()
    URL.revokeObjectURL(url)

    message.success('PDF 已导出')
  } catch (error) {
    message.error('导出PDF失败')
  } finally {
    exportingPdf.value = false
    exportProgress.value = 0
    currentTaskId.value = null
  }
}

// 轮询异步任务状态
async function pollTaskStatus(taskId: string, token: string) {
  const maxAttempts = 60 // 最多等待60秒
  let attempts = 0

  const poll = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/tests/task/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) throw new Error('查询失败')

      const data = await response.json()
      exportProgress.value = data.progress || 0

      if (data.status === 'completed') {
        // 下载PDF
        const downloadResponse = await fetch(`http://localhost:8000/api/tests/download/${taskId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (downloadResponse.ok) {
          const blob = await downloadResponse.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `${testName.value}.pdf`
          a.click()
          URL.revokeObjectURL(url)

          message.success('PDF 已导出')
        }
        return
      }

      if (data.status === 'failed') {
        throw new Error(data.error || '生成失败')
      }

      // 继续轮询
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(poll, 1000)
      } else {
        throw new Error('超时')
      }
    } catch (error) {
      message.error('导出PDF失败')
      exportingPdf.value = false
    }
  }

  await poll()
}

// 预览PDF
async function previewPdf() {
  if (questions.value.length === 0) {
    message.warning('请先添加题目')
    return
  }

  previewLoading.value = true
  previewVisible.value = true

  try {
    const token = localStorage.getItem('token')
    const response = await fetch('http://localhost:8000/api/tests/preview', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question_ids: questions.value.map(q => q.id),
        title: testName.value || '数学试卷',
        template: selectedTemplate.value,
        question_scores: questionScores.value
      })
    })

    if (!response.ok) throw new Error('预览失败')

    const blob = await response.blob()
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    message.error('预览PDF失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

// 关闭预览
function closePreview() {
  previewVisible.value = false
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

function moveQuestion(index: number, direction: -1 | 1) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= questions.value.length) return
  const temp = questions.value[index]
  questions.value[index] = questions.value[newIndex]
  questions.value[newIndex] = temp
}
</script>

<template>
  <div class="test">
    <div class="page-header">
      <h2>智能组卷</h2>
      <a-button @click="router.push('/test-manage')">
        <FileTextOutlined /> 已保存试卷
      </a-button>
    </div>

    <!-- 配置面板 -->
    <div class="config-panel">
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="试卷名称">
              <a-input v-model:value="formState.name" :placeholder="`${formState.grade}数学试卷`" />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="年级">
              <a-select v-model:value="formState.grade" style="width: 100%">
                <a-select-option v-for="g in GRADES" :key="g" :value="g">{{ g }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="按题型和难度生成数量">
              <template #label>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span>按题型和难度生成数量</span>
                  <a-button type="link" size="small" @click="loadQuestionTypes" :loading="questionTypeLoading">
                    🔄 刷新题型数据
                  </a-button>
                </div>
              </template>
              <div class="type-difficulty-config" v-if="questionTypes.length > 0">
                <div v-for="qt in questionTypes" :key="qt.type" class="type-row">
                  <div class="type-header">
                    <a-tag :color="getTypeColor(qt.type)">{{ qt.type }}</a-tag>
                    <span class="type-total">共 {{ qt.count }} 题可用</span>
                  </div>
                  <div class="difficulty-row">
                    <div v-for="diff in DIFFICULTY_OPTIONS" :key="diff.value" class="difficulty-item">
                      <a-tag :color="diff.color" size="small">{{ diff.label }}：{{ questionTypeDifficultyCounts[qt.type]?.[diff.value] || 0 }} / {{ getAvailableCount(qt.type, diff.value) }}</a-tag>
                      <a-input-number
                        v-model:value="questionTypeDifficultyCounts[qt.type][diff.value]"
                        :min="0"
                        :max="getAvailableCount(qt.type, diff.value)"
                        size="small"
                        style="width: 60px"
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="difficulty-config">
                <a-spin :spinning="questionTypeLoading" />
                <span v-if="!questionTypeLoading" style="color: #999">暂无题型数据，请先添加题目</span>
              </div>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 模板选择 -->
        <a-row :gutter="16">
          <a-col :span="24">
            <TemplateSelector v-model="selectedTemplate" />
          </a-col>
        </a-row>

        <a-form-item>
          <a-space>
            <!-- 没有题目时显示"开始生成"，有题目时显示"追加生成" -->
            <a-button
              type="primary"
              :loading="loading"
              @click="questions.length === 0 ? startGenerate() : appendGenerate()"
            >
              <PlusOutlined />
              {{ questions.length === 0 ? '开始生成' : '追加生成' }}
            </a-button>

            <!-- 保存试卷：有题目时可用 -->
            <a-button
              :loading="saving"
              :disabled="questions.length === 0"
              @click="saveTest"
            >
              <SaveOutlined /> 保存试卷
            </a-button>

            <!-- 预览PDF：有题目时可用 -->
            <a-button
              :disabled="questions.length === 0"
              @click="previewPdf"
            >
              <EyeOutlined /> 预览PDF
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <!-- 试卷预览 -->
    <div v-if="questions.length > 0" class="paper-preview">
      <!-- 试卷标题栏 -->
      <div class="paper-header">
        <h1 class="paper-title">{{ testName }}</h1>
        <div class="paper-meta">
          <span>年级：{{ formState.grade }}</span>
          <span>时间：90分钟</span>
          <span>总分：{{ totalScore }}分</span>
        </div>
      </div>

      <!-- 答案显示切换 -->
      <div class="paper-toolbar">
        <div class="toolbar-left">
          <a-checkbox :checked="selectedQuestionIds.length === questions.length && questions.length > 0" @change="toggleSelectAll">
            全选
          </a-checkbox>
          <a-button v-if="selectedQuestionIds.length > 0" size="small" danger @click="removeSelectedQuestions">
            <DeleteOutlined /> 删除选中 ({{ selectedQuestionIds.length }})
          </a-button>
          <a-button size="small" @click="clearAllQuestions">
            清空
          </a-button>
        </div>
        <div class="toolbar-right">
          <a-button @click="showAnswer = !showAnswer" size="small">
            <EyeInvisibleOutlined v-if="showAnswer" />
            <EyeOutlined v-else />
            {{ showAnswer ? '隐藏答案' : '显示答案' }}
          </a-button>
          <span class="score-info">共 {{ questions.length }} 题，满分 {{ totalScore }} 分</span>
        </div>
      </div>

      <!-- 题目列表 -->
      <div class="question-list">
        <div v-for="(q, index) in questions" :key="q.id" class="question-item">
          <div class="question-row">
            <div class="question-left">
              <a-checkbox
                :checked="selectedQuestionIds.includes(q.id)"
                @change="() => toggleQuestionSelect(q.id)"
                style="margin-right: 8px"
              />
              <div class="question-number">
                <span class="num">{{ index + 1 }}.</span>
                <a-tag :color="q.difficulty === 1 ? 'green' : q.difficulty === 2 ? 'orange' : 'red'" size="small">
                  {{ q.difficulty === 1 ? '简单' : q.difficulty === 2 ? '中等' : '困难' }}
                </a-tag>
                <a-tag v-if="q.question_type" :color="getTypeColor(q.question_type)" size="small">
                  {{ q.question_type }}
                </a-tag>
              </div>
              <div class="question-content">
                <LatexText :content="q.content" />
              </div>
              <!-- 图片单独展示在题目下方 -->
              <div v-if="parseImages(q.images).length > 0" class="question-images">
                <div v-for="(img, imgIndex) in parseImages(q.images)" :key="imgIndex" class="question-image-item">
                  <img :src="getImageUrl(img)" :alt="`配图${imgIndex + 1}`" loading="lazy" />
                </div>
              </div>
            </div>
            <div class="question-right">
              <div class="score-input">
                <a-input-number
                  :value="questionScores[q.id] || 10"
                  :min="1"
                  :max="100"
                  size="small"
                  style="width: 70px"
                  @change="(val: number) => setQuestionScore(q.id, val || 10)"
                />
                <span class="score-unit">分</span>
              </div>
              <div class="question-actions">
                <a-button size="small" :disabled="index === 0" @click="moveQuestion(index, -1)">↑</a-button>
                <a-button size="small" :disabled="index === questions.length - 1" @click="moveQuestion(index, 1)">↓</a-button>
                <a-button size="small" danger @click="removeQuestion(q.id)">×</a-button>
              </div>
            </div>
          </div>

          <!-- 答题区域 -->
          <div class="answer-area" v-if="!showAnswer">
            <div class="answer-line"></div>
          </div>

          <!-- 答案与解析 -->
          <div v-if="showAnswer && q.answer_analysis" class="answer-section">
            <div class="answer-label">答案与解析</div>
            <LatexText :content="q.answer_analysis" />
          </div>
        </div>
      </div>

      <!-- 试卷底部 -->
      <div class="paper-footer">
        <div class="footer-line">— 试卷结束 —</div>
      </div>
    </div>

    <a-empty v-else-if="!loading" description="配置参数后点击自动生成" style="margin-top: 48px" />
  </div>

  <!-- PDF预览模态框 -->
  <a-modal
    v-model:open="previewVisible"
    title="PDF预览"
    width="900px"
    :footer="null"
    @afterClose="closePreview"
  >
    <div class="preview-container">
      <a-spin :spinning="previewLoading">
        <iframe
          v-if="previewUrl"
          :src="previewUrl"
          class="pdf-preview-frame"
        />
        <a-empty v-else-if="!previewLoading" description="暂无预览" />
      </a-spin>
    </div>
  </a-modal>
</template>

<style scoped>
.test {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 配置面板 */
.config-panel {
  background: var(--color-bg-hover);
  padding: 20px 24px;
  border-radius: var(--radius-lg);
  margin-top: 16px;
}

/* 难度配置 */
.difficulty-config {
  display: flex;
  gap: 24px;
  align-items: center;
}

.difficulty-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 题型+难度配置 */
.type-difficulty-config {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.type-row {
  background: var(--color-bg-hover);
  padding: 12px 16px;
  border-radius: var(--radius-md);
}

.type-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.type-total {
  font-size: 12px;
  color: var(--color-text-muted);
}

.difficulty-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.difficulty-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 旧样式保留兼容 */
.question-type-config {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.unit {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* 工具栏 */
.paper-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 8px 12px;
  background: var(--color-bg-hover);
  border-radius: var(--radius-md);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-info {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* 试卷预览 */
.paper-preview {
  margin-top: 24px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 40px 48px;
  box-shadow: var(--shadow-rest);
}

.paper-header {
  text-align: center;
  border-bottom: 2px solid #333;
  padding-bottom: 20px;
  margin-bottom: 24px;
}

.paper-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 0 0 12px 0;
}

.paper-meta {
  display: flex;
  justify-content: center;
  gap: 32px;
  font-size: 14px;
  color: #666;
}

/* 题目列表 */
.question-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.question-item {
  padding-bottom: 20px;
  border-bottom: 1px dashed #e0e0e0;
}

.question-item:last-child {
  border-bottom: none;
}

.question-row {
  display: flex;
  gap: 8px;
}

.question-left {
  flex: 1;
}

.question-number {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.question-number .num {
  font-weight: bold;
  font-size: 15px;
  color: #333;
}

.question-number .score {
  font-size: 13px;
  color: #888;
}

.question-content {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}

/* 图片展示区域 */
.question-images {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.question-image-item {
  max-width: 300px;
}

.question-image-item img {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
  background: #fafafa;
  object-fit: contain;
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-image-item img:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
}

.question-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  min-width: 100px;
}

.score-input {
  display: flex;
  align-items: center;
  gap: 4px;
}

.question-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.question-item:hover .question-actions {
  opacity: 1;
}

/* 答题区域 */
.answer-area {
  margin-top: 12px;
  padding-left: 24px;
}

.answer-line {
  border-bottom: 1px solid #ccc;
  height: 32px;
}

/* 答案与解析 */
.answer-section {
  margin-top: 12px;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-primary);
  font-size: 14px;
  line-height: 1.8;
  color: #555;
}

.answer-label {
  font-size: 12px;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 4px;
}

/* 试卷底部 */
.paper-footer {
  margin-top: 32px;
  text-align: center;
}

.footer-line {
  font-size: 13px;
  color: #999;
}

/* PDF预览模态框 */
.preview-container {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-preview-frame {
  width: 100%;
  height: 600px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

/* 打印样式 */
@media print {
  .config-panel,
  .paper-toolbar,
  .question-actions {
    display: none !important;
  }

  .paper-preview {
    border: none;
    box-shadow: none;
    padding: 20px;
    margin: 0;
  }

  .answer-area {
    display: none !important;
  }

  .answer-section {
    display: block !important;
    background: #fff;
    border-left: 1px solid #ccc;
  }
}
</style>
