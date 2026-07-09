import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


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

    # OCR settings
    TESSERACT_PATH = os.environ.get('TESSERACT_PATH', r'D:\Tesseract-OCR\tesseract.exe')

    # Font settings (for PDF generation)
    FONT_PATH = os.environ.get('FONT_PATH', r'C:\Windows\Fonts\msyh.ttc')


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
