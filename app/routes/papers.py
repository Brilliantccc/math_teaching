"""试卷管理路由 - SQLAlchemy ORM"""

import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user

from app.models import db, Paper, Question
from app.constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_PDF_EXTENSIONS
from auth import api_login_required

papers_bp = Blueprint('papers', __name__)


@papers_bp.route("/api/papers", methods=["GET"])
@api_login_required
def get_papers():
    """获取试卷列表"""
    grade = request.args.get("grade", "")

    query = Paper.query
    if grade:
        query = query.filter(Paper.grade == grade)

    papers = query.order_by(Paper.created_at.desc()).all()
    return jsonify({"papers": [p.to_dict() for p in papers]})


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

    # 处理图片上传
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename and f.filename.rsplit(".", 1)[-1].lower() in ALLOWED_IMAGE_EXTENSIONS:
            filename = secure_filename(f"paper_{uuid.uuid4().hex}_{f.filename}")
            f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            image_path = f"uploads/{filename}"

    if not pdf_path and not image_path:
        return jsonify({"error": "请上传试卷文件（PDF或图片）"}), 400

    paper = Paper(
        name=name, grade=grade, image_path=image_path,
        pdf_path=pdf_path, source=source, created_by=current_user.id
    )
    db.session.add(paper)
    db.session.commit()

    return jsonify({"id": paper.id, "pdf_path": pdf_path, "image_path": image_path, "message": "试卷已上传"}), 201


@papers_bp.route("/api/papers/<int:p_id>", methods=["GET"])
@api_login_required
def get_paper(p_id):
    """获取试卷详情"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    data = paper.to_dict()
    questions = Question.query.filter_by(paper_id=p_id) \
        .order_by(Question.paper_question_number).all()
    data["questions"] = [q.to_dict() for q in questions]
    return jsonify(data)


@papers_bp.route("/api/papers/<int:p_id>", methods=["DELETE"])
@api_login_required
def delete_paper(p_id):
    """删除试卷"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    # 解除关联题目的引用
    Question.query.filter_by(paper_id=p_id).update({
        "paper_id": None, "paper_question_number": None
    })
    db.session.delete(paper)
    db.session.commit()
    return jsonify({"message": "试卷已删除"})


@papers_bp.route("/api/papers/<int:p_id>/download", methods=["GET"])
@api_login_required
def download_paper(p_id):
    """下载试卷PDF"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    if paper.pdf_path:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(paper.pdf_path))
        if os.path.exists(full_path):
            return send_file(full_path, as_attachment=True, download_name=f"{paper.name}.pdf")

    return jsonify({"error": "该试卷没有PDF文件"}), 404


@papers_bp.route("/api/papers/<int:p_id>/answer", methods=["POST"])
@api_login_required
def upload_paper_answer(p_id):
    """上传答案PDF"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    if "answer_pdf" not in request.files:
        return jsonify({"error": "请上传答案PDF"}), 400

    f = request.files["answer_pdf"]
    if not f or not f.filename or f.filename.rsplit(".", 1)[-1].lower() not in ALLOWED_PDF_EXTENSIONS:
        return jsonify({"error": "请上传PDF格式的答案"}), 400

    filename = secure_filename(f"answer_{uuid.uuid4().hex}_{f.filename}")
    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    paper.answer_pdf_path = f"uploads/{filename}"
    db.session.commit()

    return jsonify({"message": "答案已上传", "answer_pdf_path": paper.answer_pdf_path}), 201


@papers_bp.route("/api/papers/<int:p_id>/answer/download", methods=["GET"])
@api_login_required
def download_paper_answer(p_id):
    """下载答案PDF"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    if paper.answer_pdf_path:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(paper.answer_pdf_path))
        if os.path.exists(full_path):
            return send_file(full_path, as_attachment=True, download_name=f"{paper.name}_答案.pdf")

    return jsonify({"error": "该试卷没有上传答案"}), 404


@papers_bp.route("/api/papers/<int:p_id>/questions", methods=["POST"])
@api_login_required
def add_paper_question(p_id):
    """向试卷添加题目"""
    paper = Paper.query.get(p_id)
    if not paper:
        return jsonify({"error": "试卷不存在"}), 404

    data = request.get_json()
    question = Question(
        title=data.get("title", ""),
        content=data.get("content", ""),
        tags=data.get("tags", "[]"),
        difficulty=int(data.get("difficulty", 1)),
        answer=data.get("answer", ""),
        paper_question_number=data.get("paper_question_number"),
        grade=data.get("grade", "初一"),
        category=data.get("category", ""),
        source=f"{paper.name} 第{data.get('paper_question_number', '?')}题",
        image_path=paper.image_path,
        paper_id=p_id,
        created_by=current_user.id
    )
    db.session.add(question)
    db.session.commit()

    return jsonify({"id": question.id, "message": "题目已添加"}), 201
