/** API 封装层 */

import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      message.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (status === 403) {
      message.error('权限不足')
    } else if (status === 404) {
      message.error('资源不存在')
    } else if (status === 500) {
      message.error('服务器错误')
    } else if (detail) {
      message.error(detail)
    } else {
      message.error('请求失败')
    }

    return Promise.reject(error)
  }
)

export { api }
