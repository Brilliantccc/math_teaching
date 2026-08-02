<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { GRADES } from '@/stores/grade'
import { message } from 'ant-design-vue'
import {
  SaveOutlined, ReloadOutlined, FileTextOutlined,
  EyeOutlined, EyeInvisibleOutlined, DownloadOutlined
} from '@ant-design/icons-vue'
import LatexText from '@/components/display/LatexText.vue'

const router = useRouter()
const gradeStore = useGradeStore()

const loading = ref(false)
const saving = ref(false)
const questions = ref<any[]>([])
const testId = ref<number | null>(null)
const showAnswer = ref(false)
const scorePerQuestion = ref(10)

const formState = ref({
  name: '',
  count: 10,
  tags: [] as string[],
  difficulties: [1, 2, 3],
  grade: gradeStore.currentGrade,
  category: ''
})

const totalScore = computed(() => questions.value.length * scorePerQuestion.value)

const testName = computed(() => formState.value.name || `${formState.value.grade}数学试卷`)

async function autoGenerate() {
  loading.value = true
  questions.value = []
  testId.value = null
  try {
    const response = await api.post('/api/tests/auto', {
      count: formState.value.count,
      tags: formState.value.tags,
      difficulties: formState.value.difficulties,
      grade: formState.value.grade,
      category: formState.value.category
    })
    const ids: number[] = response.data.question_ids
    if (ids.length === 0) {
      message.warning('没有符合条件的题目')
      return
    }
    const detailResp = await api.get('/api/questions/batch', {
      params: { ids: ids.join(',') }
    })
    questions.value = detailResp.data.questions
    message.success(`已生成 ${ids.length} 道题目`)
  } catch (error) {
    console.error('Failed to generate test:', error)
  } finally {
    loading.value = false
  }
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
      score_per_question: scorePerQuestion.value
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
  try {
    const token = localStorage.getItem('token')
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
          <a-col :span="4">
            <a-form-item label="分类">
              <a-select v-model:value="formState.category" allow-clear placeholder="全部" style="width: 100%">
                <a-select-option value="数与式">数与式</a-select-option>
                <a-select-option value="代数方程">代数方程</a-select-option>
                <a-select-option value="几何">几何</a-select-option>
                <a-select-option value="统计与概率">统计与概率</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="题目数量">
              <a-input-number v-model:value="formState.count" :min="1" :max="50" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="4">
            <a-form-item label="每题分值">
              <a-input-number v-model:value="scorePerQuestion" :min="1" :max="100" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="难度">
              <a-checkbox-group v-model:value="formState.difficulties">
                <a-checkbox :value="1">简单</a-checkbox>
                <a-checkbox :value="2">中等</a-checkbox>
                <a-checkbox :value="3">困难</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-space>
            <a-button type="primary" :loading="loading" @click="autoGenerate">
              <ReloadOutlined /> 自动生成
            </a-button>
            <a-button :loading="saving" :disabled="questions.length === 0" @click="saveTest">
              <SaveOutlined /> 保存试卷
            </a-button>
            <a-button :disabled="!testId" @click="exportPdf">
              <DownloadOutlined /> 导出PDF
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
        <a-button @click="showAnswer = !showAnswer" size="small">
          <EyeInvisibleOutlined v-if="showAnswer" />
          <EyeOutlined v-else />
          {{ showAnswer ? '隐藏答案' : '显示答案' }}
        </a-button>
        <span class="score-info">共 {{ questions.length }} 题，每题 {{ scorePerQuestion }} 分，满分 {{ totalScore }} 分</span>
      </div>

      <!-- 题目列表 -->
      <div class="question-list">
        <div v-for="(q, index) in questions" :key="q.id" class="question-item">
          <div class="question-row">
            <div class="question-left">
              <div class="question-number">
                <span class="num">{{ index + 1 }}.</span>
                <span class="score">（{{ scorePerQuestion }}分）</span>
              </div>
              <div class="question-content">
                <LatexText :content="q.content" />
              </div>
            </div>
            <div class="question-actions">
              <a-button size="small" :disabled="index === 0" @click="moveQuestion(index, -1)">↑</a-button>
              <a-button size="small" :disabled="index === questions.length - 1" @click="moveQuestion(index, 1)">↓</a-button>
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

.paper-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 8px 12px;
  background: var(--color-bg-hover);
  border-radius: var(--radius-md);
}

.score-info {
  font-size: 13px;
  color: var(--color-text-muted);
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
  align-items: baseline;
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

.question-actions {
  display: flex;
  flex-direction: column;
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
