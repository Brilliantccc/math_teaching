<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { WrongQuestion, WrongQuestionListResponse } from '@/types'
import { message } from 'ant-design-vue'

const wrongQuestions = ref<WrongQuestion[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

async function loadWrongQuestions() {
  loading.value = true
  try {
    const response = await api.get('/api/practice/wrong-questions', {
      params: { page: page.value, per_page: 20 }
    })
    const data: WrongQuestionListResponse = response.data
    wrongQuestions.value = data.wrong_questions
    total.value = data.total
  } catch (error) {
    console.error('Failed to load wrong questions:', error)
  } finally {
    loading.value = false
  }
}

async function toggleMastered(id: number) {
  try {
    await api.post(`/api/practice/wrong-questions/${id}/master`)
    message.success('已更新')
    loadWrongQuestions()
  } catch (error) {
    console.error('Failed to toggle mastered:', error)
  }
}

onMounted(() => {
  loadWrongQuestions()
})
</script>

<template>
  <div class="wrong-questions">
    <h2>错题本</h2>

    <a-spin :spinning="loading">
      <div v-for="item in wrongQuestions" :key="item.id" class="wrong-item">
        <div class="question-header">
          <span class="title">{{ item.question?.title || '（无标题）' }}</span>
          <a-tag :color="item.mastered ? 'success' : 'error'">
            {{ item.mastered ? '已掌握' : '未掌握' }}
          </a-tag>
        </div>
        <div class="question-content">{{ item.question?.content }}</div>
        <div class="question-footer">
          <span class="wrong-count">错误 {{ item.wrong_count }} 次</span>
          <a-button type="link" @click="toggleMastered(item.id)">
            {{ item.mastered ? '标记为未掌握' : '标记为已掌握' }}
          </a-button>
        </div>
      </div>

      <a-empty v-if="!loading && wrongQuestions.length === 0" description="暂无错题" />
    </a-spin>

    <div class="pagination">
      <a-pagination
        v-model:current="page"
        :total="total"
        :page-size="20"
        @change="loadWrongQuestions"
      />
    </div>
  </div>
</template>

<style scoped>
.wrong-questions {
  max-width: 900px;
  margin: 0 auto;
}

.wrong-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 12px;
  background: var(--color-bg-card);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.title {
  font-weight: 500;
  font-size: 16px;
}

.question-content {
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.question-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wrong-count {
  color: var(--color-error);
  font-size: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
