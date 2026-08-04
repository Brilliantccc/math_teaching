<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Test } from '@/types'
import { message, notification } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, EyeOutlined, DownloadOutlined, LoadingOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const tests = ref<Test[]>([])
const loading = ref(false)

// PDF导出状态
const exportState = reactive<Record<number, { exporting: boolean; progress: number }>>({})

// PDF预览状态
const previewVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const previewTestId = ref<number | null>(null)

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
  // 初始化导出状态
  exportState[id] = { exporting: true, progress: 0 }

  try {
    const token = localStorage.getItem('token') || ''

    // 先尝试同步导出（简单快速）
    const response = await fetch(`http://localhost:8000/api/tests/${id}/pdf`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.ok) {
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${name || '试卷'}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      message.success('PDF 已导出')
      return
    }

    // 同步导出失败，尝试异步导出
    const test = tests.value.find(t => t.id === id)
    if (!test) throw new Error('试卷不存在')

    const taskResponse = await fetch(`http://localhost:8000/api/tests/async`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question_ids: JSON.parse(test.question_ids || '[]'),
        title: name || '试卷'
      })
    })

    if (taskResponse.ok) {
      const { task_id } = await taskResponse.json()
      await pollTaskStatus(id, task_id, token)
    } else {
      throw new Error('创建异步任务失败')
    }
  } catch (error) {
    message.error('导出PDF失败')
    exportState[id] = { exporting: false, progress: 0 }
  }
}

async function pollTaskStatus(testId: number, taskId: string, token: string) {
  const maxAttempts = 60
  let attempts = 0

  const poll = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/tests/task/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) throw new Error('查询失败')

      const data = await response.json()
      exportState[testId].progress = data.progress || 0

      if (data.status === 'completed') {
        const downloadResponse = await fetch(`http://localhost:8000/api/tests/download/${taskId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (downloadResponse.ok) {
          const blob = await downloadResponse.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `试卷.pdf`
          a.click()
          URL.revokeObjectURL(url)
          message.success('PDF 已导出')
        }
        exportState[testId] = { exporting: false, progress: 0 }
        return
      }

      if (data.status === 'failed') {
        throw new Error(data.error || '生成失败')
      }

      attempts++
      if (attempts < maxAttempts) {
        setTimeout(poll, 1000)
      } else {
        throw new Error('超时')
      }
    } catch (error) {
      message.error('导出PDF失败')
      exportState[testId] = { exporting: false, progress: 0 }
    }
  }

  await poll()
}

// 预览PDF
async function previewPdf(test: Test) {
  previewTestId.value = test.id
  previewLoading.value = true
  previewVisible.value = true

  try {
    const token = localStorage.getItem('token') || ''
    const questionIds = JSON.parse(test.question_ids || '[]')

    const response = await fetch('http://localhost:8000/api/tests/preview', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question_ids: questionIds,
        title: test.name || '数学试卷',
        template: 'standard'
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
  previewTestId.value = null
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
              <a-button
                type="link"
                @click="previewPdf(record)"
              >
                <EyeOutlined /> 预览
              </a-button>
              <a-button
                type="link"
                :disabled="exportState[record.id]?.exporting"
                @click="exportPdf(record.id, record.name)"
              >
                <LoadingOutlined v-if="exportState[record.id]?.exporting" />
                <DownloadOutlined v-else />
                {{ exportState[record.id]?.exporting ? `${exportState[record.id].progress}%` : '导出PDF' }}
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
</style>
