"""试卷模型"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User
    from backend.models.question import Question


class Paper(Base):
    """试卷模型"""
    __tablename__ = 'papers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    grade: Mapped[str] = mapped_column(Text, default='初一上')
    image_path: Mapped[str] = mapped_column(Text, default='')
    pdf_path: Mapped[str] = mapped_column(Text, default='')
    answer_pdf_path: Mapped[str] = mapped_column(Text, default='')
    source: Mapped[str] = mapped_column(Text, default='')
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    author: Mapped[Optional["User"]] = relationship(back_populates="papers")
    questions: Mapped[List["Question"]] = relationship(back_populates="paper", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "grade": self.grade,
            "image_path": self.image_path,
            "pdf_path": self.pdf_path,
            "answer_pdf_path": self.answer_pdf_path,
            "source": self.source,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "questions_count": self.questions.count() if hasattr(self.questions, 'count') else len(list(self.questions)),
        }
