"""AI 提示词配置"""

# 题目提取提示词（完整版，包含答案解析生成）
EXTRACT_PROMPT = """识别图片中的数学题，返回JSON数组。同时为每道题生成答案和解析。

每道题包含：
- content: 题干+选项（如有图用{{img:0}}引用，中文用$\\text{}$包裹，公式用$$包裹）
- image_descriptions: 图的描述数组
- image_regions: 图在原图的位置[x1,y1,x2,y2]，0-1比例值，无图返回[]
- answer_analysis: 答案和解析（格式：$\\text{答案}$\\n---解析---\\n$\\text{解析}$）
- difficulty: 1简单/2中等/3困难
- category: 几何/代数/函数等

规则：
1. 识别所有独立题目，必须包含完整选项A/B/C/D
2. 每题的图只属于该题，精确定位图片区域
3. **必须为每道题生成完整的答案和解析**
4. **解析要简洁精炼，直接给出关键解题步骤，不要输出思考过程**
5. 解析长度控制在200字以内，只保留核心推导

返回格式示例：
[{"content":"如图{{img:0}}，在$\\text{三角形}ABC$中...\\nA.选项1\\nB.选项2\\nC.选项3\\nD.选项4","image_descriptions":["描述"],"image_regions":[[0.1,0.2,0.4,0.5]],"answer_analysis":"$\\text{答案}$：B\\n---解析---\\n$\\text{根据题意，由垂直平分线性质可得...}$","difficulty":2,"category":"几何"}]

只返回JSON，不要包含任何解释或思考过程"""


# 答案解析生成提示词
ANALYSIS_PROMPT = """根据题目生成答案和解析。

题目：{content}
图片描述：{image_descriptions}

规则：
1. 中文用$\\text{}$包裹
2. 答案和解析用---解析---分隔
3. 无图时省略image_descriptions
4. **解析要简洁精炼，只给出关键解题步骤，控制在200字以内**
5. **不要输出思考过程，直接给出最终答案和简洁解析**

返回格式：{{"answer_analysis":"$\\text{答案}$\\n---解析---\\n$\\text{解析}$"}}

只返回JSON，不要包含任何解释或思考过程"""


# 知识点提取提示词（可选）
KNOWLEDGE_POINTS_PROMPT = """提取题目涉及的知识点。

返回格式：{{"knowledge_points":["知识点1","知识点2"]}}

只返回JSON"""


# 难度评估提示词（可选）
DIFFICULTY_PROMPT = """评估题目难度(1简单/2中等/3困难)。

返回格式：{{"difficulty":1,"reason":"理由"}}

只返回JSON"""
