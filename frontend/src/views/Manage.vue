<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import type { Question, QuestionListResponse } from '@/types'
import { message } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons-vue'

const gradeStore = useGradeStore()

const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const selectedRowKeys = ref<number[]>([])

async function loadQuestions() {
  loading.value = true
  try {
    const response = await api.get('/api/questions', {
      params: { page: page.value, per_page: 20, grade: gradeStore.currentGrade }
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

async function deleteQuestion(id: number) {
  try {
    await api.delete(`/api/questions/${id}`)
    message.success('已删除')
    loadQuestions()
  } catch (error) {
    console.error('Failed to delete question:', error)
  }
}

async function batchDelete() {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请选择题目')
    return
  }
  try {
    await api.post('/api/questions/batch-delete', { ids: selectedRowKeys.value })
    message.success('已批量删除')
    selectedRowKeys.value = []
    loadQuestions()
  } catch (error) {
    console.error('Failed to batch delete:', error)
  }
}

onMounted(() => {
  loadQuestions()
})
</script>

<template>
  <div class="manage">
    <div class="header">
      <h2>题目管理</h2>
      <a-space>
        <a-button type="primary" @click="$router.push('/upload')">
          <PlusOutlined /> 上传题目
        </a-button>
        <a-button danger @click="batchDelete" :disabled="selectedRowKeys.length === 0">
          <DeleteOutlined /> 批量删除
        </a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :data-source="questions"
        :columns="[
          { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
          { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
          { title: '年级', dataIndex: 'grade', key: 'grade', width: 80 },
          { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 80 },
          { title: '操作', key: 'action', width: 120 }
        ]"
        :row-selection="{ selectedRowKeys, onChange: (keys: number[]) => selectedRowKeys = keys }"
        :pagination="{ total, current: page, pageSize: 20, onChange: (p: number) => { page = p; loadQuestions() } }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'difficulty'">
            <a-tag :color="record.difficulty === 1 ? 'success' : record.difficulty === 2 ? 'warning' : 'error'">
              {{ record.difficulty === 1 ? '简单' : record.difficulty === 2 ? '中等' : '困难' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="$router.push(`/question/edit/${record.id}`)">
                <EditOutlined />
              </a-button>
              <a-popconfirm title="确定删除？" @confirm="deleteQuestion(record.id)">
                <a-button type="link" danger>
                  <DeleteOutlined />
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-spin>
  </div>
</template>

<style scoped>
.manage {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
