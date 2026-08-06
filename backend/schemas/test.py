"""组卷相关模型"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TestCreate(BaseModel):
    """创建组卷请求"""
    name: Optional[str] = None
    question_ids: List[int] = []
    score_per_question: int = 10
    question_scores: Optional[Dict[int, int]] = None  # 每道题的分值：{question_id: score}


class TestResponse(BaseModel):
    """组卷响应"""
    id: int
    name: str
    question_ids: str
    score_per_question: int = 10
    question_scores: Optional[str] = None
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
    question_type: str = ''  # 单一题型筛选
    question_type_counts: Dict[str, int] = {}  # 按题型配置数量 {"单项选择": 5, "多项选择": 2, "填空题": 3, "解答题": 2}
    # 按题型+难度配置数量 {"单项选择": {1: 3, 2: 2, 3: 0}, ...}
    question_type_difficulty_counts: Dict[str, Dict[int, int]] = {}


class PreviewPdfRequest(BaseModel):
    """预览导出PDF请求"""
    question_ids: List[int]
    title: str = '数学试卷'
    question_scores: Optional[Dict[int, int]] = None


class PDFExportRequest(BaseModel):
    """PDF导出请求（支持模板和样式配置）"""
    question_ids: List[int]
    title: str = '数学试卷'
    template: str = 'standard'  # 模板类型：standard/concise/detailed/professional
    question_scores: Optional[Dict[int, int]] = None
    style_overrides: Optional[Dict[str, Any]] = None  # 样式覆盖配置


class PDFStyleOverride(BaseModel):
    """PDF样式覆盖配置"""
    title_font_size: Optional[int] = None
    title_color: Optional[str] = None
    question_font_size: Optional[int] = None
    show_answer: Optional[bool] = None
    show_analysis: Optional[bool] = None
    show_header: Optional[bool] = None
    header_text: Optional[str] = None
    show_footer: Optional[bool] = None
    footer_text: Optional[str] = None
    group_by_type: Optional[bool] = None
    answer_space_mode: Optional[str] = None
