<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: ''
})
const loading = ref(false)

async function handleSubmit() {
  if (!formState.username || !formState.password) {
    message.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await authStore.login(formState.username, formState.password)
    message.success('登录成功')
    const redirect = route.query.redirect as string
    router.push(redirect || '/')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">数学题库</h1>
      <p class="login-subtitle">用户登录</p>

      <a-form @submit.prevent="handleSubmit">
        <a-form-item>
          <a-input
            v-model:value="formState.username"
            placeholder="用户名"
            size="large"
          >
            <template #prefix><UserOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item>
          <a-input-password
            v-model:value="formState.password"
            placeholder="密码"
            size="large"
          >
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
            size="large"
          >
            登录
          </a-button>
        </a-form-item>

        <div class="login-links">
          <router-link to="/register">注册账号</router-link>
          <router-link to="/forgot-password">忘记密码</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--color-primary);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
}

.login-title {
  text-align: center;
  font-size: 28px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.login-subtitle {
  text-align: center;
  color: var(--color-text-muted);
  margin-bottom: 32px;
}

.login-links {
  display: flex;
  justify-content: space-between;
}
</style>
