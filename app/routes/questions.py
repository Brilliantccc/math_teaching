"""题目管理路由"""

import os
import json
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.models import get_db
from app.constants import TAG_TO_CATEGORY, ALLOWED_IMAGE_EXTENSIONS
from auth import api_login_required

questions_bp = Blueprint('questions', __name__)


@questions_bp.route("/api/questions", methods=["GET"])
@api_login_required
def get_questions():
    """获取题目列表，支持筛选"""
    tag = request.args.get("tag", "")
    keyword = request.args.get("keyword", "")
    difficulty = request.args.get("difficulty", "")
    grade = request.args.get("grade", "")
    category = request.args.get("category", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    where = []
    params = []

    if tag:
        where.append("tags LIKE ?")
        params.append(f'%{tag}%')
    if keyword:
        where.append("(title LIKE ? OR content LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if difficulty:
        where.append("difficulty = ?")
        params.append(int(difficulty))
    if grade:
        where.append("grade = ?")
        params.append(grade)
    if category:
        where.append("category = ?")
        params.append(category)

    where_sql = ""
    if where:
        where_sql = "WHERE " + " AND ".join(where)

    conn = get_db()
    cursor = conn.execute(f"SELECT COUNT(*) FROM questions {where_sql}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * per_page
    cursor = conn.execute(
        f"SELECT * FROM questions {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    )
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "questions": questions,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@questions_bp.route("/api/questions/batch", methods=["GET"])
@api_login_required
def get_questions_batch():
    """批量获取题目（避免前端逐题请求的 N+1 问题）"""
    ids_param = request.args.get("ids", "")
    ids = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
    if not ids:
        return jsonify({"questions": []})

    conn = get_db()
    placeholders = ",".join("?" for _ in ids)
    cursor = conn.execute(f"SELECT * FROM questions WHERE id IN ({placeholders})", ids)
    questions = {row["id"]: dict(row) for row in cursor.fetchall()}
    conn.close()

    # 按请求顺序返回
    ordered = [questions[qid] for qid in ids if qid in questions]
    return jsonify({"questions": ordered})


@questions_bp.route("/api/questions/<int:q_id>", methods=["GET"])
@api_login_required
def get_question(q_id):
    """获取单个题目详情"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM questions WHERE id = ?", (q_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "题目不存在"}), 404
    return jsonify(dict(row))


@questions_bp.route("/api/questions", methods=["POST"])
@api_login_required
def create_question():
    """创建新题目"""
    title = request.form.get("title", "")
    content = request.form.get("content", "")
    tags = request.form.get("tags", "[]")
    difficulty = int(request.form.get("difficulty", 1))
    source = request.form.get("source", "")
    answer = request.form.get("answer", "")
    analysis = request.form.get("analysis", "")
    grade = request.form.get("grade", "初一")
    category = request.form.get("category", "")
    paper_id = request.form.get("paper_id", None)
    paper_q_num = request.form.get("paper_question_number", None)
    image_path = request.form.get("image_path", "")

    # 处理图片上传
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename and f.filename.rsplit(".", 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS:
            filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO questions (title, content, tags, difficulty, source, image_path, answer, analysis, grade, category, paper_id, paper_question_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (title, content, tags, difficulty, source, image_path, answer, analysis, grade, category, paper_id, paper_q_num),
    )
    conn.commit()
    q_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": q_id, "message": "题目已添加"}), 201


@questions_bp.route("/api/questions/<int:q_id>", methods=["PUT"])
@api_login_required
def update_question(q_id):
    """更新题目"""
    data = request.get_json()
    conn = get_db()
    conn.execute(
        "UPDATE questions SET title=?, content=?, tags=?, difficulty=?, source=?, answer=?, analysis=?, grade=?, category=? WHERE id=?",
        (
            data.get("title", ""),
            data.get("content", ""),
            data.get("tags", "[]"),
            int(data.get("difficulty", 1)),
            data.get("source", ""),
            data.get("answer", ""),
            data.get("analysis", ""),
            data.get("grade", "初一"),
            data.get("category", ""),
            q_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "题目已更新"})


@questions_bp.route("/api/questions/<int:q_id>", methods=["DELETE"])
@api_login_required
def delete_question(q_id):
    """删除题目"""
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "题目已删除"})


@questions_bp.route("/api/questions/batch-delete", methods=["POST"])
@api_login_required
def batch_delete_questions():
    """批量删除题目"""
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"error": "请选择要删除的题目"}), 400

    conn = get_db()
    placeholders = ",".join("?" for _ in ids)
    conn.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()

    return jsonify({"message": f"已删除 {len(ids)} 道题目"})


@questions_bp.route("/api/questions/batch-update", methods=["POST"])
@api_login_required
def batch_update_questions():
    """批量更新题目属性"""
    data = request.get_json()
    ids = data.get("ids", [])
    updates = data.get("updates", {})

    if not ids:
        return jsonify({"error": "请选择要更新的题目"}), 400

    if not updates:
        return jsonify({"error": "没有要更新的内容"}), 400

    conn = get_db()
    set_clauses = []
    params = []

    allowed_fields = {"grade", "category", "difficulty", "tags"}
    for field, value in updates.items():
        if field in allowed_fields:
            set_clauses.append(f"{field} = ?")
            params.append(value)

    if not set_clauses:
        return jsonify({"error": "无效的更新字段"}), 400

    placeholders = ",".join("?" for _ in ids)
    sql = f"UPDATE questions SET {', '.join(set_clauses)} WHERE id IN ({placeholders})"
    conn.execute(sql, params + ids)
    conn.commit()
    conn.close()

    return jsonify({"message": f"已更新 {len(ids)} 道题目"})
