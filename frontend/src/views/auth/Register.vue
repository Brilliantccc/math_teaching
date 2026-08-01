<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'student'
})
const loading = ref(false)

async function handleSubmit() {
  if (!formState.username || !formState.password) {
    message.warning('请填写完整信息')
    return
  }

  if (formState.password !== formState.confirmPassword) {
    message.warning('两次输入的密码不一致')
    return
  }

  if (formState.password.length < 6) {
    message.warning('密码长度至少6位')
    return
  }

  loading.value = true
  try {
    await authStore.register(formState.username, formState.password, formState.role)
    message.success('注册成功')
    router.push('/')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="register-title">数学题库</h1>
      <p class="register-subtitle">用户注册</p>

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
            placeholder="密码（至少6位）"
            size="large"
          >
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-input-password
            v-model:value="formState.confirmPassword"
            placeholder="确认密码"
            size="large"
          >
            <template #prefix><LockOutlined /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-radio-group v-model:value="formState.role" button-style="solid">
            <a-radio-button value="student">学生</a-radio-button>
            <a-radio-button value="teacher">教师</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
            size="large"
          >
            注册
          </a-button>
        </a-form-item>

        <div class="register-links">
          <router-link to="/login">已有账号？去登录</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.register-title {
  text-align: center;
  font-size: 28px;
  color: #1890ff;
  margin-bottom: 8px;
}

.register-subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 32px;
}

.register-links {
  text-align: center;
}
</style>
