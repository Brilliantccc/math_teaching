"""配置管理 - Pydantic Settings"""

import os
import sys
from pydantic_settings import BaseSettings
from functools import lru_cache


def _default_font_path():
    """根据操作系统返回中文字体默认路径"""
    if sys.platform == 'win32':
        font_dir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
        candidates = [
            os.path.join(font_dir, 'msyh.ttc'),
            os.path.join(font_dir, 'simhei.ttf'),
        ]
    elif sys.platform == 'darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


class Settings(BaseSettings):
    """应用配置"""
    # 基础配置
    APP_NAME: str = "数学题库"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'question_bank.db')}"

    # 文件上传
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50MB

    # JWT
    JWT_EXPIRE_HOURS: int = 720  # 30 天

    # 字体
    FONT_PATH: str = ""

    # LLM
    LLM_MODEL_ID: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_TIMEOUT: int = 120

    # 管理员
    ADMIN_PASSWORD: str = "admin123"

    # 重置密码
    RESET_CODE: str = ""

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        env_file_encoding = "utf-8"

    def model_post_init(self, __context):
        """后处理：设置默认路径"""
        if not self.FONT_PATH:
            self.FONT_PATH = _default_font_path()


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()


settings = get_settings()


def validate_config() -> bool:
    """验证配置是否完整，启动时调用"""
    errors = []
    warnings = []

    # 检查LLM配置
    if not settings.LLM_API_KEY:
        warnings.append("LLM_API_KEY未配置，AI功能可能无法使用")
    if not settings.LLM_BASE_URL:
        warnings.append("LLM_BASE_URL未配置，AI功能可能无法使用")
    if not settings.LLM_MODEL_ID:
        warnings.append("LLM_MODEL_ID未配置，AI功能可能无法使用")

    # 检查管理员密码
    if settings.ADMIN_PASSWORD == "admin123":
        warnings.append("ADMIN_PASSWORD使用默认值，建议修改")

    # 检查密钥
    if settings.SECRET_KEY == "dev-secret-key-change-in-production":
        warnings.append("SECRET_KEY使用默认值，生产环境请修改")

    if errors:
        error_msg = "配置错误:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n[WARNING] 配置警告:")
        for w in warnings:
            print(f"  - {w}")

    return True


def print_config():
    """打印当前配置（隐藏敏感信息）"""
    print(f"应用名称: {settings.APP_NAME}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"LLM API Key: {'已配置' if settings.LLM_API_KEY else '未配置'}")
    print(f"LLM Base URL: {settings.LLM_BASE_URL or '未配置'}")
    print(f"LLM Model: {settings.LLM_MODEL_ID or '未配置'}")
    print(f"管理员密码: {'已配置' if settings.ADMIN_PASSWORD != 'admin123' else '使用默认值'}")
    print(f"字体路径: {settings.FONT_PATH}")
