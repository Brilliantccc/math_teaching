<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import type { Question, QuestionListResponse } from '@/types'
import { SearchOutlined } from '@ant-design/icons-vue'

const gradeStore = useGradeStore()

const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const perPage = ref(20)
const loading = ref(false)

const filters = ref({
  keyword: '',
  category: '',
  difficulty: undefined as number | undefined
})

const categories = ref<string[]>([])

async function loadQuestions() {
  loading.value = true
  try {
    const response = await api.get('/api/questions', {
      params: {
        page: page.value,
        per_page: perPage.value,
        grade: gradeStore.currentGrade,
        keyword: filters.value.keyword,
        category: filters.value.category,
        difficulty: filters.value.difficulty
      }
    })
    const data: QuestionListResponse = response.data
    questions.value = data.questions
    total.value = data.total
  } catch (error) {
    console.error('Failed to load questions:', error)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const response = await api.get('/api/categories')
    categories.value = Object.keys(response.data.categories)
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

function handleSearch() {
  page.value = 1
  loadQuestions()
}

function handlePageChange(newPage: number) {
  page.value = newPage
  loadQuestions()
}

function getDifficultyText(level: number) {
  switch (level) {
    case 1: return '简单'
    case 2: return '中等'
    case 3: return '困难'
    default: return '未知'
  }
}

function getDifficultyColor(level: number) {
  switch (level) {
    case 1: return 'success'
    case 2: return 'warning'
    case 3: return 'error'
    default: return 'default'
  }
}

onMounted(() => {
  loadCategories()
  loadQuestions()
})

watch(() => gradeStore.currentGrade, () => {
  loadQuestions()
})
</script>

<template>
  <div class="browse">
    <div class="header">
      <h2>浏览题库</h2>
      <span class="total">共 {{ total }} 道题目</span>
    </div>

    <!-- 筛选栏 -->
    <div class="filters">
      <a-input-search
        v-model:value="filters.keyword"
        placeholder="搜索题目"
        style="width: 300px"
        @search="handleSearch"
      />
      <a-select
        v-model:value="filters.category"
        placeholder="选择分类"
        allow-clear
        style="width: 150px"
        @change="handleSearch"
      >
        <a-select-option v-for="cat in categories" :key="cat" :value="cat">
          {{ cat }}
        </a-select-option>
      </a-select>
      <a-select
        v-model:value="filters.difficulty"
        placeholder="选择难度"
        allow-clear
        style="width: 120px"
        @change="handleSearch"
      >
        <a-select-option :value="1">简单</a-select-option>
        <a-select-option :value="2">中等</a-select-option>
        <a-select-option :value="3">困难</a-select-option>
      </a-select>
    </div>

    <!-- 题目列表 -->
    <a-spin :spinning="loading">
      <div class="question-list">
        <div v-for="q in questions" :key="q.id" class="question-card">
          <div class="question-header">
            <span class="question-title">{{ q.title || '（无标题）' }}</span>
            <a-tag :color="getDifficultyColor(q.difficulty)">
              {{ getDifficultyText(q.difficulty) }}
            </a-tag>
          </div>
          <div class="question-content">{{ q.content }}</div>
          <div class="question-footer">
            <span class="grade">{{ q.grade }}</span>
            <span v-if="q.category" class="category">{{ q.category }}</span>
          </div>
        </div>

        <a-empty v-if="!loading && questions.length === 0" description="暂无题目" />
      </div>
    </a-spin>

    <!-- 分页 -->
    <div class="pagination">
      <a-pagination
        v-model:current="page"
        :total="total"
        :page-size="perPage"
        show-size-changer
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.browse {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
}

.total {
  color: #666;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.question-list {
  min-height: 400px;
}

.question-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  transition: box-shadow 0.3s;
}

.question-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.question-title {
  font-weight: 500;
  font-size: 16px;
}

.question-content {
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}

.question-footer {
  display: flex;
  gap: 8px;
}

.grade, .category {
  font-size: 12px;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
