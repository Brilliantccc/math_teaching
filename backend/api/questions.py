"""题目管理路由"""

import os
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
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


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有已使用的分类"""
    result = await db.execute(
        select(Question.category)
        .where(Question.category != '')
        .distinct()
        .order_by(Question.category)
    )
    categories = [row[0] for row in result.all()]
    return {"categories": categories}


@router.get("/question-types")
async def get_question_types(
    grade: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有题型及其题目数量（支持按年级筛选，多个年级用逗号分隔）"""
    query = select(
        Question.question_type,
        func.count(Question.id).label('count')
    ).where(Question.question_type != '')

    if grade and grade != '全部':
        grade_list = [g.strip() for g in grade.split(',') if g.strip()]
        if grade_list:
            query = query.where(Question.grade.in_(grade_list))

    query = query.group_by(Question.question_type)
    result = await db.execute(query)
    types = [{"type": row[0], "count": row[1]} for row in result.all()]
    return {"question_types": types}


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
        # 支持逗号分隔的多选年级（如 "初一,初二,初三"）
        grade_list = [g.strip() for g in grade.split(',') if g.strip()]
        if len(grade_list) == 1:
            query = query.where(Question.grade == grade_list[0])
        elif len(grade_list) > 1:
            query = query.where(Question.grade.in_(grade_list))
    if category:
        query = query.where(Question.category == category)

    # 获取总数
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询 - 按序号从小到大排列
    query = query.order_by(Question.display_order.asc())
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
    question_type: str = Form(default=''),
    paper_id: Optional[int] = Form(default=None),
    paper_question_number: Optional[int] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    images: Optional[List[UploadFile]] = File(default=None),
    existing_images: str = Form(default='[]'),  # 已有的图片路径（JSON数组）
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """创建新题目"""
    import json
    print(f"[DB] Creating question with answer_analysis: {answer_analysis[:200] if answer_analysis else 'N/A'}")
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
    images_list = []

    # 解析已有的图片路径（AI裁剪后的图片）
    try:
        existing_images_list = json.loads(existing_images) if existing_images else []
        if existing_images_list:
            images_list.extend(existing_images_list)
            if not image_path and existing_images_list:
                image_path = existing_images_list[0]
    except:
        pass

    # 处理单张图片上传（兼容旧版本）
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
            images_list.append(image_path)

    # 处理多图片上传
    if images:
        for img in images:
            if img and img.filename:
                ext = img.filename.rsplit(".", 1)[-1].lower()
                if ext in ALLOWED_IMAGE_EXTENSIONS:
                    filename = f"{uuid.uuid4().hex}_{img.filename}"
                    upload_path = os.path.join(settings.UPLOAD_DIR, filename)
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    with open(upload_path, "wb") as f:
                        content_bytes = await img.read()
                        f.write(content_bytes)
                    img_path = f"uploads/{filename}"
                    images_list.append(img_path)
                    # 如果没有单张图片，使用第一张作为image_path
                    if not image_path:
                        image_path = img_path

    # 获取当前年级下最大的display_order
    max_order_result = await db.execute(
        select(func.max(Question.display_order))
        .where(Question.grade == grade)
    )
    max_order = max_order_result.scalar() or 0
    next_order = max_order + 1

    question = Question(
        content=content, tags=tags, difficulty=difficulty,
        source=source, image_path=image_path, images=json.dumps(images_list, ensure_ascii=False),
        answer_analysis=answer_analysis,
        grade=grade, category=category, question_type=question_type,
        paper_id=paper_id,
        paper_question_number=paper_question_number,
        created_by=current_user.id,
        display_order=next_order
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
            question_type=item.question_type,
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
    content: str = Form(default=None),
    tags: str = Form(default=None),
    difficulty: int = Form(default=None),
    source: str = Form(default=None),
    answer_analysis: str = Form(default=None),
    grade: str = Form(default=None),
    category: str = Form(default=None),
    question_type: str = Form(default=None),
    existing_images: str = Form(default='[]'),
    images: Optional[List[UploadFile]] = File(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """更新题目"""
    question = await db.get(Question, q_id)
    if not question:
        raise NotFoundException("题目")

    # 更新基本字段
    if content is not None: question.content = content
    if tags is not None: question.tags = tags
    if difficulty is not None: question.difficulty = difficulty
    if source is not None: question.source = source
    if answer_analysis is not None: question.answer_analysis = answer_analysis
    if grade is not None: question.grade = grade
    if category is not None: question.category = category
    if question_type is not None: question.question_type = question_type

    # 处理图片
    import json
    images_list = json.loads(existing_images) if existing_images else []
    image_path = images_list[0] if images_list else ""

    # 处理新上传的图片
    if images:
        for img in images:
            if img and img.filename:
                ext = img.filename.rsplit(".", 1)[-1].lower()
                if ext in ALLOWED_IMAGE_EXTENSIONS:
                    filename = f"{uuid.uuid4().hex}_{img.filename}"
                    upload_path = os.path.join(settings.UPLOAD_DIR, filename)
                    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                    with open(upload_path, "wb") as f:
                        content_bytes = await img.read()
                        f.write(content_bytes)
                    img_path = f"uploads/{filename}"
                    images_list.append(img_path)
                    if not image_path:
                        image_path = img_path

    question.image_path = image_path
    question.images = json.dumps(images_list, ensure_ascii=False)

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

    grade = question.grade
    await db.delete(question)
    await db.commit()

    # 重新排序该年级下的所有题目
    await _reorder_questions_by_grade(db, grade)

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

    # 收集受影响的年级
    affected_grades = set()
    for q in questions:
        affected_grades.add(q.grade)
        await db.delete(q)

    await db.commit()

    # 重新排序受影响年级下的所有题目
    for grade in affected_grades:
        await _reorder_questions_by_grade(db, grade)

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


async def _reorder_questions_by_grade(db: AsyncSession, grade: str):
    """重新排序指定年级下的所有题目，按创建时间排序"""
    # 获取该年级下所有题目，按创建时间排序
    result = await db.execute(
        select(Question)
        .where(Question.grade == grade)
        .order_by(Question.created_at)
    )
    questions = result.scalars().all()

    # 重新设置display_order
    for idx, q in enumerate(questions, 1):
        q.display_order = idx

    await db.commit()
