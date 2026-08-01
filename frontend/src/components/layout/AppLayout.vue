<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useThemeStore, useGradeStore } from '@/stores'
import { GRADES } from '@/stores/grade'
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
  LogoutOutlined,
  DownOutlined,
  BulbOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const gradeStore = useGradeStore()

const collapsed = ref(false)

const themeIcon = computed(() => BulbOutlined)

const themeText = computed(() => {
  switch (themeStore.mode) {
    case 'light': return '浅色'
    case 'dark': return '深色'
    default: return '跟随系统'
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

function handleGradeChange(grade: string) {
  gradeStore.setGrade(grade)
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

      <div class="header-center">
        <a-dropdown>
          <a-button>
            {{ gradeStore.currentGrade }}
            <template #icon><DownOutlined /></template>
          </a-button>
          <template #overlay>
            <a-menu @click="({ key }: { key: string }) => handleGradeChange(key)">
              <a-menu-item v-for="grade in GRADES" :key="grade">
                {{ grade }}
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>

      <div class="header-right">
        <a-dropdown>
          <a-button type="text">
            <component :is="themeIcon" />
            {{ themeText }}
          </a-button>
          <template #overlay>
            <a-menu @click="({ key }: { key: string }) => themeStore.setMode(key as any)">
              <a-menu-item key="light">
                <SettingOutlined /> 浅色
              </a-menu-item>
              <a-menu-item key="dark">
                <SettingOutlined /> 深色
              </a-menu-item>
              <a-menu-item key="system">
                <SettingOutlined /> 跟随系统
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>

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

.header-center {
  display: flex;
  align-items: center;
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
}

:deep(.ant-menu-inline) {
  border-right: none;
}
</style>
