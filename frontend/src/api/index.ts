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

/** LLM 状态查询 */
export async function getLLMStatus() {
  const res = await api.get('/api/llm/status')
  return res.data
}

/** AI 图片识别 → 结构化题目 */
export async function extractFromImage(file: File) {
  const formData = new FormData()
  formData.append('image', file)
  const res = await api.post('/api/llm/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
  return res.data
}

/** AI 生成答案和解析 */
export async function analyzeQuestion(content: string) {
  const res = await api.post('/api/llm/analyze', { content }, { timeout: 60000 })
  return res.data
}
