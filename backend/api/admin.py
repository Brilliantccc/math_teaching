"""管理功能路由"""

import os
import json
import uuid
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

router = APIRouter()

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}


# ─── 常量数据 ─────────────────────────────────────────────

GRADES = ["初一", "初二", "初三", "高一", "高二", "高三"]

CATEGORIES = {
    "数与式": ["有理数加减", "有理数乘除", "整式", "因式分解", "分式"],
    "代数方程": ["一元一次方程", "一元二次方程", "二元一次方程组", "不等式"],
    "函数": ["一次函数", "反比例函数", "二次函数"],
    "几何": ["三角形", "四边形", "圆", "相似", "全等"],
    "统计与概率": ["统计", "概率"],
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
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新用户信息"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException("用户")

    if "role" in data and data["role"] in ("student", "teacher", "admin"):
        user.role = data["role"]
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "password" in data and len(data["password"]) >= 6:
        user.password_hash = get_password_hash(data["password"])

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


# ─── OCR ─────────────────────────────────────────────

@router.post("/ocr")
async def ocr_recognize(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """OCR文字识别"""
    if not image.filename:
        raise HTTPException(status_code=400, detail="无效的文件")

    ext = image.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")

    filename = f"ocr_{uuid.uuid4().hex}_{image.filename}"
    upload_path = os.path.join(settings.UPLOAD_DIR, filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)

    with open(upload_path, "wb") as f:
        content = await image.read()
        f.write(content)

    try:
        from backend.utils.ocr import recognize_question
        result = recognize_question(upload_path)
        return result
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)


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
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """从JSON导入题目"""
    if not data or "questions" not in data:
        raise HTTPException(status_code=400, detail="无效的JSON格式")

    questions = data["questions"]
    if not questions:
        raise HTTPException(status_code=400, detail="没有要导入的题目")

    imported = 0
    skipped = 0

    for q in questions:
        # 去重：标题+内容
        result = await db.execute(
            select(Question).where(
                Question.title == q.get("title", ""),
                Question.content == q.get("content", "")
            )
        )
        if result.scalar_one_or_none():
            skipped += 1
            continue

        question = Question(
            title=q.get("title", ""),
            content=q.get("content", ""),
            tags=q.get("tags", "[]"),
            difficulty=q.get("difficulty", 1),
            source=q.get("source", ""),
            image_path=q.get("image_path", ""),
            answer=q.get("answer", ""),
            analysis=q.get("analysis", ""),
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
