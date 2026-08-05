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
    content: Mapped[str] = mapped_column(Text, default='')
    tags: Mapped[str] = mapped_column(Text, default='[]')  # JSON array
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(Text, default='')
    image_path: Mapped[str] = mapped_column(Text, default='')
    images: Mapped[str] = mapped_column(Text, default='[]')  # JSON array: 多图片URL列表
    answer_analysis: Mapped[str] = mapped_column(Text, default='')  # 答案与解析合并在
    grade: Mapped[str] = mapped_column(Text, default='初一上')
    question_type: Mapped[str] = mapped_column(Text, default='')  # 题型：单项选择/多项选择/填空题/解答题/判断题/计算题
    paper_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('papers.id'), nullable=True)
    paper_question_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 显示序号，按年级分组

    # 关系
    author: Mapped[Optional["User"]] = relationship(back_populates="questions")
    paper: Mapped[Optional["Paper"]] = relationship(back_populates="questions")

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "source": self.source,
            "image_path": self.image_path,
            "images": self.images,
            "answer_analysis": self.answer_analysis,
            "grade": self.grade,
            "question_type": self.question_type,
            "paper_id": self.paper_id,
            "paper_question_number": self.paper_question_number,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "display_order": self.display_order,
        }
