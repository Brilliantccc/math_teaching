"""题目模型"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.paper import Paper


class Question(Base):
    """题目模型"""
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, default='')
    content: Mapped[str] = mapped_column(Text, default='')
    tags: Mapped[str] = mapped_column(Text, default='[]')  # JSON array
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(Text, default='')
    image_path: Mapped[str] = mapped_column(Text, default='')
    answer: Mapped[str] = mapped_column(Text, default='')
    analysis: Mapped[str] = mapped_column(Text, default='')
    grade: Mapped[str] = mapped_column(Text, default='初一')
    category: Mapped[str] = mapped_column(Text, default='')
    paper_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('papers.id'), nullable=True)
    paper_question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    author: Mapped[Optional["User"]] = relationship(back_populates="questions")
    paper: Mapped[Optional["Paper"]] = relationship(back_populates="questions")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "source": self.source,
            "image_path": self.image_path,
            "answer": self.answer,
            "analysis": self.analysis,
            "grade": self.grade,
            "category": self.category,
            "paper_id": self.paper_id,
            "paper_question_number": self.paper_question_number,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
