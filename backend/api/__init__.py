"""API路由包"""

from fastapi import APIRouter

from backend.api.auth import router as auth_router
from backend.api.questions import router as questions_router
from backend.api.papers import router as papers_router
from backend.api.tests import router as tests_router
from backend.api.practice import router as practice_router
from backend.api.admin import router as admin_router
from backend.api.metadata import router as metadata_router
from backend.api.student_data import router as student_data_router
from backend.api.llm import router as llm_router

api_router = APIRouter(prefix="/api")

# 无需认证的元数据路由（放在最前面）
api_router.include_router(metadata_router, tags=["元数据"])

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(questions_router, prefix="/questions", tags=["题目"])
api_router.include_router(papers_router, prefix="/papers", tags=["试卷"])
api_router.include_router(tests_router, prefix="/tests", tags=["组卷"])
api_router.include_router(practice_router, prefix="/practice", tags=["练习"])
api_router.include_router(student_data_router, prefix="/students", tags=["学生数据"])
api_router.include_router(llm_router, prefix="/llm", tags=["LLM"])
# admin路由放在最后
api_router.include_router(admin_router, prefix="", tags=["管理"])
