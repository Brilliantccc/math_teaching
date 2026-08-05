<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api'
import type { WrongQuestion, WrongQuestionListResponse } from '@/types'
import { message, Modal } from 'ant-design-vue'
import LatexText from '@/components/display/LatexText.vue'

const wrongQuestions = ref<WrongQuestion[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const selectedIds = ref<number[]>([])

const hasSelected = computed(() => selectedIds.value.length > 0)

async function loadWrongQuestions() {
  loading.value = true
  try {
    const response = await api.get('/api/practice/wrong-questions', {
      params: { page: page.value, per_page: 20 }
    })
    const data: WrongQuestionListResponse = response.data
    wrongQuestions.value = data.wrong_questions
    total.value = data.total
    selectedIds.value = []
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

async function deleteWrongQuestion(id: number) {
  try {
    await api.delete(`/api/practice/wrong-questions/${id}`)
    message.success('已删除')
    loadWrongQuestions()
  } catch (error) {
    console.error('Failed to delete wrong question:', error)
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) {
    message.warning('请选择要删除的错题')
    return
  }
  Modal.confirm({
    title: '批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 条错题记录吗？`,
    okText: '确定删除',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await api.post('/api/practice/wrong-questions/batch-delete', {
          ids: selectedIds.value
        })
        message.success(`已删除 ${selectedIds.value.length} 条错题记录`)
        loadWrongQuestions()
      } catch (error) {
        message.error('删除失败')
        console.error('Failed to batch delete:', error)
      }
    }
  })
}

function toggleSelect(id: number) {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.length === wrongQuestions.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = wrongQuestions.value.map(item => item.id)
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

onMounted(() => {
  loadWrongQuestions()
})
</script>

<template>
  <div class="wrong-questions">
    <div class="header">
      <h2>错题本</h2>
      <a-space v-if="wrongQuestions.length > 0">
        <a-checkbox
          :checked="selectedIds.length === wrongQuestions.length && wrongQuestions.length > 0"
          :indeterminate="selectedIds.length > 0 && selectedIds.length < wrongQuestions.length"
          @change="toggleSelectAll"
        >
          全选
        </a-checkbox>
        <a-button
          danger
          :disabled="!hasSelected"
          @click="batchDelete"
        >
          批量删除 {{ hasSelected ? `(${selectedIds.length})` : '' }}
        </a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <div v-for="item in wrongQuestions" :key="item.id" class="wrong-item" :class="{ selected: selectedIds.includes(item.id) }">
        <div class="question-header">
          <div class="header-left">
            <a-checkbox
              :checked="selectedIds.includes(item.id)"
              @change="toggleSelect(item.id)"
            />
            <span class="title">{{ item.question?.grade || '未知年级' }}</span>
          </div>
          <a-tag :color="item.mastered ? 'success' : 'error'">
            {{ item.mastered ? '已掌握' : '未掌握' }}
          </a-tag>
        </div>
        <div class="question-content"><LatexText :content="item.question?.content || ''" :images="parseImages(item.question?.images)" /></div>
        <div class="question-footer">
          <span class="wrong-count">错误 {{ item.wrong_count }} 次</span>
          <div class="footer-actions">
            <a-button type="link" @click="toggleMastered(item.id)">
              {{ item.mastered ? '标记为未掌握' : '标记为已掌握' }}
            </a-button>
            <a-popconfirm title="确定删除该错题记录？" @confirm="deleteWrongQuestion(item.id)">
              <a-button type="link" danger>删除</a-button>
            </a-popconfirm>
          </div>
        </div>
      </div>

      <a-empty v-if="!loading && wrongQuestions.length === 0" description="暂无错题">
        <template #description>
          <p>还没有错题记录</p>
          <p style="color: var(--color-text-muted); font-size: 13px;">去练习几道题，做错的题目会自动收录到这里</p>
        </template>
        <a-button type="primary" @click="$router.push('/practice')">开始练习</a-button>
      </a-empty>
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
}

.wrong-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 12px;
  background: var(--color-bg-card);
  transition: background-color 0.2s;
}

.wrong-item.selected {
  background: var(--color-primary-bg, #e6f7ff);
  border-color: var(--color-primary, #1890ff);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
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

.footer-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
