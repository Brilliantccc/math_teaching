"""题目管理路由"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from backend.core.deps import get_db, get_current_user, require_teacher
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.question import Question
from backend.schemas.question import (
    QuestionUpdate, QuestionResponse, QuestionListResponse,
    BatchCreateRequest, BatchDeleteRequest, BatchUpdateRequest
)
from backend.config import settings

router = APIRouter()

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}


@router.get("", response_model=QuestionListResponse)
async def get_questions(
    tag: str = Query(default=''),
    keyword: str = Query(default=''),
    difficulty: Optional[int] = Query(default=None),
    grade: str = Query(default=''),
    category: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取题目列表"""
    query = select(Question)

    if tag:
        query = query.where(Question.tags.contains(tag))
    if keyword:
        query = query.where(Question.content.contains(keyword))
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if grade:
        query = query.where(Question.grade == grade)
    if category:
        query = query.where(Question.category == category)

    # 获取总数
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询
    query = query.order_by(Question.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    questions = result.scalars().all()

    return QuestionListResponse(
        questions=[QuestionResponse(**q.to_dict()) for q in questions],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.post("", response_model=dict)
async def create_question(
    content: str = Form(default=''),
    tags: str = Form(default='[]'),
    difficulty: int = Form(default=1),
    source: str = Form(default=''),
    answer_analysis: str = Form(default=''),
    grade: str = Form(default='初一'),
    category: str = Form(default=''),
    paper_id: Optional[int] = Form(default=None),
    paper_question_number: Optional[int] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """创建新题目"""
    # 检查是否已存在相同内容的题目
    if content and content.strip():
        existing = await db.execute(
            select(Question).where(Question.content == content.strip())
        )
        existing_question = existing.scalar_one_or_none()
        if existing_question:
            return {
                "id": existing_question.id,
                "message": "已存在相同题目",
                "duplicate": True
            }

    image_path = ""

    # 处理图片上传
    if image and image.filename:
        ext = image.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            filename = f"{uuid.uuid4().hex}_{image.filename}"
            upload_path = os.path.join(settings.UPLOAD_DIR, filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            with open(upload_path, "wb") as f:
                content_bytes = await image.read()
                f.write(content_bytes)
            image_path = f"uploads/{filename}"

    question = Question(
        content=content, tags=tags, difficulty=difficulty,
        source=source, image_path=image_path, answer_analysis=answer_analysis,
        grade=grade, category=category,
        paper_id=paper_id,
        paper_question_number=paper_question_number,
        created_by=current_user.id
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    return {"id": question.id, "message": "题目已添加"}


@router.get("/batch")
async def get_questions_batch(
    ids: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量获取题目"""
    if not ids:
        return {"questions": []}

    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    if not id_list:
        return {"questions": []}

    result = await db.execute(
        select(Question).where(Question.id.in_(id_list))
    )
    questions = result.scalars().all()

    # 按请求顺序返回
    q_map = {q.id: q for q in questions}
    ordered = [q_map[qid].to_dict() for qid in id_list if qid in q_map]

    return {"questions": ordered}


@router.post("/batch-create", response_model=dict)
async def batch_create_questions(
    data: BatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """批量创建题目"""
    if not data.questions:
        raise HTTPException(status_code=400, detail="没有要创建的题目")

    created_ids = []
    skipped_count = 0

    for item in data.questions:
        # 检查是否已存在相同内容的题目
        if item.content and item.content.strip():
            existing = await db.execute(
                select(Question).where(Question.content == item.content.strip())
            )
            if existing.scalar_one_or_none():
                skipped_count += 1
                continue

        question = Question(
            content=item.content,
            answer_analysis=item.answer_analysis,
            grade=item.grade,
            category=item.category,
            difficulty=item.difficulty,
            image_path=item.image_path,
            created_by=current_user.id
        )
        db.add(question)
        await db.flush()  # 获取 ID
        created_ids.append(question.id)

    await db.commit()

    message = f"已创建 {len(created_ids)} 道题目"
    if skipped_count > 0:
        message += f"，跳过 {skipped_count} 道重复题目"

    return {"message": message, "ids": created_ids, "skipped": skipped_count}


@router.get("/check-duplicates", response_model=dict)
async def check_duplicates(
    db: AsyncSession = Depends(get_db)
):
    """检查重复题目数量（无需认证）"""
    from sqlalchemy import func

    # 统计重复题目
    subquery = (
        select(
            Question.content,
            func.count(Question.id).label('count'),
            func.min(Question.id).label('keep_id')
        )
        .where(Question.content != '')
        .group_by(Question.content)
        .having(func.count(Question.id) > 1)
    )

    result = await db.execute(subquery)
    duplicates = result.all()

    total_duplicates = sum(count - 1 for _, count, _ in duplicates)

    return {
        "duplicate_groups": len(duplicates),
        "total_duplicates": total_duplicates,
        "message": f"发现 {len(duplicates)} 组重复题目，共 {total_duplicates} 道可清理"
    }


@router.post("/deduplicate", response_model=dict)
async def deduplicate_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """清理重复题目（保留最早创建的）"""
    from sqlalchemy import func

    # 找出所有重复的 content（保留每组中 id 最小的）
    subquery = (
        select(
            Question.content,
            func.min(Question.id).label('min_id')
        )
        .where(Question.content != '')
        .group_by(Question.content)
        .having(func.count(Question.id) > 1)
    )

    result = await db.execute(subquery)
    duplicates = result.all()

    deleted_count = 0
    for content, min_id in duplicates:
        # 删除同 content 中 id 较大的记录
        delete_result = await db.execute(
            select(Question).where(
                Question.content == content,
                Question.id != min_id
            )
        )
        questions_to_delete = delete_result.scalars().all()
        for q in questions_to_delete:
            await db.delete(q)
            deleted_count += 1

    await db.commit()

    return {
        "message": f"已清理 {deleted_count} 道重复题目",
        "deleted_count": deleted_count,
        "duplicate_groups": len(duplicates)
    }


@router.get("/{q_id}", response_model=QuestionResponse)
async def get_question(
    q_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个题目详情"""
    question = await db.get(Question, q_id)
    if not question:
        raise NotFoundException("题目")
    return QuestionResponse(**question.to_dict())


@router.put("/{q_id}", response_model=dict)
async def update_question(
    q_id: int,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """更新题目"""
    question = await db.get(Question, q_id)
    if not question:
        raise NotFoundException("题目")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)

    await db.commit()
    return {"message": "题目已更新"}


@router.delete("/{q_id}", response_model=dict)
async def delete_question(
    q_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """删除题目"""
    question = await db.get(Question, q_id)
    if not question:
        raise NotFoundException("题目")

    await db.delete(question)
    await db.commit()
    return {"message": "题目已删除"}


@router.post("/batch-delete", response_model=dict)
async def batch_delete_questions(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """批量删除题目"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的题目")

    result = await db.execute(
        select(Question).where(Question.id.in_(data.ids))
    )
    questions = result.scalars().all()

    for q in questions:
        await db.delete(q)

    await db.commit()
    return {"message": f"已删除 {len(data.ids)} 道题目"}


@router.post("/batch-update", response_model=dict)
async def batch_update_questions(
    data: BatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """批量更新题目属性"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要更新的题目")
    if not data.updates:
        raise HTTPException(status_code=400, detail="没有要更新的内容")

    allowed_fields = {"grade", "category", "difficulty", "tags"}
    filtered = {k: v for k, v in data.updates.items() if k in allowed_fields}

    if not filtered:
        raise HTTPException(status_code=400, detail="无效的更新字段")

    result = await db.execute(
        select(Question).where(Question.id.in_(data.ids))
    )
    questions = result.scalars().all()

    for q in questions:
        for key, value in filtered.items():
            setattr(q, key, value)

    await db.commit()
    return {"message": f"已更新 {len(data.ids)} 道题目"}
