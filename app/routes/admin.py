"""管理功能路由 - SQLAlchemy ORM，含用户管理"""

import os
import json
import uuid
import tempfile
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from app.models import db, User, Question, Paper
from app.constants import GRADES, CATEGORIES, TAG_TO_CATEGORY, ALL_TAGS, GRADE_TAGS, ALLOWED_IMAGE_EXTENSIONS
from ocr import recognize_question
from auth import api_login_required, admin_required

admin_bp = Blueprint('admin', __name__)


# ─── 用户管理 ───────────────────────────────────────────

@admin_bp.route("/api/users", methods=["GET"])
@admin_required
def get_users():
    """获取所有用户列表"""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@admin_bp.route("/api/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id):
    """更新用户信息（管理员）"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    data = request.get_json()
    if "role" in data and data["role"] in ("student", "teacher", "admin"):
        user.role = data["role"]
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "password" in data and len(data["password"]) >= 6:
        user.password_hash = generate_password_hash(data["password"])

    db.session.commit()
    return jsonify({"message": "用户已更新", "user": user.to_dict()})


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    if user.username == "admin":
        return jsonify({"error": "不能删除管理员账户"}), 400
    if user.id == current_user.id:
        return jsonify({"error": "不能删除自己"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "用户已删除"})


@admin_bp.route("/api/user/me", methods=["GET"])
@api_login_required
def get_current_user():
    """获取当前用户信息"""
    return jsonify({"user": current_user.to_dict()})


# ─── 备份 ───────────────────────────────────────────────

@admin_bp.route("/api/backup/export", methods=["GET"])
@api_login_required
def export_backup():
    """导出数据库备份"""
    db_path = current_app.config["DATABASE"]
    if not os.path.exists(db_path):
        return jsonify({"error": "数据库不存在"}), 404

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f"math_question_bank_backup_{timestamp}.db"
    )


@admin_bp.route("/api/backup/import", methods=["POST"])
@api_login_required
def import_backup():
    """导入数据库备份"""
    import sqlite3

    if "backup_file" not in request.files:
        return jsonify({"error": "请上传备份文件"}), 400

    f = request.files["backup_file"]
    if not f or not f.filename or not f.filename.endswith(".db"):
        return jsonify({"error": "请上传 .db 格式的备份文件"}), 400

    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)
    if file_size > 100 * 1024 * 1024:
        return jsonify({"error": "备份文件大小不能超过100MB"}), 400

    header = f.read(16)
    f.seek(0)
    if not header.startswith(b'SQLite format 3'):
        return jsonify({"error": "不是有效的SQLite数据库文件"}), 400

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, 'backup.db')

    try:
        f.save(temp_path)

        conn = sqlite3.connect(temp_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        required_tables = {'questions', 'papers', 'tests', 'practice_sessions'}
        missing_tables = required_tables - tables
        if missing_tables:
            return jsonify({"error": f"备份文件缺少必要的表: {', '.join(missing_tables)}"}), 400

        db_path = current_app.config["DATABASE"]
        if os.path.exists(db_path):
            backup_path = db_path + ".bak"
            shutil.copy2(db_path, backup_path)

        shutil.move(temp_path, db_path)
        return jsonify({"message": "数据库已恢复，请刷新页面"})

    except Exception as e:
        return jsonify({"error": f"导入失败: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


# ─── 元数据 ─────────────────────────────────────────────

@admin_bp.route("/api/grades")
@api_login_required
def get_grades():
    return jsonify({"grades": GRADES})


@admin_bp.route("/api/categories")
@api_login_required
def get_categories():
    return jsonify({"categories": CATEGORIES})


@admin_bp.route("/api/tags", methods=["GET"])
@api_login_required
def get_tags():
    """获取所有标签"""
    grade = request.args.get("grade", "")
    tag_set = set()

    if grade:
        if grade in GRADE_TAGS:
            tag_set.update(GRADE_TAGS[grade])
        questions = Question.query.filter_by(grade=grade).all()
    else:
        tag_set.update(ALL_TAGS)
        questions = Question.query.all()

    for q in questions:
        try:
            tag_set.update(json.loads(q.tags))
        except (json.JSONDecodeError, TypeError):
            pass

    return jsonify({"tags": sorted(tag_set)})


@admin_bp.route("/api/stats")
@api_login_required
def get_stats():
    """获取统计数据"""
    stats = {"total": Question.query.count()}
    for grade in GRADES:
        stats[grade] = Question.query.filter_by(grade=grade).count()
    stats["papers"] = Paper.query.count()
    return jsonify(stats)


# ─── OCR ────────────────────────────────────────────────

@admin_bp.route("/api/ocr", methods=["POST"])
@api_login_required
def ocr_recognize():
    """OCR文字识别"""
    if "image" not in request.files:
        return jsonify({"error": "请上传图片"}), 400

    f = request.files["image"]
    if not f or not f.filename:
        return jsonify({"error": "无效的文件"}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "不支持的图片格式"}), 400

    filename = secure_filename(f"ocr_{uuid.uuid4().hex}_{f.filename}")
    temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    f.save(temp_path)

    try:
        result = recognize_question(temp_path)
        return jsonify(result)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ─── 文件清理 ───────────────────────────────────────────

@admin_bp.route("/api/cleanup", methods=["POST"])
@api_login_required
def run_cleanup():
    """执行文件清理"""
    from app.cleanup import run_cleanup as do_cleanup
    result = do_cleanup()
    return jsonify({"message": "清理完成", "result": result})


# ─── 题目导入导出 ───────────────────────────────────────

@admin_bp.route("/api/questions/export", methods=["GET"])
@api_login_required
def export_questions():
    """导出所有题目为JSON"""
    questions = Question.query.order_by(Question.id).all()
    return jsonify({
        "version": "2.0",
        "count": len(questions),
        "questions": [q.to_dict() for q in questions]
    })


@admin_bp.route("/api/questions/import", methods=["POST"])
@api_login_required
def import_questions():
    """从JSON导入题目"""
    data = request.get_json()
    if not data or "questions" not in data:
        return jsonify({"error": "无效的JSON格式"}), 400

    questions = data["questions"]
    if not questions:
        return jsonify({"error": "没有要导入的题目"}), 400

    imported = 0
    skipped = 0

    for q in questions:
        # 去重：标题+内容
        exists = Question.query.filter_by(
            title=q.get("title", ""),
            content=q.get("content", "")
        ).first()
        if exists:
            skipped += 1
            continue

        question = Question(
            title=q.get("title", ""),
            content=q.get("content", ""),
            tags=q.get("tags", "[]"),
            difficulty=q.get("difficulty", 1),
            source=q.get("source", ""),
            image_path=q.get("image_path", ""),
            answer=q.get("answer", ""),
            analysis=q.get("analysis", ""),
            grade=q.get("grade", "初一"),
            category=q.get("category", ""),
            paper_id=q.get("paper_id"),
            paper_question_number=q.get("paper_question_number"),
            created_by=current_user.id
        )
        db.session.add(question)
        imported += 1

    db.session.commit()

    return jsonify({
        "message": f"导入完成：成功 {imported} 题，跳过 {skipped} 题",
        "imported": imported,
        "skipped": skipped
    })
