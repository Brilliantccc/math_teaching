# 数学题库管理系统

面向初高中数学的教学资源管理平台，为教师提供题目管理、试卷组卷、在线练习等功能。

## ✨ 功能特性

### 🔐 安全机制
- 用户认证登录系统
- **忘记密码** - 通过重置码恢复访问权限（需配置 `RESET_CODE` 环境变量）
- **修改密码** - 登录后可随时修改密码
- CSRF 跨站请求伪造防护
- XSS 跨站脚本攻击防护
- API 请求速率限制
- 安全的数据库备份导入验证
- 生产环境强制要求设置 `SECRET_KEY`，密码重置码无硬编码默认值

### 📝 题目管理
- 支持图片上传，自动 OCR 识别题目内容
- 支持 LaTeX 数学公式编辑，实时预览
- 按年级（初一至高三）、知识点、难度分类管理
- 答案与解析分离录入
- **题目编辑功能** - 随时修改已有题目
- **批量操作** - 批量删除、批量修改年级
- **JSON 导入导出** - 题目数据备份与迁移

### 📄 试卷管理
- 支持 PDF / 图片格式试卷上传
- 支持上传答案 PDF，一键下载
- 试卷列表展示与管理

### 🎯 智能组卷
- 按年级、知识点、难度随机抽题
- **拖拽排序** - 手动调整题目顺序
- 导出 PDF 格式试卷（含答案）

### 📊 练习模式
- 按条件随机出题
- 即时判分与答案展示
- **练习统计** - 正确率、知识点分析、最近记录

### 📖 错题本
- 自动收集练习中答错的题目
- 按年级、知识点、难度筛选错题
- 显示答错次数与最近错误答案
- 支持在错题本内直接重新练习

### ⚡ 性能优化
- 数据库索引（年级、分类、难度、试卷ID等常用查询字段）
- 批量获取题目接口，避免 N+1 逐题请求
- 试卷列表子查询统计题目数量
- PDF 导出后自动清理临时文件

### 💾 数据安全
- 数据库一键备份导出
- 支持从备份文件恢复数据（带验证）
- 自动清理孤立文件

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, Flask 3.0 |
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
│   ├── models.py             # 数据库模型与操作
│   ├── cleanup.py            # 文件清理模块
│   └── routes/               # 蓝图路由
│       ├── questions.py      # 题目管理 API
│       ├── papers.py         # 试卷管理 API
│       ├── tests.py          # 组卷管理 API
│       ├── practice.py       # 练习模式 API
│       └── admin.py          # 管理功能 API
├── auth.py                   # 用户认证模块
├── config.py                 # 配置文件
├── run.py                    # 应用入口
├── app.py                    # 遗留入口（已迁移至 Blueprint 架构）
├── ocr.py                    # OCR 文字识别模块
├── pdf_utils.py              # PDF 读取/生成工具
├── requirements.txt          # Python 依赖
├── static/
│   ├── css/style.css         # 样式文件
│   ├── js/app.js             # 前端公共脚本
│   └── uploads/              # 上传文件存储
└── templates/                # Jinja2 模板
    ├── base.html             # 基础布局
    ├── login.html            # 登录页面
    ├── forgot_password.html  # 忘记密码页面
    ├── change_password.html  # 修改密码页面
    ├── index.html            # 首页
    ├── upload.html           # 上传题目
    ├── manage.html           # 题库管理
    ├── question_edit.html    # 题目编辑
    ├── paper_manage.html     # 试卷管理
    ├── test.html             # 智能组卷
    ├── practice.html         # 练习模式
    ├── practice_stats.html   # 练习统计
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

### 2. 环境变量配置

```bash
# 设置密钥（生产环境必须，开发环境可省略）
set SECRET_KEY=your-secret-key

# 设置 OCR 路径（可选）
set TESSERACT_PATH=D:\Tesseract-OCR\tesseract.exe

# 设置字体路径（可选）
set FONT_PATH=C:\Windows\Fonts\msyh.ttc

# 设置密码重置码（如需使用忘记密码功能则必须配置）
set RESET_CODE=your-reset-code
```

### 3. 启动服务

```bash
python run.py
```

访问 http://localhost:5000

### 4. 默认登录

- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次登录后请修改默认密码！

## 🔑 密码管理

### 修改密码

1. 登录后，点击导航栏的"修改密码"
2. 输入原密码和新密码
3. 确认修改

### 忘记密码

1. 在登录页面点击"忘记密码？"
2. 输入重置码（需通过 `RESET_CODE` 环境变量预先配置）
3. 设置新密码

## 📡 API 接口

### 认证
所有 API 需要登录认证，通过 `X-CSRFToken` 头部传递 CSRF token。

### 题目管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions` | 获取题目列表（支持筛选分页） |
| GET | `/api/questions/batch?ids=` | 批量获取题目 |
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
| POST | `/api/papers` | 上传试卷 |
| GET | `/api/papers/<id>/download` | 下载试卷 PDF |
| POST | `/api/papers/<id>/answer` | 上传答案 PDF |

### 组卷管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tests` | 获取组卷列表 |
| POST | `/api/tests` | 创建组卷 |
| POST | `/api/tests/auto` | 自动生成组卷 |
| GET | `/api/tests/<id>/pdf` | 导出组卷 PDF |

### 练习模式
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/practice/session` | 开始练习 |
| POST | `/api/practice/submit` | 提交答案 |
| GET | `/api/practice/stats` | 获取练习统计 |
| GET | `/api/practice/wrong-questions` | 获取错题本（支持筛选分页） |

### 管理功能
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/backup/export` | 导出数据库备份 |
| POST | `/api/backup/import` | 导入数据库备份 |
| POST | `/api/ocr` | OCR 图片识别 |
| POST | `/api/cleanup` | 执行文件清理 |

## 📋 页面路由

| 路径 | 说明 |
|------|------|
| `/` | 首页 |
| `/login` | 登录页面 |
| `/logout` | 退出登录 |
| `/forgot-password` | 忘记密码 |
| `/change-password` | 修改密码 |
| `/manage` | 题库管理 |
| `/upload` | 上传题目 |
| `/question/edit/<id>` | 编辑题目 |
| `/paper-manage` | 试卷管理 |
| `/test` | 智能组卷 |
| `/practice` | 练习模式 |
| `/practice/stats` | 练习统计 |
| `/wrong-questions` | 错题本 |

## 🔧 配置说明

### 开发环境

```bash
set FLASK_ENV=development
python run.py
```

### 生产环境

```bash
set FLASK_ENV=production
set SECRET_KEY=your-very-long-secret-key    # 必须设置，否则无法启动
set RESET_CODE=your-reset-code              # 如需忘记密码功能
python run.py
```

## 📄 许可证

MIT License
