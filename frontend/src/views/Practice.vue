<script setup lang="ts">
import { ref, reactive } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { message } from 'ant-design-vue'

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
const result = ref({ is_correct: false, correct_answer: '', analysis: '' })

async function startPractice() {
  loading.value = true
  try {
    const response = await api.post('/api/practice/session', {
      grade: gradeStore.currentGrade,
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
  } catch (error) {
    console.error('Failed to submit answer:', error)
  }
}

function nextQuestion() {
  showResult.value = false
  userAnswer.value = ''
  currentIndex.value++

  if (currentIndex.value >= questionIds.value.length) {
    message.success('练习完成！')
    practiceStarted.value = false
    return
  }

  loadQuestion(questionIds.value[currentIndex.value])
}

function endPractice() {
  practiceStarted.value = false
  message.info('已结束练习')
}
</script>

<template>
  <div class="practice">
    <h2>在线练习</h2>

    <!-- 配置面板 -->
    <div v-if="!practiceStarted" class="config-panel">
      <a-form layout="inline">
        <a-form-item label="题目数量">
          <a-input-number v-model:value="formState.count" :min="1" :max="50" />
        </a-form-item>
        <a-form-item label="知识点">
          <a-input v-model:value="formState.tag" placeholder="可选" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :loading="loading" @click="startPractice">
            开始练习
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 练习面板 -->
    <div v-else class="practice-panel">
      <div class="progress">
        进度：{{ currentIndex + 1 }} / {{ questionIds.length }}
        <a-button type="link" danger @click="endPractice">结束练习</a-button>
      </div>

      <div v-if="currentQuestion" class="question-area">
        <div class="question-title">{{ currentQuestion.title }}</div>
        <div class="question-content">{{ currentQuestion.content }}</div>

        <a-divider />

        <div class="answer-area">
          <a-textarea
            v-model:value="userAnswer"
            placeholder="请输入答案"
            :rows="3"
            :disabled="showResult"
          />
        </div>

        <div class="action-buttons">
          <a-button v-if="!showResult" type="primary" @click="submitAnswer">
            提交答案
          </a-button>
          <a-button v-else type="primary" @click="nextQuestion">
            {{ currentIndex >= questionIds.length - 1 ? '完成' : '下一题' }}
          </a-button>
        </div>

        <!-- 结果显示 -->
        <div v-if="showResult" class="result-area">
          <a-alert
            :type="result.is_correct ? 'success' : 'error'"
            :message="result.is_correct ? '回答正确！' : '回答错误'"
            show-icon
            style="margin-bottom: 16px"
          />
          <div class="correct-answer">
            <strong>正确答案：</strong>{{ result.correct_answer }}
          </div>
          <div v-if="result.analysis" class="analysis">
            <strong>解析：</strong>{{ result.analysis }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.practice {
  max-width: 800px;
  margin: 0 auto;
}

.config-panel {
  background: #f5f5f5;
  padding: 24px;
  border-radius: 8px;
  margin-top: 16px;
}

.progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px;
}

.question-area {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 24px;
}

.question-title {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 12px;
}

.question-content {
  color: #666;
  line-height: 1.6;
}

.answer-area {
  margin-bottom: 16px;
}

.action-buttons {
  margin-bottom: 16px;
}

.result-area {
  margin-top: 16px;
}

.correct-answer {
  margin-bottom: 8px;
  color: #52c41a;
}

.analysis {
  color: #666;
  line-height: 1.6;
}
</style>
