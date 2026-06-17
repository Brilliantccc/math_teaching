import os
import sqlite3
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'


class User(UserMixin):
    """Simple user class for flask-login."""
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID. For single-user system, always return the admin user."""
    if user_id == '1':
        return User('1', current_app.config.get('ADMIN_USERNAME', 'admin'))
    return None


def init_auth(app):
    """Initialize authentication with the Flask app."""
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
    app.config['ADMIN_PASSWORD_HASH'] = os.environ.get(
        'ADMIN_PASSWORD_HASH',
        generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
    )

    login_manager.init_app(app)

    # Create login template if it doesn't exist
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    login_template = os.path.join(template_dir, 'login.html')
    if not os.path.exists(login_template):
        with open(login_template, 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>登录 - 数学题库管理系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-container { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h1 { text-align: center; color: #333; margin-bottom: 30px; font-size: 24px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; transition: border-color 0.3s; }
        input[type="text"]:focus, input[type="password"]:focus { outline: none; border-color: #4a90d9; }
        button { width: 100%; padding: 14px; background: #4a90d9; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 500; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #357abd; }
        .error { color: #e74c3c; text-align: center; margin-bottom: 20px; padding: 10px; background: #fdf0ef; border-radius: 6px; }
        .forgot-link { text-align: center; margin-top: 15px; }
        .forgot-link a { color: #4a90d9; text-decoration: none; font-size: 14px; }
        .forgot-link a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>📚 数学题库管理系统</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="{{ url_for('auth.login') }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">登录</button>
        </form>
        <div class="forgot-link">
            <a href="/forgot-password">忘记密码？</a>
        </div>
    </div>
</body>
</html>''')

    return app


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        admin_username = current_app.config['ADMIN_USERNAME']
        admin_password_hash = current_app.config['ADMIN_PASSWORD_HASH']

        if username == admin_username and check_password_hash(admin_password_hash, password):
            user = User('1', username)
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            error = '用户名或密码错误'

    return render_template('login.html', error=error)


@auth_bp.route('/forgot-password')
def forgot_password():
    """忘记密码页面"""
    return render_template('forgot_password.html')


@auth_bp.route('/api/reset-password', methods=['POST'])
def reset_password():
    """重置密码 API（无需登录）"""
    data = request.get_json()
    reset_code = data.get('reset_code', '')
    new_password = data.get('new_password', '')

    # 验证重置码（必须通过环境变量配置，无默认值）
    expected_code = os.environ.get('RESET_CODE')
    if not expected_code:
        return jsonify({"error": "密码重置功能未配置，请联系管理员"}), 503

    if reset_code != expected_code:
        return jsonify({"error": "重置码错误"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "新密码长度不能少于6位"}), 400

    # 更新密码
    new_hash = generate_password_hash(new_password)
    current_app.config['ADMIN_PASSWORD_HASH'] = new_hash
    os.environ['ADMIN_PASSWORD_HASH'] = new_hash

    return jsonify({"message": "密码重置成功，请使用新密码登录"})


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout."""
    logout_user()
    return redirect(url_for('auth.login'))


# Custom login_required decorator for API endpoints
def api_login_required(f):
    """Decorator for API endpoints that require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "请先登录"}), 401
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    error = None
    success = None

    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证旧密码
        admin_password_hash = current_app.config['ADMIN_PASSWORD_HASH']
        if not check_password_hash(admin_password_hash, old_password):
            error = '原密码错误'
        elif len(new_password) < 6:
            error = '新密码长度不能少于6位'
        elif new_password != confirm_password:
            error = '两次输入的新密码不一致'
        else:
            # 更新密码
            new_hash = generate_password_hash(new_password)
            current_app.config['ADMIN_PASSWORD_HASH'] = new_hash

            # 同时更新环境变量（本次会话有效）
            os.environ['ADMIN_PASSWORD_HASH'] = new_hash

            success = '密码修改成功，请重新登录'

    return render_template('change_password.html', error=error, success=success)


@auth_bp.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码 API"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    # 验证旧密码
    admin_password_hash = current_app.config['ADMIN_PASSWORD_HASH']
    if not check_password_hash(admin_password_hash, old_password):
        return jsonify({"error": "原密码错误"}), 400
    elif len(new_password) < 6:
        return jsonify({"error": "新密码长度不能少于6位"}), 400
    elif new_password != confirm_password:
        return jsonify({"error": "两次输入的新密码不一致"}), 400
    else:
        # 更新密码
        new_hash = generate_password_hash(new_password)
        current_app.config['ADMIN_PASSWORD_HASH'] = new_hash
        os.environ['ADMIN_PASSWORD_HASH'] = new_hash

        return jsonify({"message": "密码修改成功"})
