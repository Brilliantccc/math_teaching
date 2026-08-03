"""管理功能路由"""

import os
import json
import tempfile
import shutil
import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.deps import get_db, get_current_user, require_teacher, require_admin
from backend.core.exceptions import NotFoundException
from backend.core.security import get_password_hash
from backend.models.user import User
from backend.models.question import Question
from backend.models.paper import Paper
from backend.config import settings
from backend.schemas.admin import (
    UpdateUserRequest, ImportQuestionsRequest, BatchUpdateCategoriesRequest,
    StudentListResponse, StudentStatsResponse, StudentWrongQuestionsResponse,
    ClassStatsResponse, StandardCategoriesResponse, CurrentCategoriesResponse,
    NormalizeCategoriesResponse
)

router = APIRouter()


# ─── 常量数据 ─────────────────────────────────────────────

GRADES = ["初一", "初二", "初三", "高一", "高二", "高三"]

# 标准题目分类
CATEGORIES = {
    "代数": ["整式", "分式", "二次根式", "方程", "不等式"],
    "函数": ["一次函数", "反比例函数", "二次函数", "函数图像"],
    "几何": ["三角形", "四边形", "圆", "相似", "全等", "勾股定理"],
    "统计与概率": ["统计", "概率", "数据分析"],
    "数与计算": ["有理数", "实数", "计算"],
    "图形与变换": ["平移", "旋转", "对称"],
    "综合": ["综合题", "应用题", "探究"],
}

ALL_TAGS = []
GRADE_TAGS = {}
for grade in GRADES:
    GRADE_TAGS[grade] = []
for cat, tags in CATEGORIES.items():
    ALL_TAGS.extend(tags)
    for grade in GRADES:
        GRADE_TAGS[grade].extend(tags)


# ─── 用户管理 ─────────────────────────────────────────────

@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """获取所有用户列表"""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return {"users": [u.to_dict() for u in users]}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新用户信息"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("用户")

    if data.role is not None:
        user.role = data.role
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.password is not None:
        user.password_hash = get_password_hash(data.password)

    await db.commit()
    return {"message": "用户已更新", "user": user.to_dict()}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """删除用户"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("用户")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除管理员账户")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    await db.delete(user)
    await db.commit()
    return {"message": "用户已删除"}


# ─── 元数据 ─────────────────────────────────────────────

@router.get("/grades")
async def get_grades():
    """获取年级列表"""
    return {"grades": GRADES}


@router.get("/categories")
async def get_categories():
    """获取分类数据"""
    return {"categories": CATEGORIES}


@router.get("/tags")
async def get_tags(
    grade: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有标签"""
    tag_set = set()

    if grade:
        if grade in GRADE_TAGS:
            tag_set.update(GRADE_TAGS[grade])
        result = await db.execute(
            select(Question).where(Question.grade == grade)
        )
        questions = result.scalars().all()
    else:
        tag_set.update(ALL_TAGS)
        result = await db.execute(select(Question))
        questions = result.scalars().all()

    for q in questions:
        try:
            tag_set.update(json.loads(q.tags))
        except (json.JSONDecodeError, TypeError):
            pass

    return {"tags": sorted(tag_set)}


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统计数据"""
    from sqlalchemy import func

    stats = {"total": (await db.execute(select(func.count()).select_from(Question))).scalar() or 0}
    for grade in GRADES:
        stats[grade] = (await db.execute(
            select(func.count()).where(Question.grade == grade)
        )).scalar() or 0
    stats["papers"] = (await db.execute(select(func.count()).select_from(Paper))).scalar() or 0

    return stats


# ─── 备份 ─────────────────────────────────────────────

@router.get("/backup/export")
async def export_backup(
    current_user: User = Depends(get_current_user)
):
    """导出数据库备份"""
    db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="数据库不存在")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        db_path,
        media_type="application/octet-stream",
        filename=f"math_question_bank_backup_{timestamp}.db"
    )


@router.post("/backup/import")
async def import_backup(
    backup_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """导入数据库备份"""
    if not backup_file.filename or not backup_file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="请上传 .db 格式的备份文件")

    content = await backup_file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="备份文件大小不能超过100MB")

    if not content.startswith(b'SQLite format 3'):
        raise HTTPException(status_code=400, detail="不是有效的SQLite数据库文件")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, 'backup.db')

    try:
        with open(temp_path, 'wb') as f:
            f.write(content)

        conn = sqlite3.connect(temp_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        required_tables = {'questions', 'papers', 'tests', 'practice_sessions'}
        missing_tables = required_tables - tables
        if missing_tables:
            raise HTTPException(
                status_code=400,
                detail=f"备份文件缺少必要的表: {', '.join(missing_tables)}"
            )

        db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        if os.path.exists(db_path):
            backup_path = db_path + ".bak"
            shutil.copy2(db_path, backup_path)

        shutil.move(temp_path, db_path)
        return {"message": "数据库已恢复，请刷新页面"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


# ─── 题目导入导出 ───────────────────────────────────────

@router.get("/questions/export")
async def export_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出所有题目为JSON"""
    result = await db.execute(
        select(Question).order_by(Question.id)
    )
    questions = result.scalars().all()

    return {
        "version": "2.0",
        "count": len(questions),
        "questions": [q.to_dict() for q in questions]
    }


@router.post("/questions/import")
async def import_questions(
    data: ImportQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """从JSON导入题目"""
    if not data.questions:
        raise HTTPException(status_code=400, detail="没有要导入的题目")

    imported = 0
    skipped = 0

    for q in data.questions:
        # 去重：内容
        if q.get("content"):
            result = await db.execute(
                select(Question).where(Question.content == q.get("content", ""))
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

        question = Question(
            content=q.get("content", ""),
            tags=q.get("tags", "[]"),
            difficulty=q.get("difficulty", 1),
            source=q.get("source", ""),
            image_path=q.get("image_path", ""),
            answer_analysis=q.get("answer_analysis", ""),
            grade=q.get("grade", "初一"),
            category=q.get("category", ""),
            paper_id=q.get("paper_id"),
            paper_question_number=q.get("paper_question_number"),
            created_by=current_user.id
        )
        db.add(question)
        imported += 1

    await db.commit()

    return {
        "message": f"导入完成：成功 {imported} 题，跳过 {skipped} 题",
        "imported": imported,
        "skipped": skipped
    }


# ─── 题目分类标准化 ─────────────────────────────────────────

@router.get("/categories/standard")
async def get_standard_categories(
    current_user: User = Depends(require_teacher)
):
    """获取标准题目分类列表"""
    from backend.models.category import STANDARD_CATEGORIES, get_all_standard_categories

    return {
        "categories": get_all_standard_categories(),
        "details": STANDARD_CATEGORIES
    }


@router.get("/categories/current")
async def get_current_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """获取数据库中当前使用的所有分类"""
    from sqlalchemy import func

    result = await db.execute(
        select(
            Question.category,
            func.count(Question.id).label('count')
        )
        .where(Question.category != '')
        .group_by(Question.category)
        .order_by(func.count(Question.id).desc())
    )

    categories = [
        {"name": row[0], "count": row[1]}
        for row in result.all()
    ]

    return {"categories": categories}


@router.post("/categories/normalize")
async def normalize_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """将所有题目的分类标准化为标准分类"""
    from backend.models.category import normalize_category

    # 获取所有题目
    result = await db.execute(select(Question))
    questions = result.scalars().all()

    updated = 0
    unchanged = 0
    changes = []

    for q in questions:
        if not q.category:
            continue

        normalized = normalize_category(q.category)
        if normalized != q.category:
            old_category = q.category
            q.category = normalized
            updated += 1
            changes.append({
                "id": q.id,
                "old": old_category,
                "new": normalized
            })
        else:
            unchanged += 1

    await db.commit()

    return {
        "message": f"标准化完成：更新 {updated} 题，未改变 {unchanged} 题",
        "updated": updated,
        "unchanged": unchanged,
        "changes": changes[:100]  # 只返回前100条变更记录
    }


@router.put("/categories/batch-update")
async def batch_update_categories(
    data: BatchUpdateCategoriesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """批量更新题目分类"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要更新的题目")
    if not data.category:
        raise HTTPException(status_code=400, detail="请指定目标分类")

    result = await db.execute(
        select(Question).where(Question.id.in_(data.ids))
    )
    questions = result.scalars().all()

    for q in questions:
        q.category = data.category

    await db.commit()

    return {"message": f"已更新 {len(questions)} 道题目的分类为 '{data.category}'"}
