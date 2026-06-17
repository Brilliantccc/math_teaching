"""练习模式路由"""

import json
from flask import Blueprint, request, jsonify

from app.models import get_db
from app.constants import TAG_TO_CATEGORY
from auth import api_login_required

practice_bp = Blueprint('practice', __name__)


@practice_bp.route("/api/practice/session", methods=["POST"])
@api_login_required
def start_practice():
    """开始练习会话"""
    data = request.get_json()
    count = int(data.get("count", 5))
    tag = data.get("tag", "")
    grade = data.get("grade", "")

    where = []
    params = []
    if tag:
        where.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if grade:
        where.append("grade = ?")
        params.append(grade)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    conn = get_db()
    cursor = conn.execute(
        f"SELECT id FROM questions {where_sql} ORDER BY RANDOM() LIMIT ?",
        params + [count],
    )
    q_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify({"question_ids": q_ids})


@practice_bp.route("/api/practice/submit", methods=["POST"])
@api_login_required
def submit_answer():
    """提交答案"""
    data = request.get_json()
    q_id = data.get("question_id")
    user_answer = data.get("answer", "")

    conn = get_db()
    cursor = conn.execute("SELECT answer FROM questions WHERE id = ?", (q_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "题目不存在"}), 404
    correct_answer = row[0]
    is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
    conn.execute(
        "INSERT INTO practice_sessions (question_id, user_answer, is_correct) VALUES (?, ?, ?)",
        (q_id, user_answer, 1 if is_correct else 0),
    )
    conn.commit()
    conn.close()

    return jsonify({"is_correct": is_correct, "correct_answer": correct_answer})


@practice_bp.route("/api/practice/wrong-questions", methods=["GET"])
@api_login_required
def get_wrong_questions():
    """获取错题本（答错过的题目，去重）"""
    tag = request.args.get("tag", "")
    grade = request.args.get("grade", "")
    difficulty = request.args.get("difficulty", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))

    conn = get_db()

    # 查询答错过的题目（去重，取最后一次答错记录）
    where = ["ps.is_correct = 0"]
    params = []
    if tag:
        where.append("q.tags LIKE ?")
        params.append(f"%{tag}%")
    if grade:
        where.append("q.grade = ?")
        params.append(grade)
    if difficulty:
        where.append("q.difficulty = ?")
        params.append(int(difficulty))

    where_sql = " AND ".join(where)

    # 统计总数
    count_sql = f"""
        SELECT COUNT(DISTINCT q.id)
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.id
        WHERE {where_sql}
    """
    total = conn.execute(count_sql, params).fetchone()[0]

    # 获取错题列表（每个题目取最后一次答错记录）
    offset = (page - 1) * per_page
    query_sql = f"""
        SELECT q.*, ps.user_answer, ps.created_at as last_wrong_time
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.id
        WHERE {where_sql}
        GROUP BY q.id
        ORDER BY MAX(ps.created_at) DESC
        LIMIT ? OFFSET ?
    """
    cursor = conn.execute(query_sql, params + [per_page, offset])
    wrong_questions = [dict(row) for row in cursor.fetchall()]

    # 统计每个题目的答错次数
    for wq in wrong_questions:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM practice_sessions WHERE question_id = ? AND is_correct = 0",
            (wq["id"],)
        )
        wq["wrong_count"] = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "questions": wrong_questions,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 0,
    })


@practice_bp.route("/api/practice/stats", methods=["GET"])
@api_login_required
def get_practice_stats():
    """获取练习统计数据"""
    conn = get_db()

    # 总练习次数和正确数
    cursor = conn.execute("SELECT COUNT(*) FROM practice_sessions")
    total = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(*) FROM practice_sessions WHERE is_correct = 1")
    correct = cursor.fetchone()[0]

    # 按知识点统计
    cursor = conn.execute("""
        SELECT q.tags, ps.is_correct
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.id
    """)

    tag_stats = {}
    for row in cursor.fetchall():
        try:
            tags = json.loads(row[0])
            is_correct = row[1]
            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"total": 0, "correct": 0}
                tag_stats[tag]["total"] += 1
                if is_correct:
                    tag_stats[tag]["correct"] += 1
        except:
            pass

    # 按难度统计
    cursor = conn.execute("""
        SELECT q.difficulty, ps.is_correct
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.id
    """)

    diff_stats = {}
    for row in cursor.fetchall():
        diff = row[0]
        is_correct = row[1]
        if diff not in diff_stats:
            diff_stats[diff] = {"total": 0, "correct": 0}
        diff_stats[diff]["total"] += 1
        if is_correct:
            diff_stats[diff]["correct"] += 1

    # 最近10次练习记录
    cursor = conn.execute("""
        SELECT q.id, q.title, q.tags, ps.user_answer, ps.is_correct, ps.created_at
        FROM practice_sessions ps
        JOIN questions q ON ps.question_id = q.id
        ORDER BY ps.created_at DESC
        LIMIT 10
    """)

    recent = []
    for row in cursor.fetchall():
        recent.append({
            "question_id": row[0],
            "title": row[1],
            "tags": row[2],
            "user_answer": row[3],
            "is_correct": row[4],
            "created_at": row[5]
        })

    conn.close()

    return jsonify({
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        "tag_stats": tag_stats,
        "diff_stats": diff_stats,
        "recent": recent
    })
