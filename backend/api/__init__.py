"""API路由包"""

from fastapi import APIRouter

from backend.api.auth import router as auth_router
from backend.api.questions import router as questions_router
from backend.api.papers import router as papers_router
from backend.api.tests import router as tests_router
from backend.api.practice import router as practice_router
from backend.api.admin import router as admin_router
from backend.api.student_data import router as student_data_router
from backend.api.llm import router as llm_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(questions_router, prefix="/questions", tags=["题目"])
api_router.include_router(papers_router, prefix="/papers", tags=["试卷"])
api_router.include_router(tests_router, prefix="/tests", tags=["组卷"])
api_router.include_router(practice_router, prefix="/practice", tags=["练习"])
api_router.include_router(admin_router, prefix="", tags=["管理"])
api_router.include_router(student_data_router, prefix="/students", tags=["学生数据"])
api_router.include_router(llm_router, prefix="/llm", tags=["LLM"])
