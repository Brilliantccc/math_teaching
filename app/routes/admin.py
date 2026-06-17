"""管理功能路由（元数据、备份、OCR等）"""

import os
import json
import uuid
import sqlite3
import tempfile
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.models import get_db
from app.constants import GRADES, CATEGORIES, TAG_TO_CATEGORY, ALL_TAGS, GRADE_TAGS, ALLOWED_IMAGE_EXTENSIONS
from ocr import recognize_question
from auth import api_login_required

admin_bp = Blueprint('admin', __name__)


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
    """导入数据库备份（带验证）"""
    if "backup_file" not in request.files:
        return jsonify({"error": "请上传备份文件"}), 400

    f = request.files["backup_file"]
    if not f or not f.filename or not f.filename.endswith(".db"):
        return jsonify({"error": "请上传 .db 格式的备份文件"}), 400

    # 检查文件大小（最大100MB）
    f.seek(0, os.SEEK_END)
    file_size = f.tell()
    f.seek(0)
    if file_size > 100 * 1024 * 1024:
        return jsonify({"error": "备份文件大小不能超过100MB"}), 400

    # 验证SQLite文件头
    header = f.read(16)
    f.seek(0)
    if not header.startswith(b'SQLite format 3'):
        return jsonify({"error": "不是有效的SQLite数据库文件"}), 400

    # 保存到临时位置进行验证
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, 'backup.db')

    try:
        f.save(temp_path)

        # 验证数据库结构
        conn = sqlite3.connect(temp_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        required_tables = {'questions', 'papers', 'tests', 'practice_sessions'}
        missing_tables = required_tables - tables
        if missing_tables:
            return jsonify({"error": f"备份文件缺少必要的表: {', '.join(missing_tables)}"}), 400

        # 保存当前数据库作为备份
        db_path = current_app.config["DATABASE"]
        if os.path.exists(db_path):
            backup_path = db_path + ".bak"
            shutil.copy2(db_path, backup_path)

        # 导入已验证的数据库
        shutil.move(temp_path, db_path)

        return jsonify({"message": "数据库已恢复，请刷新页面"})

    except Exception as e:
        return jsonify({"error": f"导入失败: {str(e)}"}), 500
    finally:
        # 清理临时目录
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


@admin_bp.route("/api/grades")
@api_login_required
def get_grades():
    """获取年级列表"""
    return jsonify({"grades": GRADES})


@admin_bp.route("/api/categories")
@api_login_required
def get_categories():
    """获取分类列表"""
    return jsonify({"categories": CATEGORIES})


@admin_bp.route("/api/tags", methods=["GET"])
@api_login_required
def get_tags():
    """获取所有标签"""
    grade = request.args.get("grade", "")
    conn = get_db()
    tag_set = set()

    if grade:
        cursor = conn.execute("SELECT tags FROM questions WHERE grade = ?", (grade,))
        if grade in GRADE_TAGS:
            tag_set.update(GRADE_TAGS[grade])
    else:
        cursor = conn.execute("SELECT tags FROM questions")
        tag_set.update(ALL_TAGS)

    for row in cursor.fetchall():
        try:
            tag_set.update(json.loads(row[0]))
        except (json.JSONDecodeError, TypeError):
            pass
    conn.close()
    return jsonify({"tags": sorted(tag_set)})


@admin_bp.route("/api/stats")
@api_login_required
def get_stats():
    """获取统计数据"""
    conn = get_db()
    stats = {"total": 0}
    cursor = conn.execute("SELECT COUNT(*) FROM questions")
    stats["total"] = cursor.fetchone()[0]
    for grade in GRADES:
        cursor = conn.execute("SELECT COUNT(*) FROM questions WHERE grade = ?", (grade,))
        stats[grade] = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM papers")
    stats["papers"] = cursor.fetchone()[0]
    conn.close()
    return jsonify(stats)


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

    # 保存临时文件
    filename = secure_filename(f"ocr_{uuid.uuid4().hex}_{f.filename}")
    temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    f.save(temp_path)

    try:
        result = recognize_question(temp_path)
        return jsonify(result)
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@admin_bp.route("/api/cleanup", methods=["POST"])
@api_login_required
def run_cleanup():
    """执行文件清理"""
    from app.cleanup import run_cleanup as do_cleanup
    result = do_cleanup()
    return jsonify({"message": "清理完成", "result": result})


@admin_bp.route("/api/questions/export", methods=["GET"])
@api_login_required
def export_questions():
    """导出所有题目为JSON"""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM questions ORDER BY id")
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "version": "1.0",
        "count": len(questions),
        "questions": questions
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

    conn = get_db()
    imported = 0
    skipped = 0

    for q in questions:
        try:
            # 检查题目是否已存在（通过标题和内容去重）
            cursor = conn.execute(
                "SELECT id FROM questions WHERE title = ? AND content = ?",
                (q.get("title", ""), q.get("content", ""))
            )
            if cursor.fetchone():
                skipped += 1
                continue

            conn.execute(
                """INSERT INTO questions (title, content, tags, difficulty, source, image_path,
                   answer, analysis, grade, category, paper_id, paper_question_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q.get("title", ""),
                    q.get("content", ""),
                    q.get("tags", "[]"),
                    q.get("difficulty", 1),
                    q.get("source", ""),
                    q.get("image_path", ""),
                    q.get("answer", ""),
                    q.get("analysis", ""),
                    q.get("grade", "初一"),
                    q.get("category", ""),
                    q.get("paper_id"),
                    q.get("paper_question_number")
                )
            )
            imported += 1
        except Exception as e:
            skipped += 1
            continue

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"导入完成：成功 {imported} 题，跳过 {skipped} 题",
        "imported": imported,
        "skipped": skipped
    })
