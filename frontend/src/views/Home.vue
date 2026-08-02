<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { api } from '@/api'
import {
  SearchOutlined,
  EditOutlined,
  WarningOutlined,
  FileTextOutlined,
  TeamOutlined,
  UploadOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const stats = ref({
  total: 0,
  papers: 0
})

const loading = ref(true)

onMounted(async () => {
  try {
    const response = await api.get('/api/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
})

const features = [
  {
    icon: SearchOutlined,
    title: '浏览题库',
    description: '查看所有数学题目，支持按年级、分类、难度筛选',
    action: () => router.push('/browse')
  },
  {
    icon: EditOutlined,
    title: '在线练习',
    description: '选择题目进行练习，自动记录错题',
    action: () => router.push('/practice')
  },
  {
    icon: WarningOutlined,
    title: '错题本',
    description: '查看错题记录，支持重练和标记掌握',
    action: () => router.push('/wrong-questions')
  },
  {
    icon: FileTextOutlined,
    title: '智能组卷',
    description: '自动生成试卷，支持导出PDF',
    action: () => router.push('/test')
  }
]

const teacherFeatures = [
  {
    icon: UploadOutlined,
    title: '上传题目',
    description: '上传新题目，支持图片识别和AI生成解析',
    action: () => router.push('/upload')
  },
  {
    icon: TeamOutlined,
    title: '学生数据',
    description: '查看学生练习数据和统计分析',
    action: () => router.push('/student-data')
  }
]
</script>

<template>
  <div class="home">
    <div class="welcome-section">
      <h1>欢迎使用数学题库</h1>
      <p>为教师和学生提供便捷的数学题目管理与练习平台</p>
    </div>

    <a-spin :spinning="loading">
      <div class="stats-section">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-statistic title="题目总数" :value="stats.total" class="stat-card" />
          </a-col>
          <a-col :span="12">
            <a-statistic title="试卷数量" :value="stats.papers" class="stat-card" />
          </a-col>
        </a-row>
      </div>
    </a-spin>

    <div class="features-section">
      <h2>功能入口</h2>
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="6" v-for="feature in features" :key="feature.title">
          <a-card hoverable @click="feature.action" class="feature-card">
            <template #cover>
              <div class="feature-icon">
                <component :is="feature.icon" />
              </div>
            </template>
            <a-card-meta :title="feature.title" :description="feature.description" />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <div v-if="authStore.isTeacher" class="features-section">
      <h2>教师功能</h2>
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" v-for="feature in teacherFeatures" :key="feature.title">
          <a-card hoverable @click="feature.action" class="feature-card">
            <template #cover>
              <div class="feature-icon">
                <component :is="feature.icon" />
              </div>
            </template>
            <a-card-meta :title="feature.title" :description="feature.description" />
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 48px;
  padding: 32px 0;
}

.welcome-section h1 {
  font-size: clamp(24px, 4vw, 36px);
  color: var(--color-primary);
  margin-bottom: 12px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.welcome-section p {
  color: var(--color-text-secondary);
  font-size: 16px;
  max-width: 48ch;
  margin: 0 auto;
  line-height: 1.6;
}

.stats-section {
  margin-bottom: 48px;
}

.stat-card {
  text-align: center;
  padding: 24px;
  background: var(--color-primary-bg);
  border-radius: var(--radius-lg);
}

.features-section {
  margin-bottom: 48px;
}

.features-section h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--color-text-primary);
}

.feature-card {
  cursor: pointer;
  transition: transform var(--transition-normal), box-shadow var(--transition-normal);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.feature-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  font-size: 48px;
  color: var(--color-primary);
  background: var(--color-primary-bg);
}

.feature-card :deep(.ant-card-body) {
  padding: 16px;
}

.feature-card :deep(.ant-card-meta-description) {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 768px) {
  .welcome-section h1 {
    font-size: 24px;
  }

  .feature-icon {
    height: 80px;
    font-size: 36px;
  }
}
</style>
