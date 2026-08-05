"""AI 提示词配置"""

# 题目提取提示词（精简版，提升速度）
EXTRACT_PROMPT = """识别数学题，返回JSON数组。

字段：
- content: 题干+选项（图用{{img:N}}，中文用$\text{}$，公式用$$）
- image_descriptions: 图描述数组，无图返回[]
- answer_analysis: 答案和解析（格式：$\text{答案}$---解析---$\text{解析}$）
- difficulty: 1简单/2中等/3困难
- question_type: 单项选择/多项选择/填空题/解答题/判断题/计算题

规则：
1. 识别所有独立题目，选择题必须有完整A/B/C/D选项
2. {{img:N}}放在图片描述内容位置（通常在题干末尾、选项前）
3. 必须为每题生成答案解析，解析简洁（200字内），直接给关键步骤
4. 题型判断：单选→一个正确答案，多选→多个正确答案，填空→有空格，解答→证明/求解，判断→对错，计算→纯计算

示例：
[{"content":"在$\triangle ABC$中，$AB=5$，$BC=12$，$AC=13$。求面积。\\n{{img:0}}\\nA.30\\nB.60\\nC.78\\nD.156","image_descriptions":["直角三角形"],"answer_analysis":"$\text{答案}$：A---解析---$\text{由}5^2+12^2=13^2\text{知为直角三角形，面积}=\frac{1}{2}\times5\times12=30$","difficulty":2,"question_type":"单项选择"}]

只返回JSON"""


# 答案解析生成提示词
ANALYSIS_PROMPT = """根据题目生成答案和解析。

题目：{content}
图片描述：{image_descriptions}

规则：
1. 中文用$\text{}$包裹
2. 答案和解析用---解析---分隔
3. 无图时图片描述为空
4. **解析要简洁精炼，只给出关键解题步骤，控制在200字以内**
5. **不要输出思考过程，直接给出最终答案和简洁解析**

返回格式：{{"answer_analysis":"$\text{答案}$---解析---$\text{解析}$"}}

只返回JSON，不要包含任何解释或思考过程"""


# 难度评估提示词（可选）
DIFFICULTY_PROMPT = """评估题目难度(1简单/2中等/3困难)。

返回格式：{{"difficulty":1,"reason":"理由"}}

只返回JSON"""
