# 数学题库管理系统

面向中国初高中的数学题库管理系统，支持教师管理题目、组卷、查看学生数据，学生在线练习、错题回顾、成绩追踪。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Ant Design Vue |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | SQLite (aiosqlite) |
| 认证 | JWT Token |

## 项目结构

```
math-question-bank/
├── backend/                # FastAPI 后端
│   ├── api/               # API 路由
│   │   ├── auth.py        # 认证接口
│   │   ├── questions.py   # 题目管理
│   │   ├── papers.py      # 试卷管理
│   │   ├── tests.py       # 组卷功能
│   │   ├── practice.py    # 练习功能
│   │   ├── admin.py       # 管理功能
│   │   ├── student_data.py # 学生数据
│   │   └── llm.py         # AI 功能
│   ├── models/            # SQLAlchemy 模型
│   ├── schemas/           # Pydantic 数据模型
│   ├── core/              # 核心模块（认证、依赖注入）
│   ├── services/          # 业务服务（LLM）
│   ├── utils/             # 工具函数（OCR、PDF）
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   └── main.py            # 应用入口
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # Axios 封装
│   │   ├── components/    # 公共组件
│   │   ├── views/         # 页面组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── router/        # Vue Router
│   │   └── types/         # TypeScript 类型
│   └── vite.config.ts     # Vite 配置
├── DESIGN.md              # 设计系统文档
├── PRODUCT.md             # 产品需求文档
└── requirements.txt       # Python 依赖
```

## 快速开始

### 1. 安装依赖

```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、LLM 等
```

### 3. 启动服务

```bash
# 后端 (端口 8000)
cd backend
uvicorn main:app --reload --port 8000

# 前端 (端口 5173)
cd frontend
npm run dev
```

### 4. 访问系统

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8000/docs | API 文档 (Swagger) |

默认管理员：`admin` / `admin123`

## 功能模块

### 教师端
- 题目管理：增删改查、批量导入、OCR 识别
- 试卷管理：手动组卷、自动组卷、PDF 导出
- 学生数据：练习统计、错题分析、成绩追踪

### 学生端
- 浏览题库：按年级/知识点/难度筛选
- 在线练习：逐题练习、即时反馈
- 错题本：错题回顾、重新练习
- 个人统计：练习进度、正确率趋势

### AI 功能
- 图片识别：从图片提取数学题目
- 智能解析：自动生成答案和解析

## 配置说明

### LLM 配置 (.env)

```bash
# 支持 OpenAI 兼容 API
LLM_MODEL_ID=gpt-4o
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
```

### OCR 配置

需要安装 [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)

```bash
TESSERACT_PATH=/path/to/tesseract
```
