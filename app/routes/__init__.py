"""路由蓝图包"""

from app.routes.questions import questions_bp
from app.routes.papers import papers_bp
from app.routes.tests import tests_bp
from app.routes.practice import practice_bp
from app.routes.admin import admin_bp

__all__ = ['questions_bp', 'papers_bp', 'tests_bp', 'practice_bp', 'admin_bp']
