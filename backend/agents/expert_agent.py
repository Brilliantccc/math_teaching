"""专家Agent - 参考helloagents-trip-planner的单一Agent设计

设计思路：
- 单一专家Agent + 结构化上下文（类似PlannerContext）
- 工具快照并行获取，减少AI幻觉
- 上下文压缩，只保留关键信息
"""

import time
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.base import BaseAgent
from backend.agents.state import WorkflowState, AgentResult, AgentStatus
from backend.agents.context import WorkflowContext


# 专家Agent提示词
EXPERT_AGENT_PROMPT = """你是数学题库管理系统专家。你的任务是根据结构化上下文（Context）执行任务。

**核心原则：**
1. 只基于Context中的信息执行任务，不要编造数据
2. 严格按照输出格式要求返回结果
3. 如果Context信息不足，明确说明缺少什么

**输出要求：**
- 只输出JSON对象，不要输出Markdown、代码块标记或解释
- 第一个非空字符必须是 {，最后一个非空字符必须是 }
"""


class ExpertAgent:
    """专家Agent - 单一Agent + 结构化上下文"""

    def __init__(
        self,
        name: str = "数学题库专家",
        max_retries: int = 3,
    ):
        self.name = name
        self.max_retries = max_retries
        self.llm = None
        self.last_error: Optional[str] = None

    def _init_llm(self):
        """初始化LLM"""
        if self.llm is None:
            from langchain_openai import ChatOpenAI
            from backend.config import settings

            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL_ID or "gpt-3.5-turbo",
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
                temperature=0.3,
            )

    def run(self, context: WorkflowContext) -> AgentResult:
        """执行任务（基于结构化上下文）

        Args:
            context: 结构化上下文

        Returns:
            AgentResult: 执行结果
        """
        self._init_llm()
        self.last_error = None

        print(f"\n{'='*60}")
        print(f"🤖 {self.name} 开始执行...")
        print(f"任务类型: {context.task_type}")
        print(f"{'='*60}\n")

        for attempt in range(self.max_retries):
            try:
                # 构建任务提示
                task_prompt = self._build_task_prompt(context, attempt)

                # 调用LLM
                messages = [
                    SystemMessage(content=EXPERT_AGENT_PROMPT),
                    HumanMessage(content=task_prompt)
                ]

                start_time = time.perf_counter()
                response = self.llm.invoke(messages)
                elapsed = time.perf_counter() - start_time

                output = response.content
                print(f"✅ {self.name} 第 {attempt + 1} 次执行成功 (耗时: {elapsed:.2f}秒)")

                # 解析输出
                result = self._parse_output(output, context)
                result.retry_count = attempt

                return result

            except Exception as e:
                self.last_error = str(e)
                print(f"⚠️  {self.name} 第 {attempt + 1} 次执行失败: {str(e)}")

                if attempt < self.max_retries - 1:
                    import time as t
                    t.sleep(1 * (2 ** attempt))  # 指数退避

        print(f"❌ {self.name} 执行失败，已重试 {self.max_retries} 次")
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            errors=[f"执行失败（重试{self.max_retries}次后）: {self.last_error}"],
            retry_count=self.max_retries,
        )

    def _build_task_prompt(self, context: WorkflowContext, attempt: int = 0) -> str:
        """构建任务提示"""
        retry_hint = ""
        if attempt > 0:
            retry_hint = f"\n\n注意：这是第 {attempt + 1} 次尝试，请仔细检查输出格式。"

        # 根据任务类型构建不同的提示
        if context.task_type == "question_parse":
            return self._build_question_parse_prompt(context, retry_hint)
        elif context.task_type == "analysis":
            return self._build_analysis_prompt(context, retry_hint)
        elif context.task_type == "test_generation":
            return self._build_test_generation_prompt(context, retry_hint)
        else:
            return self._build_general_prompt(context, retry_hint)

    def _build_question_parse_prompt(self, context: WorkflowContext, retry_hint: str) -> str:
        """构建题目解析提示"""
        content = context.input_data.get("content", "")
        image_descriptions = context.input_data.get("image_descriptions", [])

        prompt = f"""任务：解析数学题目

题目内容：
{content}

"""
        if image_descriptions:
            prompt += f"""图片描述：
{chr(10).join(f'- {desc}' for desc in image_descriptions)}

"""

        prompt += """请解析题目并返回JSON格式：
{
  "content": "题目内容（保留LaTeX格式）",
  "answer": "答案",
  "analysis": "解题思路",
  "knowledge_points": ["知识点1", "知识点2"],
  "difficulty": "easy/medium/hard",
  "question_type": "选择题/填空题/解答题"
}
""" + retry_hint

        return prompt

    def _build_analysis_prompt(self, context: WorkflowContext, retry_hint: str) -> str:
        """构建题目分析提示"""
        question = context.input_data.get("question", {})
        include_similar = context.input_data.get("include_similar", True)

        prompt = f"""任务：分析数学题目

题目信息：
- 内容：{question.get('content', '')}
- 答案：{question.get('answer', '')}
- 知识点：{question.get('knowledge_points', [])}

请分析题目并返回JSON格式：
{{
  "analysis": "详细解题思路",
  "key_points": ["关键点1", "关键点2"],
  "common_mistakes": ["常见错误1", "常见错误2"],
  "difficulty_analysis": "难度分析",
  "learning_suggestions": ["学习建议1", "学习建议2"]
}}""" + retry_hint

        return prompt

    def _build_test_generation_prompt(self, context: WorkflowContext, retry_hint: str) -> str:
        """构建试卷生成提示"""
        questions = context.input_data.get("questions", [])
        title = context.input_data.get("title", "数学试卷")

        prompt = f"""任务：生成数学试卷

试卷标题：{title}
题目数量：{len(questions)}道

题目列表：
"""
        for i, q in enumerate(questions, 1):
            prompt += f"{i}. {q.get('content', '')[:50]}...\n"

        prompt += f"""
请生成试卷结构并返回JSON格式：
{{
  "title": "{title}",
  "sections": [
    {{
      "name": "选择题",
      "questions": [1, 2, 3],
      "score_per_question": 5
    }},
    {{
      "name": "填空题",
      "questions": [4, 5],
      "score_per_question": 10
    }}
  ],
  "total_score": 100,
  "time_limit": 120
}}""" + retry_hint

        return prompt

    def _build_general_prompt(self, context: WorkflowContext, retry_hint: str) -> str:
        """构建通用提示"""
        return f"""任务：{context.task}

输入数据：
{context.input_data}

共享数据：
{context.shared_data}

请根据任务要求执行并返回结果。""" + retry_hint

    def _parse_output(self, output: str, context: WorkflowContext) -> AgentResult:
        """解析LLM输出"""
        import json
        import re

        # 尝试解析JSON
        try:
            # 清理输出
            output = output.strip()

            # 尝试直接解析
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                # 尝试从代码块中提取
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
                if json_match:
                    data = json.loads(json_match.group(1).strip())
                else:
                    # 尝试找到JSON对象
                    start = output.find("{")
                    end = output.rfind("}") + 1
                    if start != -1 and end > start:
                        data = json.loads(output[start:end])
                    else:
                        raise ValueError("无法解析JSON")

            # 存储到上下文
            context.output_data[context.task_type] = data

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                output=json.dumps(data, ensure_ascii=False, indent=2),
                metadata={"parsed_data": data}
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                output=output,
                errors=[f"解析失败: {str(e)}"]
            )


# 全局实例
expert_agent = ExpertAgent()
