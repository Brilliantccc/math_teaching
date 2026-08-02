"""组卷相关模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class TestCreate(BaseModel):
    """创建组卷请求"""
    name: Optional[str] = None
    question_ids: List[int] = []
    score_per_question: int = 10


class TestResponse(BaseModel):
    """组卷响应"""
    id: int
    name: str
    question_ids: str
    score_per_question: int = 10
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    questions: Optional[List[dict]] = None


class TestListResponse(BaseModel):
    """组卷列表响应"""
    tests: List[TestResponse]


class AutoGenerateRequest(BaseModel):
    """自动生成组卷请求"""
    tags: List[str] = []
    count: int = Field(default=10, ge=1, le=100)
    difficulties: List[int] = [1, 2, 3]
    grade: str = ''
    category: str = ''


class PreviewPdfRequest(BaseModel):
    """预览导出PDF请求"""
    question_ids: List[int]
    title: str = '数学试卷'
