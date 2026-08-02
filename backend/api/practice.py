"""练习路由"""

import json
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.deps import get_db, get_current_user
from backend.core.exceptions import NotFoundException
from backend.models.user import User
from backend.models.question import Question
from backend.models.practice import PracticeSession, WrongQuestion
from backend.schemas.practice import (
    StartPracticeRequest, SubmitAnswerRequest, SubmitAnswerResponse,
    PracticeSessionResponse, RetryRequest, WrongQuestionResponse,
    WrongQuestionListResponse, PracticeStatsResponse,
    TagStats, DifficultyStats, RecentPractice
)

router = APIRouter()


@router.post("/session", response_model=PracticeSessionResponse)
async def start_practice(
    data: StartPracticeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始练习"""
    query = select(Question)
    if data.tag:
        query = query.where(Question.tags.contains(data.tag))
    if data.grade:
        query = query.where(Question.grade == data.grade)

    result = await db.execute(query)
    all_questions = result.scalars().all()

    selected = random.sample(all_questions, min(data.count, len(all_questions)))
    question_ids = [q.id for q in selected]

    return PracticeSessionResponse(question_ids=question_ids, count=len(question_ids))


@router.post("/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    data: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交答案"""
    question = await db.get(Question, data.question_id)
    if not question:
        raise NotFoundException("题目")

    # 从 answer_analysis 中提取答案部分（分隔符前为答案）
    answer_analysis = question.answer_analysis or ""
    if "---解析---" in answer_analysis:
        correct_answer = answer_analysis.split("---解析---")[0].strip()
    else:
        correct_answer = answer_analysis.strip()
    is_correct = 1 if data.answer.strip().lower() == correct_answer.lower() else 0

    # 记录练习
    session = PracticeSession(
        user_id=current_user.id,
        question_id=data.question_id,
        user_answer=data.answer,
        is_correct=is_correct
    )
    db.add(session)

    # 错题处理
    if not is_correct:
        result = await db.execute(
            select(WrongQuestion).where(
                WrongQuestion.user_id == current_user.id,
                WrongQuestion.question_id == data.question_id
            )
        )
        wrong = result.scalar_one_or_none()

        if wrong:
            wrong.wrong_count += 1
            wrong.last_wrong_at = datetime.utcnow()
            wrong.mastered = 0
        else:
            wrong = WrongQuestion(
                user_id=current_user.id,
                question_id=data.question_id,
                wrong_count=1
            )
            db.add(wrong)

    await db.commit()

    return SubmitAnswerResponse(
        is_correct=bool(is_correct),
        answer_analysis=question.answer_analysis or ""
    )


@router.get("/wrong-questions", response_model=WrongQuestionListResponse)
async def get_wrong_questions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    mastered: str = Query(default=''),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的错题本"""
    query = select(WrongQuestion).where(WrongQuestion.user_id == current_user.id)

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
    wrong_list = []
    for item in items:
        q = await db.get(Question, item.question_id)
        data = item.to_dict()
        data["question"] = q.to_dict() if q else None
        wrong_list.append(WrongQuestionResponse(**data))

    return WrongQuestionListResponse(
        wrong_questions=wrong_list,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.post("/wrong-questions/{wq_id}/master")
async def toggle_mastered(
    wq_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记错题为已掌握/未掌握"""
    wq = await db.get(WrongQuestion, wq_id)
    if not wq or wq.user_id != current_user.id:
        raise NotFoundException("记录")

    wq.mastered = 1 if wq.mastered == 0 else 0
    await db.commit()

    return {"message": "已更新", "mastered": wq.mastered}


@router.post("/wrong-questions/retry")
async def retry_wrong_questions(
    data: RetryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取错题本中的题目用于重练"""
    result = await db.execute(
        select(WrongQuestion)
        .where(WrongQuestion.user_id == current_user.id, WrongQuestion.mastered == 0)
        .order_by(WrongQuestion.wrong_count.desc())
        .limit(data.count)
    )
    wrong_questions = result.scalars().all()
    wrong_ids = [wq.question_id for wq in wrong_questions]

    return {"question_ids": wrong_ids, "count": len(wrong_ids)}


@router.get("/stats", response_model=PracticeStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的学习统计"""
    uid = current_user.id

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
        tag_stats_list.append(TagStats(
            tag=tag,
            total=stats["total"],
            correct=stats["correct"],
            accuracy=round(stats["correct"] / stats["total"] * 100, 1)
        ))
    tag_stats_list.sort(key=lambda x: x.total, reverse=True)

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
        diff_stats.append(DifficultyStats(
            difficulty=row.difficulty,
            total=row.total,
            correct=d_correct,
            accuracy=round(d_correct / row.total * 100, 1) if row.total > 0 else 0
        ))

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
        recent_list.append(RecentPractice(
            id=r.id,
            question_id=r.question_id,
            question_title=q.content[:50] if q else "",
            is_correct=r.is_correct,
            created_at=r.created_at.isoformat() if r.created_at else None
        ))

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

    return PracticeStatsResponse(
        total=total,
        correct=correct,
        accuracy=accuracy,
        tag_stats=tag_stats_list,
        difficulty_stats=diff_stats,
        recent=recent_list,
        wrong_total=wrong_total,
        wrong_unmastered=wrong_unmastered,
        streak_days=streak
    )
