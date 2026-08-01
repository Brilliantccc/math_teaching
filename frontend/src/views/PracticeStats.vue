<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { PracticeStats } from '@/types'

const stats = ref<PracticeStats | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await api.get('/api/practice/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="practice-stats">
    <h2>练习统计</h2>

    <a-spin :spinning="loading">
      <div v-if="stats" class="stats-content">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-card>
              <a-statistic title="总练习次数" :value="stats.total" />
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic title="正确次数" :value="stats.correct" :value-style="{ color: 'var(--color-success)' }" />
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic title="正确率" :value="stats.accuracy" suffix="%" />
            </a-card>
          </a-col>
          <a-col :span="6">
            <a-card>
              <a-statistic title="连续练习" :value="stats.streak_days" suffix="天" />
            </a-card>
          </a-col>
        </a-row>

        <a-divider />

        <h3>知识点分析</h3>
        <a-table
          :data-source="stats.tag_stats"
          :columns="[
            { title: '知识点', dataIndex: 'tag', key: 'tag' },
            { title: '练习次数', dataIndex: 'total', key: 'total' },
            { title: '正确次数', dataIndex: 'correct', key: 'correct' },
            { title: '正确率', dataIndex: 'accuracy', key: 'accuracy', customRender: ({ text }: { text: any }) => text + '%' }
          ]"
          :pagination="{ pageSize: 10 }"
        />
      </div>
    </a-spin>
  </div>
</template>

<style scoped>
.practice-stats {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-content {
  margin-top: 16px;
}

h3 {
  margin: 16px 0;
}
</style>
