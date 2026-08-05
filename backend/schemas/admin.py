"""管理功能相关模型"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    role: Optional[str] = Field(default=None, pattern='^(student|teacher|admin)$')
    display_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)


class ImportQuestionsRequest(BaseModel):
    """导入题目请求"""
    questions: List[Dict]


class BatchUpdateCategoriesRequest(BaseModel):
    """批量更新分类请求"""
    ids: List[int]


class ImportBackupResponse(BaseModel):
    """导入备份响应"""
    message: str


class ExportQuestionsResponse(BaseModel):
    """导出题目响应"""
    version: str
    count: int
    questions: List[Dict]


class StandardCategoriesResponse(BaseModel):
    """标准分类响应"""
    categories: List[str]
    details: Dict[str, List[str]]


class CurrentCategoriesResponse(BaseModel):
    """当前分类响应"""
    categories: List[Dict[str, int]]


class NormalizeCategoriesResponse(BaseModel):
    """标准化分类响应"""
    message: str
    updated: int
    unchanged: int
    changes: List[Dict]


class StudentListResponse(BaseModel):
    """学生列表响应"""
    students: List[Dict]
    total: int
    page: int
    per_page: int
    pages: int


class StudentStatsResponse(BaseModel):
    """学生统计响应"""
    student: Dict
    total: int
    correct: int
    accuracy: float
    tag_stats: List[Dict]
    difficulty_stats: List[Dict]
    recent: List[Dict]
    wrong_total: int
    wrong_unmastered: int
    streak_days: int


class StudentWrongQuestionsResponse(BaseModel):
    """学生错题响应"""
    wrong_questions: List[Dict]
    total: int
    page: int
    per_page: int
    pages: int


class ClassStatsResponse(BaseModel):
    """班级统计响应"""
    total_students: int
    today_active: int
    total_practice: int
    avg_accuracy: float
    most_wrong_questions: List[Dict]
    trend: List[Dict]
