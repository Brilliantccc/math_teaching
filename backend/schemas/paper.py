"""试卷相关模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class PaperResponse(BaseModel):
    """试卷响应"""
    id: int
    name: str
    grade: str
    image_path: str
    pdf_path: str
    answer_pdf_path: str
    source: str
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    questions_count: int = 0
    questions: Optional[List[dict]] = None


class PaperListResponse(BaseModel):
    """试卷列表响应"""
    papers: List[PaperResponse]


class AddPaperQuestionRequest(BaseModel):
    """向试卷添加题目"""
    title: str = ''
    content: str = ''
    tags: str = '[]'
    difficulty: int = 1
    answer: str = ''
    paper_question_number: Optional[int] = None
    grade: str = '初一'
    category: str = ''
