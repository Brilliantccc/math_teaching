<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import { message } from 'ant-design-vue'

const loading = ref(false)
const questionIds = ref<number[]>([])

const formState = ref({
  count: 10,
  tags: [] as string[],
  difficulties: [1, 2, 3]
})

async function autoGenerate() {
  loading.value = true
  try {
    const response = await api.post('/api/tests/auto', formState.value)
    questionIds.value = response.data.question_ids
    message.success(`已生成 ${response.data.count} 道题目`)
  } catch (error) {
    console.error('Failed to generate test:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="test">
    <h2>智能组卷</h2>

    <div class="config-panel">
      <a-form layout="inline">
        <a-form-item label="题目数量">
          <a-input-number v-model:value="formState.count" :min="1" :max="50" />
        </a-form-item>
        <a-form-item label="难度">
          <a-checkbox-group v-model:value="formState.difficulties">
            <a-checkbox :value="1">简单</a-checkbox>
            <a-checkbox :value="2">中等</a-checkbox>
            <a-checkbox :value="3">困难</a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :loading="loading" @click="autoGenerate">
            自动生成
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <div v-if="questionIds.length > 0" class="result">
      <a-alert
        :message="`已生成 ${questionIds.length} 道题目`"
        type="success"
        show-icon
      />
    </div>
  </div>
</template>

<style scoped>
.test {
  max-width: 900px;
  margin: 0 auto;
}

.config-panel {
  background: var(--color-bg-hover);
  padding: 24px;
  border-radius: var(--radius-lg);
  margin-top: 16px;
}

.result {
  margin-top: 16px;
}
</style>
