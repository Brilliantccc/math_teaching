<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { StudentData as StudentDataType } from '@/types'

const students = ref<StudentDataType[]>([])
const total = ref(0)
const loading = ref(false)

async function loadStudents() {
  loading.value = true
  try {
    const response = await api.get('/api/students')
    students.value = response.data.students
    total.value = response.data.total
  } catch (error) {
    console.error('Failed to load students:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStudents()
})
</script>

<template>
  <div class="student-data">
    <h2>学生数据</h2>

    <a-spin :spinning="loading">
      <a-table
        :data-source="students"
        :columns="[
          { title: '用户名', dataIndex: 'username', key: 'username' },
          { title: '显示名', dataIndex: 'display_name', key: 'display_name' },
          { title: '练习次数', dataIndex: 'practice_count', key: 'practice_count' },
          { title: '正确率', dataIndex: 'accuracy', key: 'accuracy', customRender: ({ text }: { text: any }) => text + '%' },
          { title: '错题数', dataIndex: 'wrong_count', key: 'wrong_count' },
          { title: '最后练习', dataIndex: 'last_practice', key: 'last_practice' }
        ]"
        row-key="id"
      />
    </a-spin>
  </div>
</template>

<style scoped>
.student-data {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
