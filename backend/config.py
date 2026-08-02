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
