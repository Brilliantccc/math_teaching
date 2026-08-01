"""题目管理路由 - SQLAlchemy ORM"""

import os
import json
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user

from app.models import db, Question
from app.constants import ALLOWED_IMAGE_EXTENSIONS
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

    query = Question.query

    # 权限过滤：学生只能看公开题目，教师/管理员看所有
    # 目前不做限制，所有人都能看到所有题目

    if tag:
        query = query.filter(Question.tags.contains(tag))
    if keyword:
        query = query.filter(
            db.or_(
                Question.title.contains(keyword),
                Question.content.contains(keyword)
            )
        )
    if difficulty:
        query = query.filter(Question.difficulty == int(difficulty))
    if grade:
        query = query.filter(Question.grade == grade)
    if category:
        query = query.filter(Question.category == category)

    total = query.count()
    questions = query.order_by(Question.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    return jsonify({
        "questions": [q.to_dict() for q in questions],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    })


@questions_bp.route("/api/questions/batch", methods=["GET"])
@api_login_required
def get_questions_batch():
    """批量获取题目"""
    ids_param = request.args.get("ids", "")
    ids = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
    if not ids:
        return jsonify({"questions": []})

    questions = Question.query.filter(Question.id.in_(ids)).all()
    # 按请求顺序返回
    q_map = {q.id: q for q in questions}
    ordered = [q_map[qid].to_dict() for qid in ids if qid in q_map]
    return jsonify({"questions": ordered})


@questions_bp.route("/api/questions/<int:q_id>", methods=["GET"])
@api_login_required
def get_question(q_id):
    """获取单个题目详情"""
    question = Question.query.get(q_id)
    if not question:
        return jsonify({"error": "题目不存在"}), 404
    return jsonify(question.to_dict())


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

    question = Question(
        title=title, content=content, tags=tags, difficulty=difficulty,
        source=source, image_path=image_path, answer=answer, analysis=analysis,
        grade=grade, category=category,
        paper_id=int(paper_id) if paper_id else None,
        paper_question_number=int(paper_q_num) if paper_q_num else None,
        created_by=current_user.id
    )
    db.session.add(question)
    db.session.commit()

    return jsonify({"id": question.id, "message": "题目已添加"}), 201


@questions_bp.route("/api/questions/<int:q_id>", methods=["PUT"])
@api_login_required
def update_question(q_id):
    """更新题目"""
    question = Question.query.get(q_id)
    if not question:
        return jsonify({"error": "题目不存在"}), 404

    data = request.get_json()
    question.title = data.get("title", question.title)
    question.content = data.get("content", question.content)
    question.tags = data.get("tags", question.tags)
    question.difficulty = int(data.get("difficulty", question.difficulty))
    question.source = data.get("source", question.source)
    question.answer = data.get("answer", question.answer)
    question.analysis = data.get("analysis", question.analysis)
    question.grade = data.get("grade", question.grade)
    question.category = data.get("category", question.category)

    db.session.commit()
    return jsonify({"message": "题目已更新"})


@questions_bp.route("/api/questions/<int:q_id>", methods=["DELETE"])
@api_login_required
def delete_question(q_id):
    """删除题目"""
    question = Question.query.get(q_id)
    if not question:
        return jsonify({"error": "题目不存在"}), 404

    db.session.delete(question)
    db.session.commit()
    return jsonify({"message": "题目已删除"})


@questions_bp.route("/api/questions/batch-delete", methods=["POST"])
@api_login_required
def batch_delete_questions():
    """批量删除题目"""
    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"error": "请选择要删除的题目"}), 400

    Question.query.filter(Question.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
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

    allowed_fields = {"grade", "category", "difficulty", "tags"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}

    if not filtered:
        return jsonify({"error": "无效的更新字段"}), 400

    Question.query.filter(Question.id.in_(ids)).update(filtered, synchronize_session=False)
    db.session.commit()
    return jsonify({"message": f"已更新 {len(ids)} 道题目"})
