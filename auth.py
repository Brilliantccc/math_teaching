"""多用户认证系统"""

import os
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'


@login_manager.user_loader
def load_user(user_id):
    """通过 ID 加载用户"""
    from app.models import User
    return User.query.get(int(user_id))


def init_auth(app):
    """初始化认证系统"""
    login_manager.init_app(app)

    # 确保上传目录存在
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ─── 登录 ───────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        from app.models import User, db

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            error = '用户名或密码错误'

    return render_template('login.html', error=error)


# ─── 注册 ───────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        from app.models import User, db

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()
        role = request.form.get('role', 'student')

        # 验证
        if not username or len(username) < 2:
            error = '用户名至少需要2个字符'
        elif not password or len(password) < 6:
            error = '密码至少需要6个字符'
        elif password != confirm_password:
            error = '两次输入的密码不一致'
        elif User.query.filter_by(username=username).first():
            error = '用户名已存在'
        else:
            # 只允许注册学生和教师，管理员只能通过数据库创建
            if role not in ('student', 'teacher'):
                role = 'student'

            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                display_name=display_name or username
            )
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for('index'))

    return render_template('register.html', error=error)


# ─── 登出 ───────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('auth.login'))


# ─── 密码管理 ───────────────────────────────────────────

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    error = None
    success = None

    if request.method == 'POST':
        from app.models import db

        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not check_password_hash(current_user.password_hash, old_password):
            error = '原密码错误'
        elif len(new_password) < 6:
            error = '新密码长度不能少于6位'
        elif new_password != confirm_password:
            error = '两次输入的新密码不一致'
        else:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            success = '密码修改成功'

    return render_template('change_password.html', error=error, success=success)


@auth_bp.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码 API"""
    from app.models import db

    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not check_password_hash(current_user.password_hash, old_password):
        return jsonify({"error": "原密码错误"}), 400
    elif len(new_password) < 6:
        return jsonify({"error": "新密码长度不能少于6位"}), 400
    elif new_password != confirm_password:
        return jsonify({"error": "两次输入的新密码不一致"}), 400
    else:
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({"message": "密码修改成功"})


# ─── 忘记密码 ───────────────────────────────────────────

@auth_bp.route('/forgot-password')
def forgot_password():
    """忘记密码页面"""
    return render_template('forgot_password.html')


@auth_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    """重置密码 API（通过重置码）"""
    from app.models import User, db

    data = request.get_json()
    reset_code = data.get('reset_code', '')
    new_password = data.get('new_password', '')
    target_username = data.get('username', 'admin')

    expected_code = os.environ.get('RESET_CODE')
    if not expected_code:
        return jsonify({"error": "密码重置功能未配置，请联系管理员"}), 503

    if reset_code != expected_code:
        return jsonify({"error": "重置码错误"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "新密码长度不能少于6位"}), 400

    user = User.query.filter_by(username=target_username).first()
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "密码重置成功，请使用新密码登录"})


# ─── 权限装饰器 ─────────────────────────────────────────

def api_login_required(f):
    """API 登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "请先登录"}), 401
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """教师权限装饰器（教师或管理员）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "请先登录"}), 401
        if not current_user.is_teacher():
            return jsonify({"error": "需要教师权限"}), 403
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "请先登录"}), 401
        if not current_user.is_admin():
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated_function
