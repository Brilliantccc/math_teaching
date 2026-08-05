<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { message } from 'ant-design-vue'
import CelebrationOverlay from '@/components/common/CelebrationOverlay.vue'
import LatexText from '@/components/display/LatexText.vue'

const gradeStore = useGradeStore()

const formState = reactive({
  count: 10,
  tag: ''
})
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

const progress = computed(() => {
  if (questionIds.value.length === 0) return 0
  return Math.round(((currentIndex.value + 1) / questionIds.value.length) * 100)
})

async function startPractice() {
  loading.value = true
  try {
    const response = await api.post('/api/practice/session', {
      grade: gradeStore.getGradeParam(),
      count: formState.count,
      tag: formState.tag
    })
    questionIds.value = response.data.question_ids
    if (questionIds.value.length === 0) {
      message.warning('没有找到题目')
      return
    }
    practiceStarted.value = true
    currentIndex.value = 0
    await loadQuestion(questionIds.value[0])
  } catch (error) {
    console.error('Failed to start practice:', error)
  } finally {
    loading.value = false
  }
}

async function loadQuestion(id: number) {
  try {
    const response = await api.get(`/api/questions/${id}`)
    currentQuestion.value = response.data
  } catch (error) {
    console.error('Failed to load question:', error)
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

    if (result.value.is_correct) {
      celebrationType.value = 'success'
      showCelebration.value = true
    }
  } catch (error) {
    console.error('Failed to submit answer:', error)
  }
}

function nextQuestion() {
  showResult.value = false
  userAnswer.value = ''
  currentIndex.value++

  if (currentIndex.value >= questionIds.value.length) {
    celebrationType.value = 'milestone'
    showCelebration.value = true
    setTimeout(() => {
      practiceStarted.value = false
    }, 2000)
    return
  }

  loadQuestion(questionIds.value[currentIndex.value])
}

function endPractice() {
  practiceStarted.value = false
  message.info('已结束练习')
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

function handleCelebrationDone() {
  showCelebration.value = false
}
</script>

<template>
  <div class="practice">
    <h2>在线练习</h2>

    <!-- 维护提示 -->
    <div class="maintenance-notice">
      <a-result
        icon="🔧"
        title="功能维护中"
        sub-title="在线练习功能正在优化答案匹配算法，预计很快恢复。感谢您的耐心等待！"
      >
        <template #extra>
          <a-tag color="processing">优化中</a-tag>
        </template>
      </a-result>
    </div>

    <!-- 配置面板 -->
    <div v-if="!practiceStarted" class="config-panel" style="opacity: 0.5; pointer-events: none;">
      <div class="config-header">
        <span class="config-icon">📝</span>
        <span>选择练习内容</span>
      </div>
      <a-form layout="inline">
        <a-form-item label="题目数量">
          <a-input-number v-model:value="formState.count" :min="1" :max="50" />
        </a-form-item>
        <a-form-item label="知识点">
          <a-input v-model:value="formState.tag" placeholder="可选" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :loading="loading" @click="startPractice" disabled>
            开始练习
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 练习面板 -->
    <div v-else class="practice-panel">
      <div class="progress-bar">
        <div class="progress-text">
          进度：{{ currentIndex + 1 }} / {{ questionIds.length }}
        </div>
        <a-progress :percent="progress" :show-info="false" status="active" />
        <a-button type="link" danger @click="endPractice">结束练习</a-button>
      </div>

      <div v-if="currentQuestion" class="question-area">
        <div class="question-header">
          <span class="question-number">第 {{ currentIndex + 1 }} 题</span>
          <a-tag v-if="currentQuestion.difficulty" :color="currentQuestion.difficulty === 1 ? 'success' : currentQuestion.difficulty === 2 ? 'warning' : 'error'">
            {{ currentQuestion.difficulty === 1 ? '简单' : currentQuestion.difficulty === 2 ? '中等' : '困难' }}
          </a-tag>
        </div>
        <div class="question-title">{{ currentQuestion.title }}</div>
        <div class="question-content"><LatexText :content="currentQuestion.content" :images="parseImages(currentQuestion.images)" /></div>

        <a-divider />

        <div class="answer-area">
          <a-textarea
            v-model:value="userAnswer"
            placeholder="请输入你的答案..."
            :rows="3"
            :disabled="showResult"
          />
          <div class="answer-hint">
            <a-collapse :bordered="false" size="small">
              <a-collapse-panel header="💡 输入提示" key="hint">
                <div class="hint-content">
                  <p><strong>支持的输入格式：</strong></p>
                  <ul>
                    <li>分数：<code>1/2</code>、<code>\frac{1}{2}</code></li>
                    <li>小数：<code>0.5</code>、<code>50%</code></li>
                    <li>乘号：<code>*</code>、<code>×</code>、<code>·</code> 或省略（如 <code>2x</code>）</li>
                    <li>幂运算：<code>x^2</code>、<code>x**2</code>、<code>x^{2}</code></li>
                    <li>根号：<code>sqrt(2)</code>、<code>\sqrt{2}</code></li>
                    <li>带分数：<code>1 1/2</code> 表示 1.5</li>
                  </ul>
                  <p><strong>示例：</strong></p>
                  <p>答案 <code>½</code> 可以输入：<code>1/2</code>、<code>0.5</code>、<code>50%</code>、<code>\frac{1}{2}</code></p>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </div>

        <div class="action-buttons">
          <a-button v-if="!showResult" type="primary" size="large" @click="submitAnswer">
            提交答案
          </a-button>
          <a-button v-else type="primary" size="large" @click="nextQuestion">
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

.maintenance-notice {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius-lg);
  margin-top: 16px;
  color: white;
}

.maintenance-notice :deep(.ant-result-icon) {
  font-size: 48px;
}

.maintenance-notice :deep(.ant-result-title) {
  color: white;
}

.maintenance-notice :deep(.ant-result-subtitle) {
  color: rgba(255, 255, 255, 0.85);
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

.progress-bar {
  margin-bottom: 24px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
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

.question-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text-primary);
}

.question-content {
  color: var(--color-text-body);
  line-height: 1.8;
  font-size: 16px;
}

.answer-area {
  margin-bottom: 24px;
}

.answer-hint {
  margin-top: 8px;
}

.hint-content {
  font-size: 13px;
  line-height: 1.6;
}

.hint-content p {
  margin: 8px 0 4px;
}

.hint-content ul {
  margin: 4px 0;
  padding-left: 20px;
}

.hint-content li {
  margin: 4px 0;
}

.hint-content code {
  background: var(--color-bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
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
</style>
