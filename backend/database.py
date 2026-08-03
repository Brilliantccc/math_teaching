"""数据库配置 - SQLAlchemy Async"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}  # SQLite 需要
)

# 创建异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """模型基类"""
    pass


async def init_db():
    """初始化数据库"""
    # 导入所有模型以确保它们被注册
    from backend.models import user, question, paper, test, practice

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        # 添加缺失的字段（兼容旧数据库）
        try:
            await conn.execute(
                __import__('sqlalchemy').text(
                    "ALTER TABLE tests ADD COLUMN question_scores TEXT DEFAULT '{}'"
                )
            )
        except Exception:
            # 列已存在，忽略错误
            pass
        # 添加images字段到questions表
        try:
            await conn.execute(
                __import__('sqlalchemy').text(
                    "ALTER TABLE questions ADD COLUMN images TEXT DEFAULT '[]'"
                )
            )
        except Exception:
            # 列已存在，忽略错误
            pass

    # 创建默认管理员
    await _ensure_admin_user()


async def _ensure_admin_user():
    """确保管理员用户存在"""
    from backend.models.user import User
    from backend.core.security import get_password_hash

    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == 'admin')
        )
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username='admin',
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                role='admin',
                display_name='管理员'
            )
            session.add(admin)
            await session.commit()
        else:
            # 确保密码与配置同步
            from backend.core.security import verify_password
            if not verify_password(settings.ADMIN_PASSWORD, admin.password_hash):
                admin.password_hash = get_password_hash(settings.ADMIN_PASSWORD)
                await session.commit()
