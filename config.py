import os
import sys
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _default_tesseract_path():
    """根据操作系统返回 Tesseract 默认路径"""
    if sys.platform == 'win32':
        candidates = [
            r'D:\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
    elif sys.platform == 'darwin':
        candidates = [
            '/opt/homebrew/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
    else:
        candidates = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


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


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE = os.path.join(basedir, 'question_bank.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'question_bank.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate limiting
    RATELIMIT_DEFAULT = "60/minute"

    # OCR settings (跨平台：自动检测系统路径，也可通过环境变量覆盖)
    TESSERACT_PATH = os.environ.get('TESSERACT_PATH', _default_tesseract_path())

    # Font settings for PDF generation (跨平台：自动检测系统字体，也可通过环境变量覆盖)
    FONT_PATH = os.environ.get('FONT_PATH', _default_font_path())


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    # 生产环境 SECRET_KEY 必须通过环境变量设置，无默认值
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Rate limiting: 使用 Redis 存储（需安装 redis 依赖）
    # REDIS_URL 格式: redis://[:password@]host[:port][/db]
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_DEFAULT = "30/minute"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE = ':memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
