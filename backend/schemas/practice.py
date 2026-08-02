"""练习相关模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class StartPracticeRequest(BaseModel):
    """开始练习请求"""
    tag: str = ''
    grade: str = ''
    count: int = Field(default=10, ge=1, le=100)


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    question_id: int
    answer: str = ''


class SubmitAnswerResponse(BaseModel):
    """提交答案响应"""
    is_correct: bool
    answer_analysis: str


class WrongQuestionResponse(BaseModel):
    """错题响应"""
    id: int
    user_id: int
    question_id: int
    wrong_count: int
    last_wrong_at: Optional[str] = None
    mastered: int
    created_at: Optional[str] = None
    question: Optional[dict] = None


class WrongQuestionListResponse(BaseModel):
    """错题列表响应"""
    wrong_questions: List[WrongQuestionResponse]
    total: int
    page: int
    per_page: int
    pages: int


class PracticeSessionResponse(BaseModel):
    """练习会话响应"""
    question_ids: List[int]
    count: int


class RetryRequest(BaseModel):
    """重练请求"""
    count: int = Field(default=10, ge=1, le=100)


class TagStats(BaseModel):
    """知识点统计"""
    tag: str
    total: int
    correct: int
    accuracy: float


class DifficultyStats(BaseModel):
    """难度统计"""
    difficulty: int
    total: int
    correct: int
    accuracy: float


class RecentPractice(BaseModel):
    """最近练习记录"""
    id: int
    question_id: int
    question_title: str
    is_correct: int
    created_at: Optional[str] = None


class PracticeStatsResponse(BaseModel):
    """练习统计响应"""
    total: int
    correct: int
    accuracy: float
    tag_stats: List[TagStats]
    difficulty_stats: List[DifficultyStats]
    recent: List[RecentPractice]
    wrong_total: int
    wrong_unmastered: int
    streak_days: int
