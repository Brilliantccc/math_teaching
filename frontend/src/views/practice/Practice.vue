<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { GRADES, DIFFICULTIES, MIDDLE_SCHOOL_GRADES, HIGH_SCHOOL_GRADES } from '@/constants'
import { message } from 'ant-design-vue'
import CelebrationOverlay from '@/components/common/CelebrationOverlay.vue'
import LatexText from '@/components/display/LatexText.vue'
import ChoiceQuestion from './components/ChoiceQuestion.vue'
import FillBlankQuestion from './components/FillBlankQuestion.vue'
import JudgeQuestion from './components/JudgeQuestion.vue'

const gradeStore = useGradeStore()

// 可选题型（支持在线练习的）
const QUESTION_TYPES = ['单项选择', '多项选择', '填空题', '判断题']

// 难度选项
const DIFFICULTY_OPTIONS = [
  { value: 1, label: '简单', color: 'green' },
  { value: 2, label: '中等', color: 'orange' },
  { value: 3, label: '困难', color: 'red' }
]

// 题型列表（从数据库动态加载）
const questionTypes = ref<{type: string, count: number, difficulty_counts?: Record<number, number>}[]>([])
const questionTypeLoading = ref(false)

// 配置表单 - 按题型+难度配置数量
const formState = reactive({
  grade: '',
  // 按题型+难度配置数量：{ '单项选择': { 1: 3, 2: 2, 3: 0 }, ... }
  questionTypeCounts: {} as Record<string, Record<number, number>>
})

// 练习状态
const loading = ref(false)
const practiceStarted = ref(false)
const questionIds = ref<number[]>([])
const currentIndex = ref(0)
const currentQuestion = ref<any>(null)
const userAnswer = ref('')
const showResult = ref(false)
const result = ref({ is_correct: false, answer_analysis: '' })
const showCelebration = ref(false)
const celebrationType = ref<'success' | 'encouragement' | 'milestone'>('success')

// 练习结果统计
const practiceResults = ref<Array<{
  question_id: number
  is_correct: boolean
  question_type: string
}>>([])

const progress = computed(() => {
  if (questionIds.value.length === 0) return 0
  return Math.round(((currentIndex.value + 1) / questionIds.value.length) * 100)
})

// 计算总题目数
const totalCount = computed(() => {
  let total = 0
  for (const typeCounts of Object.values(formState.questionTypeCounts)) {
    for (const count of Object.values(typeCounts)) {
      total += count
    }
  }
  return total
})

// 获取年级参数
function getGradeParam(grade: string): string {
  if (!grade || grade === '全部') return ''
  if (grade === '初中全部') return MIDDLE_SCHOOL_GRADES.join(',')
  if (grade === '高中全部') return HIGH_SCHOOL_GRADES.join(',')
  return grade
}

// 加载题型列表
async function loadQuestionTypes() {
  questionTypeLoading.value = true
  try {
    const gradeParam = getGradeParam(formState.grade)
    const response = await api.get('/api/questions/question-types', {
      params: { grade: gradeParam }
    })
    questionTypes.value = response.data.question_types || []

    // 清空并重新初始化用户配置（从0开始）
    const newTypeCounts: Record<string, Record<number, number>> = {}
    for (const qt of questionTypes.value) {
      // 用户配置的生成数量从0开始
      newTypeCounts[qt.type] = { 1: 0, 2: 0, 3: 0 }
    }
    formState.questionTypeCounts = newTypeCounts

    // 注意：可用数量通过 questionTypes 数组中的 difficulty_counts 字段传递
  } catch (error) {
    console.error('Failed to load question types:', error)
  } finally {
    questionTypeLoading.value = false
  }
}

// 获取某题型某难度的可用数量
function getAvailableCount(type: string, difficulty: number): number {
  const qt = questionTypes.value.find(q => q.type === type)
  if (qt && qt.difficulty_counts) {
    return qt.difficulty_counts[difficulty] || 0
  }
  return 0
}

// 页面加载时获取题型
onMounted(() => {
  loadQuestionTypes()
})

// 根据题型获取组件
const questionComponent = computed(() => {
  const type = currentQuestion.value?.question_type
  if (type === '单项选择' || type === '多项选择') {
    return ChoiceQuestion
  } else if (type === '填空题') {
    return FillBlankQuestion
  } else if (type === '判断题') {
    return JudgeQuestion
  }
  return ChoiceQuestion // 默认
})

// 是否可以提交
const canSubmit = computed(() => {
  if (showResult.value) return false
  return userAnswer.value.trim() !== ''
})

// 获取当前题目对应的 props
const questionProps = computed(() => ({
  content: currentQuestion.value?.content || '',
  disabled: showResult.value
}))

// 统计结果
const statsSummary = computed(() => {
  const total = practiceResults.value.length
  const correct = practiceResults.value.filter(r => r.is_correct).length
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0

  // 按题型统计
  const typeStats: Record<string, { total: number; correct: number }> = {}
  for (const result of practiceResults.value) {
    const type = result.question_type || '未知'
    if (!typeStats[type]) {
      typeStats[type] = { total: 0, correct: 0 }
    }
    typeStats[type].total++
    if (result.is_correct) {
      typeStats[type].correct++
    }
  }

  return { total, correct, accuracy, typeStats }
})

async function startPractice() {
  const totalQuestions = totalCount.value
  if (totalQuestions === 0) {
    message.warning('请至少配置一道题目')
    return
  }

  loading.value = true
  try {
    const gradeParam = getGradeParam(formState.grade)

    const response = await api.post('/api/practice/session', {
      grade: gradeParam,
      question_type_difficulty_counts: formState.questionTypeCounts
    })

    questionIds.value = response.data.question_ids
    if (questionIds.value.length === 0) {
      message.warning('没有找到符合条件的题目')
      return
    }

    practiceStarted.value = true
    currentIndex.value = 0
    practiceResults.value = []
    await loadQuestion(questionIds.value[0])
  } catch (error) {
    console.error('Failed to start practice:', error)
    message.error('开始练习失败，请重试')
  } finally {
    loading.value = false
  }
}

async function loadQuestion(id: number) {
  try {
    const response = await api.get(`/api/questions/${id}`)
    currentQuestion.value = response.data
    userAnswer.value = ''
    showResult.value = false
  } catch (error) {
    console.error('Failed to load question:', error)
    message.error('加载题目失败')
  }
}

async function submitAnswer() {
  if (!userAnswer.value.trim()) {
    message.warning('请输入答案')
    return
  }

  try {
    const response = await api.post('/api/practice/submit', {
      question_id: currentQuestion.value.id,
      answer: userAnswer.value
    })

    result.value = response.data
    showResult.value = true

    // 记录结果
    practiceResults.value.push({
      question_id: currentQuestion.value.id,
      is_correct: response.data.is_correct,
      question_type: currentQuestion.value.question_type || '未知'
    })

    if (response.data.is_correct) {
      celebrationType.value = 'success'
      showCelebration.value = true
    }
  } catch (error) {
    console.error('Failed to submit answer:', error)
    message.error('提交答案失败，请重试')
  }
}

function nextQuestion() {
  showResult.value = false
  userAnswer.value = ''
  currentIndex.value++

  if (currentIndex.value >= questionIds.value.length) {
    // 练习完成
    celebrationType.value = 'milestone'
    showCelebration.value = true
    return
  }

  loadQuestion(questionIds.value[currentIndex.value])
}

function endPractice() {
  practiceStarted.value = false
  practiceResults.value = []
  message.info('已结束练习')
}

function restartPractice() {
  practiceStarted.value = false
  startPractice()
}

function handleCelebrationDone() {
  showCelebration.value = false
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

// 获取题型对应的颜色
function getTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    '单项选择': 'blue',
    '多项选择': 'purple',
    '填空题': 'green',
    '解答题': 'orange',
    '判断题': 'magenta',
    '计算题': 'cyan'
  }
  return colorMap[type] || 'default'
}
</script>

<template>
  <div class="practice">
    <h2>在线练习</h2>

    <!-- 配置面板 -->
    <div v-if="!practiceStarted" class="config-panel">
      <div class="config-header">
        <span class="config-icon">📝</span>
        <span>选择练习内容</span>
      </div>

      <a-form layout="vertical" :model="formState">
        <!-- 年级选择 -->
        <a-form-item label="选择年级（可选）">
          <a-select
            v-model:value="formState.grade"
            placeholder="全部年级"
            allow-clear
            style="width: 100%"
            @change="loadQuestionTypes"
          >
            <a-select-option value="">全部年级</a-select-option>
            <a-select-option v-for="grade in GRADES.filter(g => g !== '全部')" :key="grade" :value="grade">
              {{ grade }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 按题型+难度配置数量 -->
        <a-form-item label="按题型和难度配置数量">
          <template #label>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>按题型和难度配置数量</span>
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
                  <a-tag :color="diff.color" size="small">{{ diff.label }}：{{ formState.questionTypeCounts[qt.type]?.[diff.value] || 0 }} / {{ getAvailableCount(qt.type, diff.value) }}</a-tag>
                  <a-input-number
                    v-model:value="formState.questionTypeCounts[qt.type][diff.value]"
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

        <!-- 总数统计 -->
        <a-form-item>
          <a-alert
            :message="`共配置 ${totalCount} 道题目`"
            type="info"
            show-icon
          />
        </a-form-item>

        <!-- 开始按钮 -->
        <a-form-item>
          <a-button
            type="primary"
            size="large"
            block
            :loading="loading"
            @click="startPractice"
          >
            开始练习
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 练习完成面板 -->
    <div v-else-if="currentIndex >= questionIds.length" class="result-panel">
      <a-result
        icon="🎉"
        title="练习完成！"
        :sub-title="`你完成了 ${statsSummary.total} 道题，正确率 ${statsSummary.accuracy}%`"
      >
        <template #extra>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ statsSummary.total }}</div>
              <div class="stat-label">总题数</div>
            </div>
            <div class="stat-card success">
              <div class="stat-value">{{ statsSummary.correct }}</div>
              <div class="stat-label">正确</div>
            </div>
            <div class="stat-card danger">
              <div class="stat-value">{{ statsSummary.total - statsSummary.correct }}</div>
              <div class="stat-label">错误</div>
            </div>
            <div class="stat-card primary">
              <div class="stat-value">{{ statsSummary.accuracy }}%</div>
              <div class="stat-label">正确率</div>
            </div>
          </div>

          <a-divider />

          <!-- 按题型统计 -->
          <div class="type-stats">
            <h4>各题型统计</h4>
            <div v-for="(stats, type) in statsSummary.typeStats" :key="type" class="type-stat-item">
              <span class="type-name">{{ type }}</span>
              <span class="type-detail">
                {{ stats.correct }}/{{ stats.total }} 正确
                ({{ stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0 }}%)
              </span>
            </div>
          </div>

          <div class="action-buttons">
            <a-button type="primary" size="large" @click="restartPractice">
              再练一次
            </a-button>
            <a-button size="large" @click="practiceStarted = false">
              返回配置
            </a-button>
          </div>
        </template>
      </a-result>
    </div>

    <!-- 练习进行中面板 -->
    <div v-else class="practice-panel">
      <div class="progress-bar">
        <div class="progress-text">
          <span>第 {{ currentIndex + 1 }} / {{ questionIds.length }} 题</span>
          <a-tag v-if="currentQuestion?.question_type" color="blue">
            {{ currentQuestion.question_type }}
          </a-tag>
        </div>
        <a-progress :percent="progress" :show-info="false" status="active" />
        <a-button type="link" danger @click="endPractice">结束练习</a-button>
      </div>

      <div v-if="currentQuestion" class="question-area">
        <div class="question-header">
          <span class="question-number">第 {{ currentIndex + 1 }} 题</span>
          <div class="question-tags">
            <a-tag v-if="currentQuestion.difficulty" :color="currentQuestion.difficulty === 1 ? 'success' : currentQuestion.difficulty === 2 ? 'warning' : 'error'">
              {{ currentQuestion.difficulty === 1 ? '简单' : currentQuestion.difficulty === 2 ? '中等' : '困难' }}
            </a-tag>
          </div>
        </div>

        <!-- 题目图片（优先显示 images 数组，避免重复） -->
        <div v-if="parseImages(currentQuestion.images).length > 0" class="question-images">
          <img v-for="(img, idx) in parseImages(currentQuestion.images)" :key="idx" :src="img" alt="题目图片" />
        </div>
        <div v-else-if="currentQuestion.image_path" class="question-image">
          <img :src="currentQuestion.image_path" alt="题目图片" />
        </div>

        <!-- 根据题型渲染答题组件 -->
        <component
          :is="questionComponent"
          v-model="userAnswer"
          v-bind="questionProps"
        />

        <a-divider />

        <div class="action-buttons">
          <a-button
            v-if="!showResult"
            type="primary"
            size="large"
            :disabled="!canSubmit"
            @click="submitAnswer"
          >
            提交答案
          </a-button>
          <a-button
            v-else
            type="primary"
            size="large"
            @click="nextQuestion"
          >
            {{ currentIndex >= questionIds.length - 1 ? '🎉 完成' : '下一题 →' }}
          </a-button>
        </div>

        <!-- 结果显示 -->
        <Transition name="result">
          <div v-if="showResult" class="result-area">
            <a-alert
              :type="result.is_correct ? 'success' : 'warning'"
              :message="result.is_correct ? '🎉 回答正确！' : '😊 回答错误，继续加油！'"
              show-icon
              style="margin-bottom: 16px"
            />
            <div class="answer-analysis-display">
              <h4>答案解析：</h4>
              <LatexText :content="result.answer_analysis" />
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 庆祝动画 -->
    <CelebrationOverlay
      :show="showCelebration"
      :type="celebrationType"
      @done="handleCelebrationDone"
    />
  </div>
</template>

<style scoped>
.practice {
  max-width: 800px;
  margin: 0 auto;
}

.config-panel {
  background: var(--color-bg-card);
  padding: 32px;
  border-radius: var(--radius-lg);
  margin-top: 16px;
  border: 1px solid var(--color-border);
}

.config-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 500;
}

.config-icon {
  font-size: 24px;
}

/* 题型+难度配置 */
.type-difficulty-config {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.difficulty-config {
  display: flex;
  gap: 12px;
  align-items: center;
}

.result-panel {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  margin-top: 16px;
  border: 1px solid var(--color-border);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 20px 0;
}

.stat-card {
  background: var(--color-bg-hover);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
}

.stat-card.success {
  background: rgba(82, 196, 26, 0.1);
}

.stat-card.danger {
  background: rgba(255, 77, 79, 0.1);
}

.stat-card.primary {
  background: rgba(102, 126, 234, 0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.type-stats {
  margin: 20px 0;
  text-align: left;
}

.type-stats h4 {
  margin-bottom: 12px;
  color: var(--color-text-primary);
}

.type-stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}

.type-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.type-detail {
  color: var(--color-text-muted);
}

.progress-bar {
  margin-bottom: 24px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--color-text-muted);
}

.question-area {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 32px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-number {
  font-size: 14px;
  color: var(--color-text-muted);
}

.question-tags {
  display: flex;
  gap: 8px;
}

.question-image {
  margin-bottom: 16px;
  text-align: center;
}

.question-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: var(--radius-md);
}

.question-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.question-images img {
  max-width: 200px;
  max-height: 200px;
  border-radius: var(--radius-md);
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.result-area {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
}

.answer-analysis-display {
  line-height: 1.8;
  font-size: 15px;
  color: var(--color-text-body);
}

.answer-analysis-display h4 {
  margin-bottom: 8px;
  color: var(--color-text-primary);
}

.result-enter-active,
.result-leave-active {
  transition: all 0.3s ease;
}

.result-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.result-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .question-area {
    padding: 20px;
  }
}
</style>
