<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { GRADES } from '@/stores/grade'
import type { Question, QuestionListResponse } from '@/types'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, EditOutlined, ClearOutlined } from '@ant-design/icons-vue'
import LatexText from '@/components/display/LatexText.vue'
import QuestionPreview from '@/components/display/QuestionPreview.vue'

const gradeStore = useGradeStore()

const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const deduplicating = ref(false)
const selectedRowKeys = ref<number[]>([])
const duplicateInfo = ref<{ groups: number; count: number } | null>(null)

async function loadQuestions() {
  loading.value = true
  try {
    const response = await api.get('/api/questions', {
      params: { page: page.value, per_page: 20, grade: gradeStore.getGradeParam() }
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

async function checkDuplicates() {
  try {
    const token = localStorage.getItem('token')
    console.log('[Manage] Token exists:', !!token)
    const response = await api.get('/api/questions/check-duplicates')
    duplicateInfo.value = {
      groups: response.data.duplicate_groups,
      count: response.data.total_duplicates
    }
  } catch (error: any) {
    console.error('Failed to check duplicates:', error.response?.status, error.response?.data)
    // 不显示错误，静默处理
  }
}

async function deduplicate() {
  Modal.confirm({
    title: '清理重复题目',
    content: `确定要清理重复题目吗？将保留每组中最早创建的题目，删除其余重复项。`,
    okText: '确定清理',
    cancelText: '取消',
    onOk: async () => {
      deduplicating.value = true
      try {
        const response = await api.post('/api/questions/deduplicate')
        message.success(response.data.message)
        duplicateInfo.value = null
        loadQuestions()
        checkDuplicates()
      } catch (error) {
        message.error('清理失败')
        console.error('Failed to deduplicate:', error)
      } finally {
        deduplicating.value = false
      }
    }
  })
}

async function deleteQuestion(id: number) {
  try {
    await api.delete(`/api/questions/${id}`)
    message.success('已删除')
    loadQuestions()
    checkDuplicates()
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
    checkDuplicates()
  } catch (error) {
    console.error('Failed to batch delete:', error)
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

function handleGradeChange(grade: string) {
  gradeStore.setGrade(grade)
  page.value = 1
  loadQuestions()
}

onMounted(() => {
  loadQuestions()
  checkDuplicates()
})
</script>

<template>
  <div class="manage">
    <div class="header">
      <div class="header-left">
        <h2>题目管理</h2>
        <a-select
          :value="gradeStore.currentGrade"
          style="width: 120px"
          @change="handleGradeChange"
        >
          <a-select-option v-for="g in gradeStore.grades" :key="g" :value="g">{{ g }}</a-select-option>
          <a-select-option v-for="g in GRADES" :key="g" :value="g">{{ g }}</a-select-option>
        </a-select>
      </div>
      <a-space>
        <a-button @click="$router.push('/upload')">
          <PlusOutlined /> 上传题目
        </a-button>
        <a-button
          v-if="duplicateInfo && duplicateInfo.count > 0"
          type="primary"
          danger
          :loading="deduplicating"
          @click="deduplicate"
        >
          <ClearOutlined /> 清理重复（{{ duplicateInfo.count }}道）
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
          { title: '题干', dataIndex: 'content', key: 'content' },
          { title: '年级', dataIndex: 'grade', key: 'grade', width: 70 },
          { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 70 },
          { title: '操作', key: 'action', width: 100 }
        ]"
        :row-selection="{ selectedRowKeys, onChange: (keys: number[]) => selectedRowKeys = keys }"
        :pagination="{ total, current: page, pageSize: 20, onChange: (p: number) => { page = p; loadQuestions() } }"
        row-key="id"
        :scroll="{ x: 800 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'content'">
            <div class="content-cell">
              <QuestionPreview :content="record.content" :images="parseImages(record.images)" :show-images="true" :compact="true" />
            </div>
          </template>
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

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
}

:deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
}

.content-cell {
  max-width: 400px;
  overflow: hidden;
}

:deep(.ant-table-cell) {
  vertical-align: top;
}
</style>
