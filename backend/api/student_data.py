"""学生数据路由"""

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.deps import get_db, require_teacher
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.question import Question
from backend.models.practice import PracticeSession, WrongQuestion

router = APIRouter()


@router.get("")
async def get_students(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """获取所有学生列表"""
    query = select(User).where(User.role == 'student')

    if keyword:
        query = query.where(
            User.username.contains(keyword) | User.display_name.contains(keyword)
        )

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    students = result.scalars().all()

    # 为每个学生附加统计信息
    result_list = []
    for s in students:
        data = s.to_dict()

        # 练习统计
        data['practice_count'] = (await db.execute(
            select(func.count()).where(PracticeSession.user_id == s.id)
        )).scalar() or 0

        data['correct_count'] = (await db.execute(
            select(func.count()).where(PracticeSession.user_id == s.id, PracticeSession.is_correct == 1)
        )).scalar() or 0

        total_practice = data['practice_count']
        data['accuracy'] = round(data['correct_count'] / total_practice * 100, 1) if total_practice > 0 else 0

        # 错题统计
        data['wrong_count'] = (await db.execute(
            select(func.count()).where(WrongQuestion.user_id == s.id)
        )).scalar() or 0

        data['wrong_unmastered'] = (await db.execute(
            select(func.count()).where(WrongQuestion.user_id == s.id, WrongQuestion.mastered == 0)
        )).scalar() or 0

        # 最后练习时间
        result = await db.execute(
            select(PracticeSession)
            .where(PracticeSession.user_id == s.id)
            .order_by(PracticeSession.created_at.desc())
            .limit(1)
        )
        last_practice = result.scalar_one_or_none()
        data['last_practice'] = last_practice.created_at.isoformat() if last_practice and last_practice.created_at else None

        result_list.append(data)

    return {
        "students": result_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{student_id}/stats")
async def get_student_stats(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """获取指定学生的练习统计"""
    student = await db.get(User, student_id)
    if not student or student.role != 'student':
        raise NotFoundException("学生")

    uid = student.id

    # 总体统计
    total = (await db.execute(
        select(func.count()).where(PracticeSession.user_id == uid)
    )).scalar() or 0

    correct = (await db.execute(
        select(func.count()).where(PracticeSession.user_id == uid, PracticeSession.is_correct == 1)
    )).scalar() or 0

    accuracy = round(correct / total * 100, 1) if total > 0 else 0

    # 按知识点（标签）统计
    tag_detail = {}
    result = await db.execute(
        select(PracticeSession).where(PracticeSession.user_id == uid)
    )
    sessions = result.scalars().all()

    for s in sessions:
        q = await db.get(Question, s.question_id)
        if not q:
            continue
        try:
            tags = json.loads(q.tags)
        except Exception:
            tags = []
        for tag in tags:
            if tag not in tag_detail:
                tag_detail[tag] = {"total": 0, "correct": 0}
            tag_detail[tag]["total"] += 1
            if s.is_correct:
                tag_detail[tag]["correct"] += 1

    tag_stats_list = []
    for tag, stats in tag_detail.items():
        tag_stats_list.append({
            "tag": tag,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(stats["correct"] / stats["total"] * 100, 1)
        })
    tag_stats_list.sort(key=lambda x: x["total"], reverse=True)

    # 按难度统计
    result = await db.execute(
        select(
            Question.difficulty,
            func.count(PracticeSession.id).label('total'),
            func.sum(PracticeSession.is_correct).label('correct')
        )
        .join(Question, PracticeSession.question_id == Question.id)
        .where(PracticeSession.user_id == uid)
        .group_by(Question.difficulty)
    )
    difficulty_stats = result.all()

    diff_stats = []
    for row in difficulty_stats:
        d_correct = row.correct or 0
        diff_stats.append({
            "difficulty": row.difficulty,
            "total": row.total,
            "correct": d_correct,
            "accuracy": round(d_correct / row.total * 100, 1) if row.total > 0 else 0
        })

    # 最近练习记录
    result = await db.execute(
        select(PracticeSession)
        .where(PracticeSession.user_id == uid)
        .order_by(PracticeSession.created_at.desc())
        .limit(10)
    )
    recent_sessions = result.scalars().all()

    recent_list = []
    for r in recent_sessions:
        q = await db.get(Question, r.question_id)
        recent_list.append({
            "id": r.id,
            "question_id": r.question_id,
            "question_title": q.title if q else "",
            "is_correct": r.is_correct,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    # 错题统计
    wrong_total = (await db.execute(
        select(func.count()).where(WrongQuestion.user_id == uid)
    )).scalar() or 0

    wrong_unmastered = (await db.execute(
        select(func.count()).where(WrongQuestion.user_id == uid, WrongQuestion.mastered == 0)
    )).scalar() or 0

    # 连续练习天数
    today = datetime.utcnow().date()
    streak = 0
    for i in range(365):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        has_practice = (await db.execute(
            select(PracticeSession).where(
                PracticeSession.user_id == uid,
                PracticeSession.created_at.between(day_start, day_end)
            )
        )).first()
        if has_practice:
            streak += 1
        else:
            break

    return {
        "student": student.to_dict(),
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "tag_stats": tag_stats_list,
        "difficulty_stats": diff_stats,
        "recent": recent_list,
        "wrong_total": wrong_total,
        "wrong_unmastered": wrong_unmastered,
        "streak_days": streak,
    }


@router.get("/{student_id}/wrong-questions")
async def get_student_wrong_questions(
    student_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    mastered: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """获取指定学生的错题本"""
    student = await db.get(User, student_id)
    if not student or student.role != 'student':
        raise NotFoundException("学生")

    query = select(WrongQuestion).where(WrongQuestion.user_id == student_id)

    if mastered != '':
        query = query.where(WrongQuestion.mastered == int(mastered))

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页查询
    query = query.order_by(WrongQuestion.last_wrong_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    # 获取关联题目
    result_list = []
    for item in items:
        q = await db.get(Question, item.question_id)
        data = item.to_dict()
        data["question"] = q.to_dict() if q else None
        result_list.append(data)

    return {
        "wrong_questions": result_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/class/stats")
async def get_class_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """获取班级整体统计"""
    # 学生总数
    total_students = (await db.execute(
        select(func.count()).where(User.role == 'student')
    )).scalar() or 0

    # 今日活跃学生
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_active = (await db.execute(
        select(func.count(func.distinct(PracticeSession.user_id)))
        .where(PracticeSession.created_at.between(today_start, today_end))
    )).scalar() or 0

    # 总练习次数
    total_practice = (await db.execute(
        select(func.count()).select_from(PracticeSession)
    )).scalar() or 0

    # 平均正确率
    total_correct = (await db.execute(
        select(func.count()).where(PracticeSession.is_correct == 1)
    )).scalar() or 0
    avg_accuracy = round(total_correct / total_practice * 100, 1) if total_practice > 0 else 0

    # 最常见的错题
    result = await db.execute(
        select(
            WrongQuestion.question_id,
            func.count(WrongQuestion.id).label('wrong_count')
        )
        .group_by(WrongQuestion.question_id)
        .order_by(func.count(WrongQuestion.id).desc())
        .limit(10)
    )
    most_wrong_questions = result.all()

    wrong_list = []
    for item in most_wrong_questions:
        q = await db.get(Question, item.question_id)
        if q:
            wrong_list.append({
                "question_id": item.question_id,
                "question_title": q.title,
                "wrong_count": item.wrong_count,
            })

    # 最近7天练习趋势
    trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = (await db.execute(
            select(func.count()).where(
                PracticeSession.created_at.between(day_start, day_end)
            )
        )).scalar() or 0
        trend.append({
            "date": day.isoformat(),
            "count": count,
        })

    return {
        "total_students": total_students,
        "today_active": today_active,
        "total_practice": total_practice,
        "avg_accuracy": avg_accuracy,
        "most_wrong_questions": wrong_list,
        "trend": trend,
    }
