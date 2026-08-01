"""用户模型"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.question import Question
    from backend.models.paper import Paper
    from backend.models.test import Test
    from backend.models.practice import PracticeSession, WrongQuestion


class User(Base):
    """用户模型"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='student')
    display_name: Mapped[str] = mapped_column(String(100), default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    questions: Mapped[List["Question"]] = relationship(back_populates="author", lazy="dynamic")
    papers: Mapped[List["Paper"]] = relationship(back_populates="author", lazy="dynamic")
    tests: Mapped[List["Test"]] = relationship(back_populates="author", lazy="dynamic")
    practice_sessions: Mapped[List["PracticeSession"]] = relationship(back_populates="user", lazy="dynamic")
    wrong_questions: Mapped[List["WrongQuestion"]] = relationship(back_populates="user", lazy="dynamic")

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def is_teacher(self) -> bool:
        return self.role in ('teacher', 'admin')

    def is_student(self) -> bool:
        return self.role == 'student'

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
