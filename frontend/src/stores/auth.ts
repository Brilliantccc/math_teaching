/** 认证状态管理 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { api } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const userFetched = ref(false) // 标记是否已尝试获取用户信息

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')
  const isAdmin = computed(() => user.value?.role === 'admin')

  /** 登录 */
  async function login(username: string, password: string) {
    const response = await api.post('/api/auth/login', { username, password })
    const data = response.data
    token.value = data.access_token
    user.value = data.user
    userFetched.value = true
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
    userFetched.value = true
    localStorage.setItem('token', data.access_token)
    return data
  }

  /** 登出 */
  function logout() {
    token.value = null
    user.value = null
    userFetched.value = false
    localStorage.removeItem('token')
  }

  /** 获取当前用户信息 */
  async function fetchUser() {
    if (!token.value) {
      userFetched.value = true
      return null
    }
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data
      userFetched.value = true
      return response.data
    } catch (error: any) {
      // 只有 401 错误才清除 token（token 过期或无效）
      // 网络错误或其他错误保留 token，等待下次重试
      if (error.response?.status === 401) {
        console.warn('Token 已过期或无效，清除登录状态')
        logout()
      } else {
        console.warn('获取用户信息失败，保留 token 等待重试:', error.message)
        user.value = null
        userFetched.value = true
      }
      return null
    }
  }

  /** 初始化：如果token存在则获取用户信息 */
  async function init() {
    // 只有在 token 存在且未尝试获取过用户信息时才调用
    if (token.value && !userFetched.value) {
      await fetchUser()
    }
  }

  return {
    user,
    token,
    userFetched,
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
