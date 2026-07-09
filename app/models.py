"""数据库模型 - SQLAlchemy ORM"""

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student / teacher / admin
    display_name = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # 关系
    questions = db.relationship('Question', backref='author', lazy='dynamic')
    papers = db.relationship('Paper', backref='author', lazy='dynamic')
    tests = db.relationship('Test', backref='author', lazy='dynamic')
    practice_sessions = db.relationship('PracticeSession', backref='user', lazy='dynamic')
    wrong_questions = db.relationship('WrongQuestion', backref='user', lazy='dynamic')

    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role in ('teacher', 'admin')

    def is_student(self):
        return self.role == 'student'

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class Question(db.Model):
    """题目模型"""
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, default='')
    content = db.Column(db.Text, default='')
    tags = db.Column(db.Text, default='[]')  # JSON array
    difficulty = db.Column(db.Integer, default=1)
    source = db.Column(db.Text, default='')
    image_path = db.Column(db.Text, default='')
    answer = db.Column(db.Text, default='')
    analysis = db.Column(db.Text, default='')
    grade = db.Column(db.Text, default='初一')
    category = db.Column(db.Text, default='')
    paper_id = db.Column(db.Integer, db.ForeignKey('papers.id'), nullable=True)
    paper_question_number = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "source": self.source,
            "image_path": self.image_path,
            "answer": self.answer,
            "analysis": self.analysis,
            "grade": self.grade,
            "category": self.category,
            "paper_id": self.paper_id,
            "paper_question_number": self.paper_question_number,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Paper(db.Model):
    """试卷模型"""
    __tablename__ = 'papers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Text, default='初一')
    image_path = db.Column(db.Text, default='')
    pdf_path = db.Column(db.Text, default='')
    answer_pdf_path = db.Column(db.Text, default='')
    source = db.Column(db.Text, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    questions = db.relationship('Question', backref='paper', lazy='dynamic')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "grade": self.grade,
            "image_path": self.image_path,
            "pdf_path": self.pdf_path,
            "answer_pdf_path": self.answer_pdf_path,
            "source": self.source,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "questions_count": self.questions.count(),
        }


class Test(db.Model):
    """组卷模型"""
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    question_ids = db.Column(db.Text, default='[]')  # JSON array of question IDs
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "question_ids": self.question_ids,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PracticeSession(db.Model):
    """练习记录模型"""
    __tablename__ = 'practice_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_answer = db.Column(db.Text, default='')
    is_correct = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "user_answer": self.user_answer,
            "is_correct": self.is_correct,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WrongQuestion(db.Model):
    """错题本模型"""
    __tablename__ = 'wrong_questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong_at = db.Column(db.DateTime, default=datetime.utcnow)
    mastered = db.Column(db.Integer, default=0)  # 0=未掌握, 1=已掌握
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    question = db.relationship('Question', backref='wrong_entries')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_id": self.question_id,
            "wrong_count": self.wrong_count,
            "last_wrong_at": self.last_wrong_at.isoformat() if self.last_wrong_at else None,
            "mastered": self.mastered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        # 迁移旧数据库结构
        _migrate_schema()

        # 创建新表（不会修改已存在的表）
        db.create_all()

        # 创建索引
        with db.engine.connect() as conn:
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_questions_grade ON questions(grade)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_questions_paper_id ON questions(paper_id)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_id ON practice_sessions(user_id)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_practice_sessions_question_id ON practice_sessions(question_id)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_wrong_questions_user_id ON wrong_questions(user_id)"
            ))
            conn.execute(db.text(
                "CREATE INDEX IF NOT EXISTS idx_wrong_questions_user_question ON wrong_questions(user_id, question_id)"
            ))
            conn.commit()

        # 创建默认管理员账户
        _ensure_admin_user(app)

        # 如果没有示例数据则插入
        _seed_if_empty()

        db.session.commit()


def _migrate_schema():
    """迁移旧数据库结构，添加新字段"""
    import sqlite3 as _sqlite3

    db_path = db.engine.url.database
    if not db_path or not os.path.exists(db_path):
        return

    conn = _sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    # 迁移 questions 表
    if 'questions' in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(questions)").fetchall()}
        if 'created_by' not in cols:
            conn.execute("ALTER TABLE questions ADD COLUMN created_by INTEGER")

    # 迁移 papers 表
    if 'papers' in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()}
        if 'created_by' not in cols:
            conn.execute("ALTER TABLE papers ADD COLUMN created_by INTEGER")
        if 'pdf_path' not in cols:
            conn.execute("ALTER TABLE papers ADD COLUMN pdf_path TEXT DEFAULT ''")
        if 'answer_pdf_path' not in cols:
            conn.execute("ALTER TABLE papers ADD COLUMN answer_pdf_path TEXT DEFAULT ''")

    # 迁移 tests 表
    if 'tests' in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tests)").fetchall()}
        if 'created_by' not in cols:
            conn.execute("ALTER TABLE tests ADD COLUMN created_by INTEGER")

    # 迁移 practice_sessions 表
    if 'practice_sessions' in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(practice_sessions)").fetchall()}
        if 'user_id' not in cols:
            conn.execute("ALTER TABLE practice_sessions ADD COLUMN user_id INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


def _ensure_admin_user(app):
    """确保管理员账户存在"""
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        import os
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin = User(
            username='admin',
            password_hash=generate_password_hash(password),
            role='admin',
            display_name='管理员'
        )
        db.session.add(admin)
        db.session.flush()  # 获取 ID

    # 确保环境变量中的密码与数据库同步
    import os
    env_hash = os.environ.get('ADMIN_PASSWORD_HASH')
    if env_hash and admin.password_hash != env_hash:
        admin.password_hash = env_hash


def _seed_if_empty():
    """如果数据库为空则插入示例数据"""
    if Question.query.count() > 0:
        return

    import json
    from app.constants import CATEGORIES

    admin = User.query.filter_by(username='admin').first()
    admin_id = admin.id if admin else None

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
        q = Question(
            title=s["title"], content=s["content"], tags=s["tags"],
            difficulty=s["difficulty"], source=s["source"], answer=s["answer"],
            grade=s["grade"], category=s["category"], created_by=admin_id
        )
        db.session.add(q)
