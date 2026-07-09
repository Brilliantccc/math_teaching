"""组卷管理路由 - SQLAlchemy ORM"""

import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app, after_this_request
from flask_login import current_user
import random

from app.models import db, Test, Question
from pdf_utils import generate_test_pdf
from auth import api_login_required

tests_bp = Blueprint('tests', __name__)


@tests_bp.route("/api/tests", methods=["GET"])
@api_login_required
def get_tests():
    """获取组卷列表"""
    tests = Test.query.order_by(Test.created_at.desc()).all()
    return jsonify({"tests": [t.to_dict() for t in tests]})


@tests_bp.route("/api/tests", methods=["POST"])
@api_login_required
def create_test():
    """创建组卷"""
    data = request.get_json()
    name = data.get("name", f"试卷_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    question_ids = json.dumps(data.get("question_ids", []), ensure_ascii=False)

    test = Test(name=name, question_ids=question_ids, created_by=current_user.id)
    db.session.add(test)
    db.session.commit()

    return jsonify({"id": test.id, "message": "试卷已保存"}), 201


@tests_bp.route("/api/tests/<int:t_id>", methods=["GET"])
@api_login_required
def get_test(t_id):
    """获取组卷详情"""
    test = Test.query.get(t_id)
    if not test:
        return jsonify({"error": "试卷不存在"}), 404

    data = test.to_dict()
    q_ids = json.loads(test.question_ids)
    if q_ids:
        questions = Question.query.filter(Question.id.in_(q_ids)).all()
        q_map = {q.id: q for q in questions}
        data["questions"] = [q_map[qid].to_dict() for qid in q_ids if qid in q_map]
    else:
        data["questions"] = []
    return jsonify(data)


@tests_bp.route("/api/tests/auto", methods=["POST"])
@api_login_required
def auto_generate_test():
    """自动生成组卷"""
    data = request.get_json()
    tags = data.get("tags", [])
    count = int(data.get("count", 10))
    difficulties = data.get("difficulties", [1, 2, 3])
    grade = data.get("grade", "")
    category = data.get("category", "")

    query = Question.query

    if tags:
        tag_conditions = [Question.tags.contains(t) for t in tags]
        query = query.filter(db.or_(*tag_conditions))
    if difficulties:
        query = query.filter(Question.difficulty.in_(difficulties))
    if grade:
        query = query.filter(Question.grade == grade)
    if category:
        query = query.filter(Question.category == category)

    all_questions = query.all()
    # 随机抽样
    selected = random.sample(all_questions, min(count, len(all_questions)))
    q_ids = [q.id for q in selected]

    return jsonify({"question_ids": q_ids, "count": len(q_ids)})


@tests_bp.route("/api/tests/<int:t_id>/pdf", methods=["GET"])
@api_login_required
def export_test_pdf(t_id):
    """导出组卷PDF"""
    test = Test.query.get(t_id)
    if not test:
        return jsonify({"error": "试卷不存在"}), 404

    q_ids = json.loads(test.question_ids)
    if not q_ids:
        return jsonify({"error": "试卷没有题目"}), 400

    questions = Question.query.filter(Question.id.in_(q_ids)).all()
    questions_data = [q.to_dict() for q in questions]

    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"test_{t_id}_{uuid.uuid4().hex}.pdf")
    try:
        generate_test_pdf(questions_data, output_path, title=test.name or "数学试卷")

        @after_this_request
        def cleanup(response):
            try:
                os.remove(output_path)
            except OSError:
                pass
            return response

        return send_file(output_path, as_attachment=True, download_name=f"{test.name or '试卷'}.pdf")
    except Exception as e:
        return jsonify({"error": f"生成PDF失败: {str(e)}"}), 500


@tests_bp.route("/api/tests/preview/pdf", methods=["POST"])
@api_login_required
def export_preview_pdf():
    """预览导出PDF（不保存）"""
    data = request.get_json()
    question_ids = data.get("question_ids", [])
    title = data.get("title", "数学试卷")

    if not question_ids:
        return jsonify({"error": "没有题目"}), 400

    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    questions_data = [q.to_dict() for q in questions]

    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"preview_{uuid.uuid4().hex}.pdf")
    try:
        generate_test_pdf(questions_data, output_path, title=title)

        @after_this_request
        def cleanup(response):
            try:
                os.remove(output_path)
            except OSError:
                pass
            return response

        return send_file(output_path, as_attachment=True, download_name=f"{title}.pdf")
    except Exception as e:
        return jsonify({"error": f"生成PDF失败: {str(e)}"}), 500
