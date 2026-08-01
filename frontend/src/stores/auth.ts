/** 认证状态管理 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { api } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')
  const isAdmin = computed(() => user.value?.role === 'admin')

  /** 登录 */
  async function login(username: string, password: string) {
    const response = await api.post('/api/auth/login', { username, password })
    const data = response.data
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    return data
  }

  /** 注册 */
  async function register(username: string, password: string, role: string = 'student') {
    const response = await api.post('/api/auth/register', {
      username,
      password,
      role,
      display_name: username
    })
    const data = response.data
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    return data
  }

  /** 登出 */
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  /** 获取当前用户信息 */
  async function fetchUser() {
    if (!token.value) return null
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data
      return response.data
    } catch (error) {
      logout()
      return null
    }
  }

  /** 初始化：如果token存在则获取用户信息 */
  async function init() {
    if (token.value) {
      await fetchUser()
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isTeacher,
    isAdmin,
    login,
    register,
    logout,
    fetchUser,
    init
  }
})
