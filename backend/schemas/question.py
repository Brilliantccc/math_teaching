"""题目相关模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    """创建题目请求"""
    title: str = ''
    content: str = ''
    tags: str = '[]'
    difficulty: int = Field(default=1, ge=1, le=3)
    source: str = ''
    answer: str = ''
    analysis: str = ''
    grade: str = '初一'
    category: str = ''
    paper_id: Optional[int] = None
    paper_question_number: Optional[int] = None


class QuestionUpdate(BaseModel):
    """更新题目请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=3)
    source: Optional[str] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    title: str
    content: str
    tags: str
    difficulty: int
    source: str
    image_path: str
    answer: str
    analysis: str
    grade: str
    category: str
    paper_id: Optional[int] = None
    paper_question_number: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


class QuestionListResponse(BaseModel):
    """题目列表响应"""
    questions: List[QuestionResponse]
    total: int
    page: int
    per_page: int
    pages: int


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int]


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ids: List[int]
    updates: dict
