"""题目相关模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    """创建题目请求"""
    content: str = ''
    tags: str = '[]'
    difficulty: int = Field(default=1, ge=1, le=3)
    source: str = ''
    answer_analysis: str = ''
    grade: str = '初一'
    category: str = ''
    paper_id: Optional[int] = None
    paper_question_number: Optional[int] = None


class QuestionUpdate(BaseModel):
    """更新题目请求"""
    content: Optional[str] = None
    tags: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=3)
    source: Optional[str] = None
    answer_analysis: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    image_path: Optional[str] = None
    images: Optional[str] = None


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    content: str
    tags: str
    difficulty: int
    source: str
    image_path: str
    images: str = '[]'  # JSON array: 多图片URL列表
    answer_analysis: str
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


class QuestionBatchItem(BaseModel):
    """批量创建中的单个题目"""
    content: str = ''
    answer_analysis: str = ''
    grade: str = '初一'
    category: str = ''
    difficulty: int = 1
    image_path: str = ''
    images: str = '[]'  # JSON array: 多图片URL列表


class BatchCreateRequest(BaseModel):
    """批量创建题目请求"""
    questions: List[QuestionBatchItem]


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int]


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ids: List[int]
    updates: dict
