<script setup lang="ts">
import { computed, onErrorCaptured } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()

// 认证页面（登录、注册、忘记密码）不使用 AppLayout
const isAuthPage = computed(() => {
  const authPages = ['Login', 'Register', 'ForgotPassword']
  return authPages.includes(route.name as string)
})

// 全局错误处理 - 防止单个组件错误导致整个应用崩溃
onErrorCaptured((err, instance, info) => {
  console.error('[App] Component error:', err, info)
  // 阻止错误继续向上传播
  return false
})
</script>

<template>
  <AppLayout v-if="!isAuthPage">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>

<style>
#app {
  min-height: 100vh;
}
</style>
