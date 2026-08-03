/** 用户类型 */
export interface User {
  id: number
  username: string
  role: 'student' | 'teacher' | 'admin'
  display_name: string
  created_at: string | null
  last_login: string | null
}

/** 登录请求 */
export interface LoginRequest {
  username: string
  password: string
}

/** 注册请求 */
export interface RegisterRequest {
  username: string
  password: string
  display_name?: string
  role?: 'student' | 'teacher'
}

/** 令牌响应 */
export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

/** 题目类型 */
export interface Question {
  id: number
  content: string
  tags: string
  difficulty: number
  source: string
  image_path: string
  images: string  // JSON数组格式的图片路径列表
  answer_analysis: string
  grade: string
  category: string
  paper_id: number | null
  paper_question_number: number | null
  created_by: number | null
  created_at: string | null
}

/** 题目列表响应 */
export interface QuestionListResponse {
  questions: Question[]
  total: number
  page: number
  per_page: number
  pages: number
}

/** 试卷类型 */
export interface Paper {
  id: number
  name: string
  grade: string
  image_path: string
  pdf_path: string
  answer_pdf_path: string
  source: string
  created_by: number | null
  created_at: string | null
  questions_count: number
  questions?: Question[]
}

/** 组卷类型 */
export interface Test {
  id: number
  name: string
  question_ids: string
  score_per_question: number
  question_scores: string | null
  created_by: number | null
  created_at: string | null
  questions?: Question[]
}

/** 组卷创建请求 */
export interface TestCreateRequest {
  name?: string
  question_ids: number[]
  score_per_question?: number
  question_scores?: Record<number, number>
}

/** 自动生成组卷请求 */
export interface AutoGenerateRequest {
  tags?: string[]
  count?: number
  difficulties?: number[]
  grade?: string
  category?: string
}

/** 错题类型 */
export interface WrongQuestion {
  id: number
  user_id: number
  question_id: number
  wrong_count: number
  last_wrong_at: string | null
  mastered: number
  created_at: string | null
  question?: Question
}

/** 练习统计 */
export interface PracticeStats {
  total: number
  correct: number
  accuracy: number
  tag_stats: TagStats[]
  difficulty_stats: DifficultyStats[]
  recent: RecentPractice[]
  wrong_total: number
  wrong_unmastered: number
  streak_days: number
}

/** 知识点统计 */
export interface TagStats {
  tag: string
  total: number
  correct: number
  accuracy: number
}

/** 难度统计 */
export interface DifficultyStats {
  difficulty: number
  total: number
  correct: number
  accuracy: number
}

/** 最近练习记录 */
export interface RecentPractice {
  id: number
  question_id: number
  question_title: string
  is_correct: number
  created_at: string | null
}

/** 错题列表响应 */
export interface WrongQuestionListResponse {
  wrong_questions: WrongQuestion[]
  total: number
  page: number
  per_page: number
  pages: number
}

/** 学生数据 */
export interface StudentData {
  id: number
  username: string
  role: string
  display_name: string
  practice_count: number
  correct_count: number
  accuracy: number
  wrong_count: number
  wrong_unmastered: number
  last_practice: string | null
}

/** 班级统计 */
export interface ClassStats {
  total_students: number
  today_active: number
  total_practice: number
  avg_accuracy: number
  most_wrong_questions: { question_id: number; question_title: string; wrong_count: number }[]
  trend: { date: string; count: number }[]
}

/** LLM 状态 */
export interface LLMStatus {
  configured: boolean
  model: string
}

/** LLM 题目提取结果 */
export interface LLMExtractResult {
  content: string
  answer_analysis: string
  tags: string[]
  difficulty: number
  category: string
}

/** LLM 分析结果 */
export interface LLMAnalyzeResult {
  answer_analysis: string
}

/** 练习会话请求 */
export interface PracticeSessionRequest {
  tag?: string
  grade?: string
  count?: number
}

/** 提交答案请求 */
export interface SubmitAnswerRequest {
  question_id: number
  answer?: string
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

/** 重置密码请求 */
export interface ResetPasswordRequest {
  username: string
  reset_code: string
  new_password: string
}

/** 批量删除请求 */
export interface BatchDeleteRequest {
  ids: number[]
}

/** 批量更新请求 */
export interface BatchUpdateRequest {
  ids: number[]
  updates: Record<string, any>
}

/** 批量更新分类请求 */
export interface BatchUpdateCategoriesRequest {
  ids: number[]
  category: string
}

/** 错题重练请求 */
export interface RetryWrongQuestionsRequest {
  count?: number
}

/** 年级选项 */
export type GradeOption = '初一' | '初二' | '初三' | '高一' | '高二' | '高三'

/** 难度选项 */
export type DifficultyOption = 1 | 2 | 3

/** 角色选项 */
export type RoleOption = 'student' | 'teacher' | 'admin'

/** 标准分类 */
export type CategoryOption = '代数' | '函数' | '几何' | '统计与概率' | '数与计算' | '图形与变换' | '综合'
