"""组卷管理路由"""

import os
import json
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app, after_this_request

from app.models import get_db
from pdf_utils import generate_test_pdf
from auth import api_login_required

tests_bp = Blueprint('tests', __name__)


@tests_bp.route("/api/tests", methods=["GET"])
@api_login_required
def get_tests():
    """获取组卷列表"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM tests ORDER BY created_at DESC")
    tests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"tests": tests})


@tests_bp.route("/api/tests", methods=["POST"])
@api_login_required
def create_test():
    """创建组卷"""
    data = request.get_json()
    name = data.get("name", f"试卷_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    question_ids = json.dumps(data.get("question_ids", []), ensure_ascii=False)
    conn = get_db()
    cursor = conn.execute("INSERT INTO tests (name, question_ids) VALUES (?, ?)", (name, question_ids))
    conn.commit()
    test_id = cursor.lastrowid
    conn.close()
    return jsonify({"id": test_id, "message": "试卷已保存"}), 201


@tests_bp.route("/api/tests/<int:t_id>", methods=["GET"])
@api_login_required
def get_test(t_id):
    """获取组卷详情"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM tests WHERE id = ?", (t_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "试卷不存在"}), 404
    test = dict(row)
    q_ids = json.loads(test["question_ids"])
    if q_ids:
        placeholders = ",".join("?" for _ in q_ids)
        cursor = conn.execute(f"SELECT * FROM questions WHERE id IN ({placeholders})", q_ids)
        test["questions"] = [dict(r) for r in cursor.fetchall()]
    else:
        test["questions"] = []
    conn.close()
    return jsonify(test)


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

    where = []
    params = []
    if tags:
        conditions = [f"tags LIKE ?" for _ in tags]
        params.extend([f"%{t}%" for t in tags])
        where.append("(" + " OR ".join(conditions) + ")")
    if difficulties:
        placeholders = ",".join("?" for _ in difficulties)
        where.append(f"difficulty IN ({placeholders})")
        params.extend(difficulties)
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
    cursor = conn.execute(
        f"SELECT id FROM questions {where_sql} ORDER BY RANDOM() LIMIT ?",
        params + [count],
    )
    q_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify({"question_ids": q_ids, "count": len(q_ids)})


@tests_bp.route("/api/tests/<int:t_id>/pdf", methods=["GET"])
@api_login_required
def export_test_pdf(t_id):
    """导出组卷PDF"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM tests WHERE id = ?", (t_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "试卷不存在"}), 404

    test = dict(row)
    q_ids = json.loads(test["question_ids"])

    if not q_ids:
        conn.close()
        return jsonify({"error": "试卷没有题目"}), 400

    placeholders = ",".join("?" for _ in q_ids)
    cursor = conn.execute(f"SELECT * FROM questions WHERE id IN ({placeholders})", q_ids)
    questions = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # 生成PDF
    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"test_{t_id}_{uuid.uuid4().hex}.pdf")
    try:
        generate_test_pdf(questions, output_path, title=test.get("name", "数学试卷"))

        @after_this_request
        def cleanup(response):
            try:
                os.remove(output_path)
            except OSError:
                pass
            return response

        return send_file(output_path, as_attachment=True, download_name=f"{test.get('name', '试卷')}.pdf")
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

    conn = get_db()
    placeholders = ",".join("?" for _ in question_ids)
    cursor = conn.execute(f"SELECT * FROM questions WHERE id IN ({placeholders})", question_ids)
    questions = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # 生成PDF
    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"preview_{uuid.uuid4().hex}.pdf")
    try:
        generate_test_pdf(questions, output_path, title=title)

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
