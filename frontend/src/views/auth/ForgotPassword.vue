<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, KeyOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const formState = reactive({
  username: '',
  resetCode: '',
  newPassword: ''
})
const loading = ref(false)

async function handleSubmit() {
  if (!formState.username || !formState.resetCode || !formState.newPassword) {
    message.warning('请填写完整信息')
    return
  }

  if (formState.newPassword.length < 6) {
    message.warning('密码长度至少6位')
    return
  }

  loading.value = true
  try {
    await api.post('/api/auth/reset', {
      username: formState.username,
      reset_code: formState.resetCode,
      new_password: formState.newPassword
    })
    message.success('密码重置成功')
    router.push('/login')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="forgot-container">
    <div class="forgot-card">
      <h1 class="forgot-title">数学题库</h1>
      <p class="forgot-subtitle">重置密码</p>

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
          <a-input
            v-model:value="formState.resetCode"
            placeholder="重置码"
            size="large"
          >
            <template #prefix><KeyOutlined /></template>
          </a-input>
        </a-form-item>

        <a-form-item>
          <a-input-password
            v-model:value="formState.newPassword"
            placeholder="新密码（至少6位）"
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
            重置密码
          </a-button>
        </a-form-item>

        <div class="forgot-links">
          <router-link to="/login">返回登录</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<style scoped>
.forgot-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--color-primary);
}

.forgot-card {
  width: 400px;
  padding: 40px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-modal);
}

.forgot-title {
  text-align: center;
  font-size: 28px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.forgot-subtitle {
  text-align: center;
  color: var(--color-text-muted);
  margin-bottom: 32px;
}

.forgot-links {
  text-align: center;
}
</style>
