<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()

// 认证页面（登录、注册、忘记密码）不使用 AppLayout
const isAuthPage = computed(() => {
  const authPages = ['Login', 'Register', 'ForgotPassword']
  return authPages.includes(route.name as string)
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
