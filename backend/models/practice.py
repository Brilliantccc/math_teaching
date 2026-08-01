"""练习模型"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.question import Question


class PracticeSession(Base):
    """练习记录模型"""
    __tablename__ = 'practice_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey('questions.id'), nullable=False)
    user_answer: Mapped[str] = mapped_column(Text, default='')
    is_correct: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    user: Mapped["User"] = relationship(back_populates="practice_sessions")
    question: Mapped["Question"] = relationship()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "user_answer": self.user_answer,
            "is_correct": self.is_correct,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WrongQuestion(Base):
    """错题本模型"""
    __tablename__ = 'wrong_questions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey('questions.id'), nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    mastered: Mapped[int] = mapped_column(Integer, default=0)  # 0=未掌握, 1=已掌握
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    user: Mapped["User"] = relationship(back_populates="wrong_questions")
    question: Mapped["Question"] = relationship()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "wrong_count": self.wrong_count,
            "last_wrong_at": self.last_wrong_at.isoformat() if self.last_wrong_at else None,
            "mastered": self.mastered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
