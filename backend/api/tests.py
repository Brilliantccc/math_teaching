"""组卷管理路由"""

import os
import json
import uuid
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from backend.core.deps import get_db, get_current_user
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.test import Test
from backend.models.question import Question
from backend.schemas.test import (
    TestCreate, TestResponse, TestListResponse,
    AutoGenerateRequest, PreviewPdfRequest
)
from backend.config import settings

router = APIRouter()


@router.get("", response_model=TestListResponse)
async def get_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组卷列表"""
    result = await db.execute(
        select(Test).order_by(Test.created_at.desc())
    )
    tests = result.scalars().all()

    return TestListResponse(
        tests=[TestResponse(**t.to_dict()) for t in tests]
    )


@router.post("", response_model=dict)
async def create_test(
    data: TestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建组卷"""
    name = data.name or f"试卷_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    question_ids = json.dumps(data.question_ids, ensure_ascii=False)

    # 处理每道题的分值
    question_scores = {}
    if data.question_scores:
        question_scores = data.question_scores
    else:
        # 使用统一分值
        for qid in data.question_ids:
            question_scores[qid] = data.score_per_question

    test = Test(
        name=name,
        question_ids=question_ids,
        score_per_question=data.score_per_question,
        question_scores=json.dumps(question_scores, ensure_ascii=False),
        created_by=current_user.id
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    return {"id": test.id, "message": "试卷已保存"}


@router.delete("/{t_id}")
async def delete_test(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除组卷"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")
    await db.delete(test)
    await db.commit()
    return {"message": "已删除"}


@router.get("/{t_id}", response_model=TestResponse)
async def get_test(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取组卷详情"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")

    data = test.to_dict()
    q_ids = json.loads(test.question_ids)

    if q_ids:
        result = await db.execute(
            select(Question).where(Question.id.in_(q_ids))
        )
        questions = result.scalars().all()
        q_map = {q.id: q for q in questions}
        data["questions"] = [q_map[qid].to_dict() for qid in q_ids if qid in q_map]
    else:
        data["questions"] = []

    return TestResponse(**data)


@router.post("/auto", response_model=dict)
async def auto_generate_test(
    data: AutoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动生成组卷"""
    query = select(Question)

    if data.tags:
        tag_conditions = [Question.tags.contains(t) for t in data.tags]
        query = query.where(or_(*tag_conditions))
    if data.difficulties:
        query = query.where(Question.difficulty.in_(data.difficulties))
    if data.grade:
        query = query.where(Question.grade == data.grade)
    if data.category:
        query = query.where(Question.category == data.category)

    result = await db.execute(query)
    all_questions = result.scalars().all()

    # 随机抽样
    selected = random.sample(all_questions, min(data.count, len(all_questions)))
    q_ids = [q.id for q in selected]

    return {"question_ids": q_ids, "count": len(q_ids)}


@router.get("/{t_id}/pdf")
async def export_test_pdf(
    t_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出组卷PDF"""
    test = await db.get(Test, t_id)
    if not test:
        raise NotFoundException("试卷")

    q_ids = json.loads(test.question_ids)
    if not q_ids:
        raise HTTPException(status_code=400, detail="试卷没有题目")

    result = await db.execute(
        select(Question).where(Question.id.in_(q_ids))
    )
    questions = result.scalars().all()
    questions_data = [q.to_dict() for q in questions]

    # 解析question_scores
    question_scores = {}
    if test.question_scores:
        try:
            question_scores = json.loads(test.question_scores)
            # 将字符串key转换为int
            question_scores = {int(k): v for k, v in question_scores.items()}
        except:
            pass

    # 生成PDF（需要导入pdf_utils）
    from backend.utils.pdf_utils import generate_test_pdf
    output_path = os.path.join(settings.UPLOAD_DIR, f"test_{t_id}_{uuid.uuid4().hex}.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        generate_test_pdf(
            questions_data, output_path,
            title=test.name or "数学试卷",
            question_scores=question_scores if question_scores else None
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{test.name or '试卷'}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")


@router.post("/preview/pdf")
async def export_preview_pdf(
    data: PreviewPdfRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览导出PDF"""
    if not data.question_ids:
        raise HTTPException(status_code=400, detail="没有题目")

    result = await db.execute(
        select(Question).where(Question.id.in_(data.question_ids))
    )
    questions = result.scalars().all()
    questions_data = [q.to_dict() for q in questions]

    from backend.utils.pdf_utils import generate_test_pdf
    output_path = os.path.join(settings.UPLOAD_DIR, f"preview_{uuid.uuid4().hex}.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        generate_test_pdf(
            questions_data, output_path,
            title=data.title,
            question_scores=data.question_scores
        )
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"{data.title}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")
