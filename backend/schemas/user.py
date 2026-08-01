"""用户相关模型"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=80)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=80)
    password: str = Field(..., min_length=6)
    display_name: str = Field(default='')
    role: str = Field(default='student', pattern='^(student|teacher)$')


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    username: str
    reset_code: str
    new_password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    display_name: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    role: Optional[str] = None
    display_name: Optional[str] = None
    password: Optional[str] = None
