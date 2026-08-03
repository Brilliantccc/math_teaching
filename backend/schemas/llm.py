"""LLM相关模型"""

from typing import Optional, List
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """生成解析请求"""
    content: str
    image_descriptions: Optional[List[str]] = None


class AnalyzeResponse(BaseModel):
    """生成解析响应"""
    success: bool
    data: dict


class ExtractResponse(BaseModel):
    """图片识别响应"""
    success: bool
    data: List[dict]


class BatchExtractResponse(BaseModel):
    """批量识别响应"""
    success: bool
    data: List[dict]
    errors: List[dict]


class LLMStatusResponse(BaseModel):
    """LLM状态响应"""
    configured: bool
    model: str
