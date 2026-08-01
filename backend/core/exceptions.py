"""自定义异常模块"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用基础异常"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """资源不存在"""
    def __init__(self, resource: str = "资源"):
        super().__init__(detail=f"{resource}不存在", status_code=status.HTTP_404_NOT_FOUND)


class PermissionDeniedException(AppException):
    """权限不足"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class BadRequestException(AppException):
    """请求错误"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(AppException):
    """未授权"""
    def __init__(self, detail: str = "请先登录"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)
