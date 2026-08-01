"""组卷模型"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User


class Test(Base):
    """组卷模型"""
    __tablename__ = 'tests'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    question_ids: Mapped[str] = mapped_column(Text, default='[]')  # JSON array
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    author: Mapped[Optional["User"]] = relationship(back_populates="tests")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "question_ids": self.question_ids,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
