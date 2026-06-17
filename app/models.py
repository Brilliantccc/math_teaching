"""数据库模型和操作"""

import sqlite3
import json
import os
from flask import current_app


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(current_app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def migrate_schema(conn):
    """迁移数据库结构，添加新字段/表"""
    cursor = conn.execute("PRAGMA table_info(questions)")
    columns = [row[1] for row in cursor.fetchall()]

    if "grade" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN grade TEXT DEFAULT '初一'")
    if "category" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN category TEXT DEFAULT ''")
    if "paper_id" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN paper_id INTEGER")
    if "paper_question_number" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN paper_question_number INTEGER")
    if "analysis" not in columns:
        conn.execute("ALTER TABLE questions ADD COLUMN analysis TEXT DEFAULT ''")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT DEFAULT '初一',
            image_path TEXT DEFAULT '',
            pdf_path TEXT DEFAULT '',
            answer_pdf_path TEXT DEFAULT '',
            source TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor = conn.execute("PRAGMA table_info(papers)")
    paper_columns = [row[1] for row in cursor.fetchall()]
    if "pdf_path" not in paper_columns:
        conn.execute("ALTER TABLE papers ADD COLUMN pdf_path TEXT DEFAULT ''")
    if "answer_pdf_path" not in paper_columns:
        conn.execute("ALTER TABLE papers ADD COLUMN answer_pdf_path TEXT DEFAULT ''")

    conn.commit()


def backfill_categories(conn, tag_to_category):
    """自动为未分类的题目分配分类"""
    cursor = conn.execute("SELECT id, tags FROM questions WHERE category = '' OR category IS NULL")
    for row in cursor.fetchall():
        q_id = row[0]
        try:
            tags = json.loads(row[1])
        except Exception:
            continue
        for tag in tags:
            if tag in tag_to_category:
                conn.execute("UPDATE questions SET category = ? WHERE id = ?", (tag_to_category[tag], q_id))
                break
    conn.commit()


def seed_data(conn):
    """插入示例数据"""
    from app.constants import CATEGORIES

    samples = [
        {"title": "计算：(-3) + (+5)", "content": "计算有理数加法",
         "tags": json.dumps(["有理数加减", "计算技巧"], ensure_ascii=False),
         "difficulty": 1, "source": "示例", "answer": "2",
         "grade": "初一", "category": "数与式"},
        {"title": "解方程：2x + 3 = 7", "content": "一元一次方程基础题",
         "tags": json.dumps(["一元一次方程", "解方程"], ensure_ascii=False),
         "difficulty": 1, "source": "示例", "answer": "x = 2",
         "grade": "初一", "category": "代数方程"},
        {"title": "求 |-7| 的值", "content": "绝对值概念题",
         "tags": json.dumps(["绝对值"], ensure_ascii=False),
         "difficulty": 1, "source": "示例", "answer": "7",
         "grade": "初一", "category": "数与式"},
    ]
    for s in samples:
        conn.execute(
            "INSERT INTO questions (title, content, tags, difficulty, source, answer, grade, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (s["title"], s["content"], s["tags"], s["difficulty"], s["source"], s["answer"], s["grade"], s["category"]),
        )


def init_db(app):
    """初始化数据库"""
    from app.constants import TAG_TO_CATEGORY

    with app.app_context():
        conn = get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                difficulty INTEGER DEFAULT 1,
                source TEXT DEFAULT '',
                image_path TEXT DEFAULT '',
                answer TEXT DEFAULT '',
                analysis TEXT DEFAULT '',
                grade TEXT DEFAULT '初一',
                category TEXT DEFAULT '',
                paper_id INTEGER,
                paper_question_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                question_ids TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS practice_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                user_answer TEXT DEFAULT '',
                is_correct INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                grade TEXT DEFAULT '初一',
                image_path TEXT NOT NULL,
                source TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        migrate_schema(conn)
        backfill_categories(conn, TAG_TO_CATEGORY)

        # 创建索引以优化查询性能
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_questions_grade ON questions(grade);
            CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
            CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
            CREATE INDEX IF NOT EXISTS idx_questions_paper_id ON questions(paper_id);
            CREATE INDEX IF NOT EXISTS idx_practice_sessions_question_id ON practice_sessions(question_id);
            CREATE INDEX IF NOT EXISTS idx_practice_sessions_is_correct ON practice_sessions(is_correct);
        """)

        cursor = conn.execute("SELECT COUNT(*) FROM questions")
        row = cursor.fetchone()
        if row[0] == 0:
            seed_data(conn)

        conn.commit()
        conn.close()
