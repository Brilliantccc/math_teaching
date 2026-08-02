/** API 封装层 */

import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000
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
    const url = error.config?.url

    if (status === 401) {
      // 对于获取用户信息的请求，不清除 token（由 auth store 处理）
      if (url && url.includes('/api/auth/me')) {
        // 传递错误，由 auth store 处理
        return Promise.reject(error)
      }
      // 对于其他请求，清除 token 并跳转登录
      message.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (status === 403) {
      message.error('没有权限执行此操作，请联系管理员')
    } else if (status === 404) {
      message.error('请求的内容不存在，可能已被删除')
    } else if (status === 500) {
      message.error('服务器出错，请稍后重试')
    } else if (detail) {
      message.error(detail)
    } else {
      message.error('网络请求失败，请检查网络连接')
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
    timeout: 120000
  })
  return res.data
}

/** AI 生成答案和解析 */
export async function analyzeQuestion(content: string) {
  const res = await api.post('/api/llm/analyze', { content }, { timeout: 60000 })
  return res.data
}

/** AI 批量图片识别 → 多道题目 */
export async function batchExtractFromImages(files: File[]) {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  const res = await api.post('/api/llm/batch-extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
  return res.data
}

/** 批量创建题目 */
export async function batchCreateQuestions(questions: Array<{
  content: string
  answer_analysis: string
  grade: string
  category: string
  difficulty: number
  image_path?: string
}>) {
  const res = await api.post('/api/questions/batch-create', { questions })
  return res.data
}
