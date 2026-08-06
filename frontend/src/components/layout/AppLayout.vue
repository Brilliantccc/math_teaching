<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { getLLMStatus } from '@/api'
import {
  MenuOutlined,
  HomeOutlined,
  SearchOutlined,
  EditOutlined,
  LineChartOutlined,
  WarningOutlined,
  FileTextOutlined,
  TeamOutlined,
  UploadOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const collapsed = ref(false)
const llmConfigured = ref(false)

onMounted(async () => {
  try {
    const status = await getLLMStatus()
    llmConfigured.value = status.configured
  } catch {
    // 静默处理
  }
})

const menuItems = computed(() => {
  const items = [
    { key: '/', icon: HomeOutlined, label: '首页' },
    { key: '/browse', icon: SearchOutlined, label: '浏览题库' },
    { key: '/practice', icon: EditOutlined, label: '练习' },
    { key: '/wrong-questions', icon: WarningOutlined, label: '错题本' },
    { key: '/test', icon: FileTextOutlined, label: '组卷' },
  ]

  if (authStore.isTeacher) {
    items.push(
      { key: '/manage', icon: TeamOutlined, label: '管理' },
      { key: '/upload', icon: UploadOutlined, label: '上传' },
      { key: '/test-manage', icon: FileTextOutlined, label: '组卷管理' },
      { key: '/student-data', icon: LineChartOutlined, label: '学生数据' },
    )
  }

  return items
})

function handleMenuClick({ key }: { key: string }) {
  router.push(key)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <a-layout class="app-layout">
    <!-- 导航栏 -->
    <a-layout-header class="header">
      <div class="header-left">
        <MenuOutlined class="trigger" @click="collapsed = !collapsed" />
        <span class="logo">数学题库</span>
      </div>

      <div class="header-right">
        <a-tooltip>
          <template #title>AI: {{ llmConfigured ? '已配置' : '未配置' }}</template>
          <a-badge :status="llmConfigured ? 'success' : 'default'" text="AI" />
        </a-tooltip>

        <a-dropdown v-if="authStore.isAuthenticated">
          <a-button type="text">
            <UserOutlined />
            {{ authStore.user?.display_name || authStore.user?.username }}
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="change-password" @click="router.push('/change-password')">
                修改密码
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout">
                <LogoutOutlined /> 退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-button v-else type="link" @click="router.push('/login')">
          登录
        </a-button>
      </div>
    </a-layout-header>

    <a-layout>
      <!-- 侧边栏 -->
      <a-layout-sider
        v-model:collapsed="collapsed"
        :trigger="null"
        collapsible
        breakpoint="lg"
        @breakpoint="(broken: boolean) => collapsed = broken"
      >
        <a-menu
          mode="inline"
          :selected-keys="[$route.path]"
          @click="handleMenuClick"
        >
          <a-menu-item v-for="item in menuItems" :key="item.key">
            <component :is="item.icon" />
            <span>{{ item.label }}</span>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>

      <!-- 主内容区 -->
      <a-layout-content class="content">
        <slot />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-bg-card);
  padding: 0 24px;
  box-shadow: var(--shadow-rest);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  transition: color var(--transition-normal);
}

.trigger:hover {
  color: var(--color-primary);
}

.logo {
  font-size: 18px;
  font-weight: bold;
  color: var(--color-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.content {
  margin: 24px;
  padding: 24px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  min-height: calc(100vh - 64px - 48px);
}

:deep(.ant-layout-sider) {
  background: var(--color-bg-card);
  position: sticky;
  top: 64px;
  align-self: flex-start;
  height: calc(100vh - 64px);
  overflow-y: auto;
}

:deep(.ant-menu-inline) {
  border-right: none;
}
</style>
