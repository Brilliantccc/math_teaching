"""练习路由 - SQLAlchemy ORM，多用户支持"""

import json
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user
from sqlalchemy import func

from app.models import db, Question, PracticeSession, WrongQuestion
from auth import api_login_required

practice_bp = Blueprint('practice', __name__)


@practice_bp.route("/api/practice/session", methods=["POST"])
@api_login_required
def start_practice():
    """开始练习：返回随机题目 ID 列表"""
    data = request.get_json()
    tag = data.get("tag", "")
    grade = data.get("grade", "")
    count = int(data.get("count", 10))

    query = Question.query
    if tag:
        query = query.filter(Question.tags.contains(tag))
    if grade:
        query = query.filter(Question.grade == grade)

    all_questions = query.all()
    selected = random.sample(all_questions, min(count, len(all_questions)))
    question_ids = [q.id for q in selected]

    return jsonify({"question_ids": question_ids, "count": len(question_ids)})


@practice_bp.route("/api/practice/submit", methods=["POST"])
@api_login_required
def submit_answer():
    """提交答案，自动记录错题"""
    data = request.get_json()
    question_id = data.get("question_id")
    user_answer = data.get("answer", "").strip()

    if not question_id:
        return jsonify({"error": "缺少题目 ID"}), 400

    question = Question.query.get(question_id)
    if not question:
        return jsonify({"error": "题目不存在"}), 404

    correct_answer = (question.answer or "").strip()
    is_correct = 1 if user_answer.lower() == correct_answer.lower() else 0

    # 记录练习
    session = PracticeSession(
        user_id=current_user.id,
        question_id=question_id,
        user_answer=user_answer,
        is_correct=is_correct
    )
    db.session.add(session)

    # 错题处理
    if not is_correct:
        wrong = WrongQuestion.query.filter_by(
            user_id=current_user.id, question_id=question_id
        ).first()

        if wrong:
            wrong.wrong_count += 1
            wrong.last_wrong_at = datetime.utcnow()
            wrong.mastered = 0
        else:
            wrong = WrongQuestion(
                user_id=current_user.id,
                question_id=question_id,
                wrong_count=1
            )
            db.session.add(wrong)

    db.session.commit()

    return jsonify({
        "is_correct": bool(is_correct),
        "correct_answer": correct_answer,
        "analysis": question.analysis or ""
    })


# ─── 错题本 ─────────────────────────────────────────────

@practice_bp.route("/api/practice/wrong-questions", methods=["GET"])
@api_login_required
def get_wrong_questions():
    """获取当前用户的错题本"""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    mastered = request.args.get("mastered", "")

    query = WrongQuestion.query.filter_by(user_id=current_user.id)

    if mastered != "":
        query = query.filter(WrongQuestion.mastered == int(mastered))

    total = query.count()
    items = query.order_by(WrongQuestion.last_wrong_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    result = []
    for item in items:
        q = Question.query.get(item.question_id)
        data = item.to_dict()
        data["question"] = q.to_dict() if q else None
        result.append(data)

    return jsonify({
        "wrong_questions": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@practice_bp.route("/api/practice/wrong-questions/<int:wq_id>/master", methods=["POST"])
@api_login_required
def toggle_mastered(wq_id):
    """标记错题为已掌握/未掌握"""
    wq = WrongQuestion.query.get(wq_id)
    if not wq or wq.user_id != current_user.id:
        return jsonify({"error": "记录不存在"}), 404

    wq.mastered = 1 if wq.mastered == 0 else 0
    db.session.commit()
    return jsonify({"message": "已更新", "mastered": wq.mastered})


@practice_bp.route("/api/practice/wrong-questions/retry", methods=["POST"])
@api_login_required
def retry_wrong_questions():
    """获取错题本中的题目用于重练"""
    count = int(request.get_json().get("count", 10))

    wrong_ids = [
        wq.question_id for wq in
        WrongQuestion.query.filter_by(user_id=current_user.id, mastered=0)
        .order_by(WrongQuestion.wrong_count.desc())
        .limit(count)
        .all()
    ]

    return jsonify({"question_ids": wrong_ids, "count": len(wrong_ids)})


# ─── 学习统计 ───────────────────────────────────────────

@practice_bp.route("/api/practice/stats", methods=["GET"])
@api_login_required
def get_stats():
    """获取当前用户的学习统计"""
    uid = current_user.id

    # 总体统计
    total = PracticeSession.query.filter_by(user_id=uid).count()
    correct = PracticeSession.query.filter_by(user_id=uid, is_correct=1).count()
    accuracy = round(correct / total * 100, 1) if total > 0 else 0

    # 按知识点（标签）统计
    tag_detail = {}
    sessions = PracticeSession.query.filter_by(user_id=uid).all()
    for s in sessions:
        q = Question.query.get(s.question_id)
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
    difficulty_stats = db.session.query(
        Question.difficulty,
        func.count(PracticeSession.id).label('total'),
        func.sum(PracticeSession.is_correct).label('correct')
    ).join(Question, PracticeSession.question_id == Question.id) \
     .filter(PracticeSession.user_id == uid) \
     .group_by(Question.difficulty).all()

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
    recent = PracticeSession.query.filter_by(user_id=uid) \
        .order_by(PracticeSession.created_at.desc()) \
        .limit(10).all()

    recent_list = []
    for r in recent:
        q = Question.query.get(r.question_id)
        recent_list.append({
            "id": r.id,
            "question_id": r.question_id,
            "question_title": q.title if q else "",
            "is_correct": r.is_correct,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    # 错题统计
    wrong_total = WrongQuestion.query.filter_by(user_id=uid).count()
    wrong_unmastered = WrongQuestion.query.filter_by(user_id=uid, mastered=0).count()

    # 连续练习天数
    today = datetime.utcnow().date()
    streak = 0
    for i in range(365):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        has_practice = PracticeSession.query.filter(
            PracticeSession.user_id == uid,
            PracticeSession.created_at.between(day_start, day_end)
        ).first()
        if has_practice:
            streak += 1
        else:
            break

    return jsonify({
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "tag_stats": tag_stats_list,
        "difficulty_stats": diff_stats,
        "recent": recent_list,
        "wrong_total": wrong_total,
        "wrong_unmastered": wrong_unmastered,
        "streak_days": streak,
    })
