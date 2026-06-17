"""文件清理模块 - 自动清理孤立文件和临时PDF"""

import os
import time
import logging
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)


def get_db():
    """延迟导入避免循环依赖"""
    from app.models import get_db as _get_db
    return _get_db()


def cleanup_orphaned_uploads():
    """
    清理孤立的上传文件（数据库中没有引用的文件）
    返回: 删除的文件数量
    """
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_dir):
        return 0

    # 获取数据库中所有引用的文件
    referenced_files = set()
    try:
        conn = get_db()

        # 获取题目引用的文件
        cursor = conn.execute("SELECT image_path FROM questions WHERE image_path != ''")
        for row in cursor.fetchall():
            if row[0]:
                # image_path 格式: uploads/filename
                filename = os.path.basename(row[0])
                referenced_files.add(filename)

        # 获取试卷引用的文件
        cursor = conn.execute("SELECT pdf_path, image_path, answer_pdf_path FROM papers")
        for row in cursor.fetchall():
            for path in row:
                if path:
                    filename = os.path.basename(path)
                    referenced_files.add(filename)

        conn.close()
    except Exception as e:
        logger.error(f"Failed to query referenced files: {str(e)}")
        return 0

    # 扫描上传目录
    deleted_count = 0
    for filename in os.listdir(upload_dir):
        # 跳过目录
        filepath = os.path.join(upload_dir, filename)
        if os.path.isdir(filepath):
            continue

        # 检查是否被引用
        if filename not in referenced_files:
            try:
                os.remove(filepath)
                logger.info(f"Deleted orphaned file: {filename}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {filename}: {str(e)}")

    return deleted_count


def cleanup_temp_files(max_age_hours=24):
    """
    清理临时文件（生成的预览PDF等）
    max_age_hours: 文件最大保留时间（小时）
    返回: 删除的文件数量
    """
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_dir):
        return 0

    cutoff_time = time.time() - (max_age_hours * 3600)
    deleted_count = 0

    for filename in os.listdir(upload_dir):
        filepath = os.path.join(upload_dir, filename)
        if os.path.isdir(filepath):
            continue

        # 只清理预览和测试生成的临时PDF
        if not filename.startswith(('preview_', 'test_')):
            continue

        # 检查文件修改时间
        try:
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                logger.info(f"Deleted temp file: {filename}")
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Failed to delete temp file {filename}: {str(e)}")

    return deleted_count


def run_cleanup():
    """
    执行完整的清理任务
    返回: 清理结果字典
    """
    logger.info("Starting file cleanup...")

    orphaned_deleted = cleanup_orphaned_uploads()
    temp_deleted = cleanup_temp_files()

    result = {
        "orphaned_files_deleted": orphaned_deleted,
        "temp_files_deleted": temp_deleted,
        "total_deleted": orphaned_deleted + temp_deleted,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Cleanup completed: {result}")
    return result
