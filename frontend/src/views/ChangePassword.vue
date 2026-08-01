<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { message } from 'ant-design-vue'

const router = useRouter()

const formState = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const loading = ref(false)

async function handleSubmit() {
  if (!formState.oldPassword || !formState.newPassword) {
    message.warning('请填写完整信息')
    return
  }

  if (formState.newPassword !== formState.confirmPassword) {
    message.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    await api.put('/api/auth/password', {
      old_password: formState.oldPassword,
      new_password: formState.newPassword,
      confirm_password: formState.confirmPassword
    })
    message.success('密码修改成功')
    router.push('/')
  } catch (error) {
    console.error('Failed to change password:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="change-password">
    <h2>修改密码</h2>

    <a-form layout="vertical" style="max-width: 400px">
      <a-form-item label="原密码">
        <a-input-password v-model:value="formState.oldPassword" />
      </a-form-item>

      <a-form-item label="新密码">
        <a-input-password v-model:value="formState.newPassword" />
      </a-form-item>

      <a-form-item label="确认新密码">
        <a-input-password v-model:value="formState.confirmPassword" />
      </a-form-item>

      <a-form-item>
        <a-button type="primary" :loading="loading" @click="handleSubmit">
          修改密码
        </a-button>
      </a-form-item>
    </a-form>
  </div>
</template>

<style scoped>
.change-password {
  max-width: 600px;
  margin: 0 auto;
}
</style>
