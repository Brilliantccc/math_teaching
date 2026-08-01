# 数学题库管理系统

面向初高中数学的教学资源管理平台，支持多用户角色（管理员/教师/学生），提供题目管理、试卷组卷、在线练习、错题本、学习统计等功能。

## ✨ 功能特性

### 👥 多用户系统
- **注册/登录** — 支持学生、教师角色自主注册，管理员账户自动创建
- **角色权限** — 管理员（全部权限）、教师（上传/组卷）、学生（练习/错题本）
- **密码管理** — 修改密码、通过重置码恢复密码，全部持久化到数据库
- **用户管理** — 管理员可查看、编辑角色、删除用户

### 📝 题目管理
- 支持图片上传，自动 OCR 识别题目内容
- 支持 LaTeX 数学公式编辑，实时预览
- 按年级（初一至高三）、知识点、难度分类管理
- 答案与解析分离录入
- **题目编辑功能** — 随时修改已有题目
- **批量操作** — 批量删除、批量修改年级
- **JSON 导入导出** — 题目数据备份与迁移

### 📄 试卷管理
- 支持 PDF / 图片格式试卷上传
- 支持上传答案 PDF，一键下载
- 试卷列表展示与管理

### 🎯 智能组卷
- 按年级、知识点、难度随机抽题
- **拖拽排序** — 手动调整题目顺序
- 导出 PDF 格式试卷（含答案）

### 📊 练习模式
- 按条件随机出题
- 即时判分与答案展示
- **每用户独立记录** — 练习数据按用户隔离

### 📖 错题本
- **自动收集** — 练习中答错的题目自动归入错题本
- **累计统计** — 显示每道题的答错次数
- **掌握标记** — 可手动标记"已掌握"，筛选未掌握题目
- **错题重练** — 直接在错题本内重新练习

### 📈 学习统计
- 总体正确率、连续练习天数
- 按知识点统计掌握度
- 按难度统计正确率
- 最近练习记录

### ⚡ 性能优化
- 数据库索引（年级、分类、难度、试卷ID等常用查询字段）
- 批量获取题目接口，避免 N+1 逐题请求
- 试卷列表子查询统计题目数量
- PDF 导出后自动清理临时文件

### 💾 数据安全
- 数据库一键备份导出
- 支持从备份文件恢复数据（带验证）
- 自动清理孤立文件
- CSRF / XSS 防护、API 速率限制

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1 |
| 数据库 | SQLite |
| 前端 | HTML5, CSS3, JavaScript |
| 数学渲染 | MathJax 3 |
| OCR | Tesseract-OCR, Pillow |
| PDF | PyMuPDF, ReportLab |
| 安全 | Flask-Login, Flask-WTF, Flask-Limiter |

## 📁 项目结构

```
math-question-bank/
├── app/                      # 应用工厂模块
│   ├── __init__.py           # 应用工厂与路由注册
│   ├── constants.py          # 常量定义（年级、知识点）
│   ├── models.py             # SQLAlchemy ORM 模型（6张表）
│   ├── cleanup.py            # 文件清理模块
│   └── routes/               # 蓝图路由
│       ├── questions.py      # 题目管理 API
│       ├── papers.py         # 试卷管理 API
│       ├── tests.py          # 组卷管理 API
│       ├── practice.py       # 练习 + 错题本 + 学习统计 API
│       └── admin.py          # 管理 + 用户管理 API
├── auth.py                   # 多用户认证模块（注册/登录/权限）
├── config.py                 # 配置文件
├── run.py                    # 应用入口
├── ocr.py                    # OCR 文字识别模块
├── pdf_utils.py              # PDF 读取/生成工具
├── requirements.txt          # Python 依赖
├── static/
│   ├── css/style.css         # 样式文件
│   ├── js/app.js             # 前端公共脚本
│   └── uploads/              # 上传文件存储
└── templates/                # Jinja2 模板
    ├── base.html             # 基础布局（含用户信息导航）
    ├── login.html            # 登录页面
    ├── register.html         # 注册页面
    ├── forgot_password.html  # 忘记密码页面
    ├── change_password.html  # 修改密码页面
    ├── index.html            # 首页
    ├── upload.html           # 上传题目
    ├── manage.html           # 题库管理
    ├── question_edit.html    # 题目编辑
    ├── paper_manage.html     # 试卷管理
    ├── test.html             # 智能组卷
    ├── practice.html         # 练习模式
    ├── practice_stats.html   # 学习统计
    ├── wrong_questions.html  # 错题本
    └── errors/               # 错误页面
        ├── 404.html
        └── 500.html
```

## 🚀 安装与运行

### 1. 安装依赖

```bash
cd math-question-bank
pip install -r requirements.txt
```

### 2. 安装系统依赖（OCR 功能需要）

<details>
<summary><b>Windows</b></summary>

下载并安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)，默认安装路径即可。
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install tesseract
brew install tesseract-lang  # 中文语言包
```
</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```
</details>

### 3. 环境变量配置（可选）

程序会**自动检测**系统路径，通常无需手动配置。如需覆盖默认值：

<details>
<summary><b>Windows (CMD)</b></summary>

```cmd
set SECRET_KEY=your-secret-key
set TESSERACT_PATH=D:\Tesseract-OCR\tesseract.exe
set FONT_PATH=C:\Windows\Fonts\msyh.ttc
set RESET_CODE=your-reset-code
```
</details>

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
$env:SECRET_KEY="your-secret-key"
$env:TESSERACT_PATH="D:\Tesseract-OCR\tesseract.exe"
$env:FONT_PATH="C:\Windows\Fonts\msyh.ttc"
$env:RESET_CODE="your-reset-code"
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
export SECRET_KEY=your-secret-key
export RESET_CODE=your-reset-code

# 仅在非标准安装时需要：
# export TESSERACT_PATH=/usr/local/bin/tesseract
# export FONT_PATH=/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc
```
</details>

### 4. 启动服务

```bash
python run.py
```

访问 http://localhost:5001

> 💡 端口号可在 [run.py](run.py) 中修改，默认为 `5001`。

### 4. 默认账户

- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次登录后请修改默认密码！可通过 `/register` 页面注册新用户（学生/教师）。

## 📡 API 接口

所有 API 需要登录认证，通过 `X-CSRFToken` 头部传递 CSRF token。

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/login` | 登录 |
| GET/POST | `/register` | 注册 |
| GET | `/logout` | 退出登录 |
| POST | `/api/change-password` | 修改密码 |
| POST | `/api/reset-password` | 重置密码（无需登录） |

### 用户管理（管理员）
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/user/me` | 获取当前用户信息 |
| GET | `/api/users` | 获取所有用户列表 |
| PUT | `/api/users/<id>` | 更新用户（角色/密码） |
| DELETE | `/api/users/<id>` | 删除用户 |

### 题目管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions` | 获取题目列表（支持筛选分页） |
| GET | `/api/questions/batch?ids=` | 批量获取题目 |
| GET | `/api/questions/<id>` | 获取单个题目详情 |
| POST | `/api/questions` | 创建题目 |
| PUT | `/api/questions/<id>` | 更新题目 |
| DELETE | `/api/questions/<id>` | 删除题目 |
| POST | `/api/questions/batch-delete` | 批量删除题目 |
| POST | `/api/questions/batch-update` | 批量更新题目 |
| GET | `/api/questions/export` | 导出题目 JSON |
| POST | `/api/questions/import` | 导入题目 JSON |

### 试卷管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/papers` | 获取试卷列表 |
| GET | `/api/papers/<id>` | 获取试卷详情 |
| POST | `/api/papers` | 上传试卷 |
| DELETE | `/api/papers/<id>` | 删除试卷 |
| GET | `/api/papers/<id>/download` | 下载试卷 PDF |
| POST | `/api/papers/<id>/answer` | 上传答案 PDF |
| GET | `/api/papers/<id>/answer/download` | 下载答案 PDF |
| POST | `/api/papers/<id>/questions` | 向试卷添加题目 |

### 组卷管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tests` | 获取组卷列表 |
| GET | `/api/tests/<id>` | 获取组卷详情 |
| POST | `/api/tests` | 创建组卷 |
| POST | `/api/tests/auto` | 自动生成组卷 |
| GET | `/api/tests/<id>/pdf` | 导出组卷 PDF |
| POST | `/api/tests/preview/pdf` | 预览导出 PDF（不保存） |

### 练习模式
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/practice/session` | 开始练习（返回随机题目） |
| POST | `/api/practice/submit` | 提交答案（自动记录错题） |
| GET | `/api/practice/stats` | 获取学习统计 |

### 错题本
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/practice/wrong-questions` | 获取错题本（支持分页） |
| POST | `/api/practice/wrong-questions/<id>/master` | 标记已掌握/取消掌握 |
| POST | `/api/practice/wrong-questions/retry` | 获取错题用于重练 |

### 管理功能
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/grades` | 获取年级列表 |
| GET | `/api/categories` | 获取分类列表 |
| GET | `/api/tags` | 获取所有标签 |
| GET | `/api/stats` | 获取统计数据 |
| GET | `/api/backup/export` | 导出数据库备份 |
| POST | `/api/backup/import` | 导入数据库备份 |
| POST | `/api/ocr` | OCR 图片识别 |
| POST | `/api/cleanup` | 执行文件清理 |

## 📋 页面路由

| 路径 | 说明 |
|------|------|
| `/` | 首页（统计概览） |
| `/login` | 登录页面 |
| `/register` | 注册页面 |
| `/logout` | 退出登录 |
| `/forgot-password` | 忘记密码 |
| `/change-password` | 修改密码 |
| `/manage` | 题库管理 |
| `/upload` | 上传题目 |
| `/question/edit/<id>` | 编辑题目 |
| `/paper-manage` | 试卷管理 |
| `/test` | 智能组卷 |
| `/practice` | 练习模式 |
| `/practice/stats` | 学习统计 |
| `/wrong-questions` | 错题本 |

## 🔧 配置说明

### 开发环境（默认）

```bash
set FLASK_ENV=development
python run.py
```

### 生产环境

```bash
set FLASK_ENV=production
set SECRET_KEY=your-very-long-secret-key    # 必须设置，否则无法启动
set REDIS_URL=redis://localhost:6379/0      # 速率限制存储（推荐）
set RESET_CODE=your-reset-code              # 如需忘记密码功能
python run.py
```

> 💡 生产环境推荐使用 Redis 存储速率限制数据（`REDIS_URL`），避免重启后限流状态丢失。未配置时自动回退到内存存储。

## 🗃️ 数据库

使用 SQLAlchemy ORM 管理 SQLite 数据库，包含以下 6 张表：

| 表名 | 说明 |
|------|------|
| `users` | 用户账户（管理员/教师/学生） |
| `questions` | 题目数据 |
| `papers` | 试卷（PDF/图片） |
| `tests` | 组卷记录 |
| `practice_sessions` | 练习记录（每用户独立） |
| `wrong_questions` | 错题本（每用户独立，累计错误次数） |

数据库文件位于项目根目录 `question_bank.db`，支持通过管理界面一键备份/恢复。

## 📄 许可证

MIT License
