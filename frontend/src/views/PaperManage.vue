<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { Paper } from '@/types'
import { message } from 'ant-design-vue'

const papers = ref<Paper[]>([])
const loading = ref(false)

async function loadPapers() {
  loading.value = true
  try {
    const response = await api.get('/api/papers')
    papers.value = response.data.papers
  } catch (error) {
    console.error('Failed to load papers:', error)
  } finally {
    loading.value = false
  }
}

async function deletePaper(id: number) {
  try {
    await api.delete(`/api/papers/${id}`)
    message.success('已删除')
    loadPapers()
  } catch (error) {
    console.error('Failed to delete paper:', error)
  }
}

onMounted(() => {
  loadPapers()
})
</script>

<template>
  <div class="paper-manage">
    <div class="header">
      <h2>试卷管理</h2>
    </div>

    <a-spin :spinning="loading">
      <a-table
        :data-source="papers"
        :columns="[
          { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
          { title: '名称', dataIndex: 'name', key: 'name' },
          { title: '年级', dataIndex: 'grade', key: 'grade', width: 80 },
          { title: '题目数', dataIndex: 'questions_count', key: 'questions_count', width: 80 },
          { title: '操作', key: 'action', width: 120 }
        ]"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-popconfirm title="确定删除？" @confirm="deletePaper(record.id)">
              <a-button type="link" danger>删除</a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </a-spin>
  </div>
</template>

<style scoped>
.paper-manage {
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
