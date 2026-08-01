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
  title: string
  content: string
  tags: string
  difficulty: number
  source: string
  image_path: string
  answer: string
  analysis: string
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
  created_by: number | null
  created_at: string | null
  questions?: Question[]
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
  title: string
  content: string
  answer: string
  analysis: string
  tags: string[]
  difficulty: number
  category: string
}

/** LLM 分析结果 */
export interface LLMAnalyzeResult {
  answer: string
  analysis: string
}
