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
export async function extractFromImage(file: File, signal?: AbortSignal) {
  const formData = new FormData()
  formData.append('image', file)
  const config: any = {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,  // 5分钟，AI识别+图片裁剪需要较长时间
  }
  if (signal) {
    config.signal = signal
  }
  const res = await api.post('/api/llm/extract', formData, config)
  return res.data
}

/** AI 生成答案和解析 */
export async function analyzeQuestion(content: string, image_descriptions?: string[], signal?: AbortSignal) {
  const config: any = {
    timeout: 120000,  // 2分钟
  }
  if (signal) {
    config.signal = signal
  }
  const res = await api.post('/api/llm/analyze', { content, image_descriptions }, config)
  return res.data
}

/** AI 批量图片识别 → 多道题目 */
export async function batchExtractFromImages(files: File[]) {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  const res = await api.post('/api/llm/batch-extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000  // 10分钟，批量识别需要更长时间
  })
  return res.data
}

/** 批量创建题目 */
export async function batchCreateQuestions(questions: Array<{
  content: string
  answer_analysis: string
  grade: string
  category: string
  question_type?: string
  difficulty: number
  image_path?: string
}>) {
  const res = await api.post('/api/questions/batch-create', { questions })
  return res.data
}

// ========== 管理功能 API ==========

/** 获取年级列表 */
export async function getGrades() {
  const res = await api.get('/api/grades')
  return res.data
}

/** 获取分类数据 */
export async function getCategories() {
  const res = await api.get('/api/categories')
  return res.data
}

/** 获取标签列表 */
export async function getTags(grade?: string) {
  const res = await api.get('/api/tags', { params: { grade } })
  return res.data
}

/** 获取统计数据 */
export async function getStats() {
  const res = await api.get('/api/stats')
  return res.data
}

/** 导出数据库备份 */
export async function exportBackup() {
  const token = localStorage.getItem('token')
  const response = await fetch('http://localhost:8000/api/backup/export', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  if (!response.ok) throw new Error('导出失败')
  return response.blob()
}

/** 导入数据库备份 */
export async function importBackup(file: File) {
  const formData = new FormData()
  formData.append('backup_file', file)
  const res = await api.post('/api/backup/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

/** 导出所有题目 */
export async function exportQuestions() {
  const res = await api.get('/api/questions/export')
  return res.data
}

/** 导入题目 */
export async function importQuestions(data: { questions: any[] }) {
  const res = await api.post('/api/questions/import', data)
  return res.data
}

/** 获取标准分类 */
export async function getStandardCategories() {
  const res = await api.get('/api/categories/standard')
  return res.data
}

/** 获取当前分类 */
export async function getCurrentCategories() {
  const res = await api.get('/api/categories/current')
  return res.data
}

/** 标准化分类 */
export async function normalizeCategories() {
  const res = await api.post('/api/categories/normalize')
  return res.data
}

/** 批量更新分类 */
export async function batchUpdateCategories(ids: number[], category: string) {
  const res = await api.put('/api/categories/batch-update', { ids, category })
  return res.data
}

// ========== 学生数据 API ==========

/** 获取学生列表 */
export async function getStudents(params?: { page?: number; per_page?: number; keyword?: string }) {
  const res = await api.get('/api/students', { params })
  return res.data
}

/** 获取学生统计 */
export async function getStudentStats(studentId: number) {
  const res = await api.get(`/api/students/${studentId}/stats`)
  return res.data
}

/** 获取学生错题 */
export async function getStudentWrongQuestions(studentId: number, params?: { page?: number; per_page?: number; mastered?: string }) {
  const res = await api.get(`/api/students/${studentId}/wrong-questions`, { params })
  return res.data
}

/** 获取班级统计 */
export async function getClassStats() {
  const res = await api.get('/api/students/class/stats')
  return res.data
}

// ========== 练习扩展 API ==========

/** 错题重练 */
export async function retryWrongQuestions(count: number = 10) {
  const res = await api.post('/api/practice/wrong-questions/retry', { count })
  return res.data
}

// ========== 用户管理 API ==========

/** 获取用户列表 */
export async function getUsers() {
  const res = await api.get('/api/users')
  return res.data
}

/** 更新用户 */
export async function updateUser(userId: number, data: { role?: string; display_name?: string; password?: string }) {
  const res = await api.put(`/api/users/${userId}`, data)
  return res.data
}

/** 删除用户 */
export async function deleteUser(userId: number) {
  const res = await api.delete(`/api/users/${userId}`)
  return res.data
}

// ========== 试卷管理 API ==========

/** 创建试卷 */
export async function createPaper(formData: FormData) {
  const res = await api.post('/api/papers', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

/** 获取试卷详情 */
export async function getPaper(paperId: number) {
  const res = await api.get(`/api/papers/${paperId}`)
  return res.data
}

/** 上传答案 */
export async function uploadPaperAnswer(paperId: number, file: File) {
  const formData = new FormData()
  formData.append('answer_pdf', file)
  const res = await api.post(`/api/papers/${paperId}/answer`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

/** 向试卷添加题目 */
export async function addPaperQuestion(paperId: number, data: any) {
  const res = await api.post(`/api/papers/${paperId}/questions`, data)
  return res.data
}
