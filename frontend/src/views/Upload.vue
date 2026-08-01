<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useGradeStore } from '@/stores'
import { message } from 'ant-design-vue'

const router = useRouter()
const gradeStore = useGradeStore()

const formState = reactive({
  title: '',
  content: '',
  answer: '',
  analysis: '',
  grade: gradeStore.currentGrade,
  category: '',
  difficulty: 1
})
const fileList = ref<any[]>([])
const loading = ref(false)
const aiLoading = ref(false)

async function handleSubmit() {
  if (!formState.title && !formState.content) {
    message.warning('请输入题目标题或内容')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    Object.keys(formState).forEach(key => {
      formData.append(key, (formState as any)[key])
    })
    if (fileList.value.length > 0) {
      formData.append('image', fileList.value[0].originFileObj)
    }

    await api.post('/api/questions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    message.success('上传成功')
    router.push('/manage')
  } catch (error) {
    console.error('Failed to upload:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="upload">
    <h2>上传题目</h2>

    <a-form layout="vertical" style="max-width: 600px">
      <a-form-item label="标题">
        <a-input v-model:value="formState.title" placeholder="题目标题" />
      </a-form-item>

      <a-form-item label="内容">
        <a-textarea v-model:value="formState.content" :rows="4" placeholder="题目内容" />
      </a-form-item>

      <a-form-item label="图片">
        <a-upload
          v-model:file-list="fileList"
          :before-upload="() => false"
          list-type="picture"
          :max-count="1"
        >
          <a-button>选择图片</a-button>
        </a-upload>
      </a-form-item>

      <a-form-item label="答案">
        <a-textarea v-model:value="formState.answer" :rows="2" placeholder="答案" />
      </a-form-item>

      <a-form-item label="解析">
        <a-textarea v-model:value="formState.analysis" :rows="3" placeholder="解析" />
      </a-form-item>

      <a-form-item label="年级">
        <a-select v-model:value="formState.grade" style="width: 100%">
          <a-select-option v-for="g in gradeStore.grades" :key="g" :value="g">{{ g }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="难度">
        <a-radio-group v-model:value="formState.difficulty">
          <a-radio :value="1">简单</a-radio>
          <a-radio :value="2">中等</a-radio>
          <a-radio :value="3">困难</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item>
        <a-button type="primary" :loading="loading" @click="handleSubmit">
          提交
        </a-button>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.upload {
  max-width: 800px;
  margin: 0 auto;
}
</style>
