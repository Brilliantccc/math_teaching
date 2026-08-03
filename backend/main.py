"""FastAPI 应用入口"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.config import settings, validate_config, print_config
from backend.database import init_db
from backend.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 打印配置信息
    print_config()
    # 验证配置
    validate_config()
    # 确保数据目录存在
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    # 启动时初始化数据库
    await init_db()
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="数学题库管理系统 API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vue 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保上传目录存在（StaticFiles 挂载时目录必须存在）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 挂载上传文件目录
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册 API 路由
app.include_router(api_router)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "数学题库管理系统 API", "version": "2.0.0"}


@app.get("/health")
async def health():
    """健康检查 - 返回系统状态"""
    from backend.config import settings
    from datetime import datetime

    # 检查数据库状态
    db_status = "ok"
    try:
        from backend.database import async_session
        async with async_session() as session:
            await session.execute(__import__('sqlalchemy').text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 检查LLM配置
    llm_configured = bool(settings.LLM_API_KEY and settings.LLM_BASE_URL)

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": db_status,
            "llm_configured": llm_configured,
        },
        "config": {
            "app_name": settings.APP_NAME,
            "debug": settings.DEBUG,
        }
    }


@app.exception_handler(404)
async def not_found(request: Request, exc):
    """404 错误处理"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "资源不存在"}
        )
    return JSONResponse(
        status_code=404,
        content={"error": "页面不存在"}
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    """500 错误处理"""
    return JSONResponse(
        status_code=500,
        content={"error": "服务器内部错误"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
