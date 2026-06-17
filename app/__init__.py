"""应用工厂模块"""

import os
import logging
from flask import Flask, redirect, url_for, render_template, jsonify, request
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config
from auth import init_auth, auth_bp
from app.routes import questions_bp, papers_bp, tests_bp, practice_bp, admin_bp
from app.models import init_db

# 初始化速率限制器（延迟初始化）
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name=None):
    """创建Flask应用"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config[config_name])

    # 生产环境安全检查
    if config_name == 'production':
        if not app.config.get('SECRET_KEY'):
            raise RuntimeError("生产环境必须设置 SECRET_KEY 环境变量")

    # 配置日志
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting app in {config_name} mode")

    # 初始化CSRF保护
    csrf = CSRFProtect(app)

    # 初始化速率限制
    limiter.init_app(app)

    # 初始化认证
    init_auth(app)

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(papers_bp)
    app.register_blueprint(tests_bp)
    app.register_blueprint(practice_bp)
    app.register_blueprint(admin_bp)

    # 页面路由
    from app.constants import GRADES, CATEGORIES

    @app.route("/")
    def index():
        return render_template("index.html", grades=GRADES)

    @app.route("/upload")
    def upload_page():
        return render_template("upload.html", grades=GRADES, categories=list(CATEGORIES.keys()), categories_detail=CATEGORIES)

    @app.route("/practice")
    def practice_page():
        return render_template("practice.html", grades=GRADES)

    @app.route("/practice/stats")
    def practice_stats_page():
        return render_template("practice_stats.html", grades=GRADES)

    @app.route("/wrong-questions")
    def wrong_questions_page():
        return render_template("wrong_questions.html", grades=GRADES)

    @app.route("/test")
    def test_page():
        return render_template("test.html", grades=GRADES)

    @app.route("/manage")
    def manage_page():
        return render_template("manage.html", grades=GRADES, categories=list(CATEGORIES.keys()), categories_detail=CATEGORIES)

    @app.route("/question/edit/<int:q_id>")
    def question_edit_page(q_id):
        return render_template("question_edit.html", grades=GRADES, categories=list(CATEGORIES.keys()), categories_detail=CATEGORIES, question_id=q_id)

    @app.route("/paper-manage")
    def paper_manage_page():
        return render_template("paper_manage.html", grades=GRADES)

    @app.route("/papers")
    def papers_page():
        """旧路由重定向"""
        return redirect(url_for('paper_manage_page'))

    # 全局模板变量
    @app.context_processor
    def inject_grades():
        return dict(grades=GRADES)

    # 错误处理器
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "资源不存在"}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "服务器内部错误"}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "文件大小超过限制"}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    # 初始化数据库
    init_db(app)

    # 确保上传目录存在
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
