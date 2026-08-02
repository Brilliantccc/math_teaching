<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Test } from '@/types'
import { message } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const tests = ref<Test[]>([])
const loading = ref(false)

async function loadTests() {
  loading.value = true
  try {
    const response = await api.get('/api/tests')
    tests.value = response.data.tests
  } catch (error) {
    console.error('Failed to load tests:', error)
  } finally {
    loading.value = false
  }
}

function getQuestionCount(test: Test): number {
  try {
    return JSON.parse(test.question_ids).length
  } catch {
    return 0
  }
}

async function deleteTest(id: number) {
  try {
    await api.delete(`/api/tests/${id}`)
    message.success('已删除')
    loadTests()
  } catch (error) {
    console.error('Failed to delete test:', error)
  }
}

async function exportPdf(id: number, name: string) {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:8000/api/tests/${id}/pdf`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('导出失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${name || '试卷'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
    message.success('PDF 已导出')
  } catch (error) {
    message.error('导出PDF失败')
  }
}

onMounted(() => {
  loadTests()
})
</script>

<template>
  <div class="test-manage">
    <div class="header">
      <h2>组卷管理</h2>
      <a-button type="primary" @click="$router.push('/test')">
        <PlusOutlined /> 智能组卷
      </a-button>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :data-source="tests"
        :columns="[
          { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
          { title: '名称', dataIndex: 'name', key: 'name' },
          { title: '题目数', key: 'count', width: 80 },
          { title: '总分', key: 'totalScore', width: 80 },
          { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
          { title: '操作', key: 'action', width: 160 }
        ]"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'count'">
            {{ getQuestionCount(record) }} 题
          </template>
          <template v-if="column.key === 'totalScore'">
            {{ getQuestionCount(record) * (record.score_per_question || 10) }} 分
          </template>
          <template v-if="column.key === 'created_at'">
            {{ record.created_at ? new Date(record.created_at).toLocaleString('zh-CN') : '-' }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="exportPdf(record.id, record.name)">
                <DownloadOutlined /> 导出PDF
              </a-button>
              <a-popconfirm title="确定删除？" @confirm="deleteTest(record.id)">
                <a-button type="link" danger>
                  <DeleteOutlined /> 删除
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
.test-manage {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

:deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
}
</style>
