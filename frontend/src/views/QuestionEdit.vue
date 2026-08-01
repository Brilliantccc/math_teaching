<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { message } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()

const formState = ref({
  title: '',
  content: '',
  answer: '',
  analysis: '',
  grade: '初一',
  difficulty: 1
})
const loading = ref(false)

async function loadQuestion() {
  try {
    const response = await api.get(`/api/questions/${route.params.id}`)
    formState.value = response.data
  } catch (error) {
    console.error('Failed to load question:', error)
  }
}

async function handleSave() {
  loading.value = true
  try {
    await api.put(`/api/questions/${route.params.id}`, formState.value)
    message.success('保存成功')
    router.push('/manage')
  } catch (error) {
    console.error('Failed to save:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadQuestion()
})
</script>

<template>
  <div class="question-edit">
    <h2>编辑题目</h2>

    <a-form layout="vertical" style="max-width: 600px">
      <a-form-item label="标题">
        <a-input v-model:value="formState.title" />
      </a-form-item>

      <a-form-item label="内容">
        <a-textarea v-model:value="formState.content" :rows="4" />
      </a-form-item>

      <a-form-item label="答案">
        <a-textarea v-model:value="formState.answer" :rows="2" />
      </a-form-item>

      <a-form-item label="解析">
        <a-textarea v-model:value="formState.analysis" :rows="3" />
      </a-form-item>

      <a-form-item label="难度">
        <a-radio-group v-model:value="formState.difficulty">
          <a-radio :value="1">简单</a-radio>
          <a-radio :value="2">中等</a-radio>
          <a-radio :value="3">困难</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item>
        <a-space>
          <a-button type="primary" :loading="loading" @click="handleSave">
            保存
          </a-button>
          <a-button @click="router.back()">取消</a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.question-edit {
  max-width: 800px;
  margin: 0 auto;
}
</style>
