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
│   ├── utils/             # 工具函数（PDF、模板）
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
├── requirements.txt       # Python 依赖
├── docker-compose.yml     # Docker Compose 配置
└── docs/                  # 项目文档
    └── docker-deployment.md
```

## 安装与配置

### 1. 安装依赖

**Windows (PowerShell):**
```powershell
# 后端
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

**Linux / Mac (Bash):**
```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

**Windows (PowerShell):**
```powershell
copy backend\.env.example backend\.env
```

**Linux / Mac (Bash):**
```bash
cp backend/.env.example backend/.env
```

然后编辑 `backend/.env` 文件，配置以下参数：

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `SECRET_KEY` | 应用密钥，用于 JWT 等加密 | 随机字符串（如 `my-secret-key-123`） |
| `DEBUG` | 调试模式 | `true` |
| `ADMIN_PASSWORD` | 管理员默认密码 | `admin123` |
| `RESET_CODE` | 重置密码验证码（留空则禁用） | 可选 |
| `LLM_MODEL_ID` | LLM 模型名称 | `gpt-4o` |
| `LLM_API_KEY` | LLM API 密钥 | 你的 API Key |
| `LLM_BASE_URL` | LLM 服务地址 | `https://api.openai.com/v1` |
| `LLM_TIMEOUT` | LLM 请求超时（秒） | `60` |

> 注意：至少需要配置 `LLM_API_KEY` 才能使用 AI 功能。

### 3. 启动服务

**Windows (PowerShell):**
```powershell
# 后端 (端口 8000)
cd backend
uvicorn main:app --reload --port 8000

# 前端 (端口 5173)
cd frontend
npm run dev
```

**Linux / Mac (Bash):**
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

### 注意事项

- **Python 版本**：建议使用 Python 3.8+
- **Node.js 版本**：建议使用 Node.js 16+
- **端口冲突**：如果端口 8000 或 5173 被占用，可以修改启动命令中的端口号
- **防火墙**：确保防火墙允许访问这些端口

### Docker 部署（推荐）

使用 Docker 可以快速部署，无需手动安装依赖：

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd math-question-bank

# 2. 创建环境变量配置
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入你的配置

# 3. 启动服务
docker compose up -d --build

# 4. 访问应用
# 前端: http://localhost
# API 文档: http://localhost:8000/docs
```

详细 Docker 部署说明请参考 [docs/docker-deployment.md](docs/docker-deployment.md)。

## 功能模块

### 教师端
- 题目管理：增删改查、批量导入、AI 图片识别
- 试卷管理：手动组卷、自动组卷、PDF 导出
- 学生数据：练习统计、错题分析、成绩追踪

### 学生端
- 浏览题库：按年级/知识点/难度筛选
- 在线练习：逐题练习、即时反馈
- 错题本：错题回顾、重新练习
- 个人统计：练习进度、正确率趋势

### AI 功能
- 图片识别：从图片提取数学题目（基于 LLM 视觉识别）
- 智能解析：自动生成答案和解析
- LaTeX 公式渲染：使用 KaTeX 支持数学公式显示
- 题目去重：自动检测并防止重复题目
- 异步处理：后台任务不阻塞界面操作

### 试卷导出
- PDF 导出：支持多种试卷模板
- 模板系统：可自定义试卷样式
- 答案分离：支持题目和答案分开导出

### LaTeX 支持

系统使用 KaTeX 渲染数学公式，支持以下格式：

#### 基本语法

| 格式 | 示例 | 说明 |
|------|------|------|
| 行内公式 | `$a^2+b^2=c^2$` | 公式在文本中显示 |
| 块级公式 | `$$\frac{1}{2}$$` | 公式独占一行 |
| 中文文本 | `$\text{已知}a=2$` | 中文需要用 `\text{}` 包裹 |
| 图片引用 | `{{img:0}}` | 引用题目配图 |

#### 常用数学符号

| 符号 | LaTeX | 说明 |
|------|-------|------|
| 分数 | `\frac{a}{b}` | 分数表示 |
| 根号 | `\sqrt{x}` | 平方根 |
| 上标 | `x^{2}` | 上标 |
| 下标 | `x_{i}` | 下标 |
| 乘号 | `\times` | × |
| 除号 | `\div` | ÷ |
| 正负号 | `\pm` | ± |
| 小于等于 | `\leq` | ≤ |
| 大于等于 | `\geq` | ≥ |
| 不等于 | `\neq` | ≠ |

#### 编辑器工具栏

系统内置 LaTeX 编辑器，提供快捷按钮插入常用符号：
- 公式包裹：`$...$`
- 中文包裹：`\text{...}`
- 分数、根号、上标、下标
- 常用数学符号

> 💡 **提示**：系统会自动处理双反斜杠转义，输入 `\\text` 和 `\text` 效果相同

## 配置说明

### LLM 配置 (.env)

```bash
# 支持 OpenAI 兼容 API
LLM_MODEL_ID=gpt-4o
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
```

## 许可证

本项目采用自定义使用许可协议，详见 [LICENSE](LICENSE) 文件。

### 许可证要点

- **非商业使用**：免费授权用于个人学习、教育、非营利组织等非商业用途
- **商业使用**：必须事先联系作者获取书面授权
- **禁止行为**：未经授权的商业使用、去除许可协议、侵犯知识产权

### 商业授权申请

如需商业使用本软件，请联系作者：
- 作者：Brilliant
- 联系方式：[3461222397@qq.com]or[202230127106@hunnu.edu.cn]

详见 [LICENSE](LICENSE) 文件获取完整条款。




