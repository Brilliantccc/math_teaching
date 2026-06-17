"""试卷管理路由"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from app.models import get_db
from app.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_PDF_EXTENSIONS
from auth import api_login_required

papers_bp = Blueprint('papers', __name__)


@papers_bp.route("/api/papers", methods=["GET"])
@api_login_required
def get_papers():
    """获取试卷列表"""
    grade = request.args.get("grade", "")
    conn = get_db()
    if grade:
        cursor = conn.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM questions q WHERE q.paper_id = p.id) as questions_count "
            "FROM papers p WHERE p.grade = ? ORDER BY p.created_at DESC", (grade,))
    else:
        cursor = conn.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM questions q WHERE q.paper_id = p.id) as questions_count "
            "FROM papers p ORDER BY p.created_at DESC")
    papers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"papers": papers})


@papers_bp.route("/api/papers", methods=["POST"])
@api_login_required
def create_paper():
    """创建新试卷"""
    name = request.form.get("name", "")
    grade = request.form.get("grade", "初一")
    source = request.form.get("source", "")

    image_path = ""
    pdf_path = ""

    # 处理PDF上传
    if "pdf" in request.files:
        f = request.files["pdf"]
        if f and f.filename and f.filename.rsplit(".", 1)[-1].lower() in ALLOWED_PDF_EXTENSIONS:
            filename = secure_filename(f"paper_{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            pdf_path = f"uploads/{filename}"

    # 处理图片上传（向后兼容）
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename and f.filename.rsplit(".", 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS:
            filename = secure_filename(f"paper_{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

    if not pdf_path and not image_path:
        return jsonify({"error": "请上传试卷文件（PDF或图片）"}), 400

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO papers (name, grade, image_path, pdf_path, source) VALUES (?, ?, ?, ?, ?)",
        (name, grade, image_path, pdf_path, source),
    )
    conn.commit()
    paper_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": paper_id, "pdf_path": pdf_path, "image_path": image_path, "message": "试卷已上传"}), 201


@papers_bp.route("/api/papers/<int:p_id>", methods=["GET"])
@api_login_required
def get_paper(p_id):
    """获取试卷详情"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (p_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "试卷不存在"}), 404
    paper = dict(row)
    cursor = conn.execute("SELECT * FROM questions WHERE paper_id = ? ORDER BY paper_question_number", (p_id,))
    paper["questions"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(paper)


@papers_bp.route("/api/papers/<int:p_id>", methods=["DELETE"])
@api_login_required
def delete_paper(p_id):
    """删除试卷"""
    conn = get_db()
    conn.execute("DELETE FROM papers WHERE id = ?", (p_id,))
    conn.execute("UPDATE questions SET paper_id = NULL, paper_question_number = NULL WHERE paper_id = ?", (p_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "试卷已删除"})


@papers_bp.route("/api/papers/<int:p_id>/download", methods=["GET"])
@api_login_required
def download_paper(p_id):
    """下载试卷PDF"""
    conn = get_db()
    cursor = conn.execute("SELECT pdf_path, image_path, name FROM papers WHERE id = ?", (p_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "试卷不存在"}), 404

    pdf_path, image_path, name = row

    if pdf_path:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(pdf_path))
        if os.path.exists(full_path):
            return send_file(full_path, as_attachment=True, download_name=f"{name}.pdf")

    return jsonify({"error": "该试卷没有PDF文件"}), 404


@papers_bp.route("/api/papers/<int:p_id>/answer", methods=["POST"])
@api_login_required
def upload_paper_answer(p_id):
    """上传答案PDF"""
    conn = get_db()
    cursor = conn.execute("SELECT id FROM papers WHERE id = ?", (p_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "试卷不存在"}), 404

    if "answer_pdf" not in request.files:
        return jsonify({"error": "请上传答案PDF"}), 400

    f = request.files["answer_pdf"]
    if not f or not f.filename or f.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_PDF_EXTENSIONS:
        return jsonify({"error": "请上传PDF格式的答案"}), 400

    filename = secure_filename(f"answer_{uuid.uuid4().hex}_{f.filename}")
    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    answer_pdf_path = f"uploads/{filename}"

    conn.execute("UPDATE papers SET answer_pdf_path = ? WHERE id = ?", (answer_pdf_path, p_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "答案已上传", "answer_pdf_path": answer_pdf_path}), 201


@papers_bp.route("/api/papers/<int:p_id>/answer/download", methods=["GET"])
@api_login_required
def download_paper_answer(p_id):
    """下载答案PDF"""
    conn = get_db()
    cursor = conn.execute("SELECT answer_pdf_path, name FROM papers WHERE id = ?", (p_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "试卷不存在"}), 404

    answer_pdf_path, name = row

    if answer_pdf_path:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(answer_pdf_path))
        if os.path.exists(full_path):
            return send_file(full_path, as_attachment=True, download_name=f"{name}_答案.pdf")

    return jsonify({"error": "该试卷没有上传答案"}), 404


@papers_bp.route("/api/papers/<int:p_id>/questions", methods=["POST"])
@api_login_required
def add_paper_question(p_id):
    """向试卷添加题目"""
    data = request.get_json()
    title = data.get("title", "")
    content = data.get("content", "")
    tags = data.get("tags", "[]")
    difficulty = int(data.get("difficulty", 1))
    answer = data.get("answer", "")
    paper_q_num = data.get("paper_question_number")
    grade = data.get("grade", "初一")
    category = data.get("category", "")

    conn = get_db()
    cursor = conn.execute("SELECT image_path, name FROM papers WHERE id = ?", (p_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "试卷不存在"}), 404
    paper_image = row[0]
    paper_name = row[1]

    source = f"{paper_name} 第{paper_q_num}题"
    cursor = conn.execute(
        "INSERT INTO questions (title, content, tags, difficulty, source, image_path, answer, grade, category, paper_id, paper_question_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (title, content, tags, difficulty, source, paper_image, answer, grade, category, p_id, paper_q_num),
    )
    conn.commit()
    q_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": q_id, "message": "题目已添加"}), 201
