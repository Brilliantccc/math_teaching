"""结构化上下文协议 - 参考helloagents-trip-planner的PlannerContext设计"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentContext(BaseModel):
    """Agent执行上下文"""
    agent_name: str
    task: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowContext(BaseModel):
    """工作流上下文 - 结构化协议"""
    task: str
    task_type: str = "unknown"  # question_parse, analysis, test_generation等
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # 输入数据
    input_data: Dict[str, Any] = Field(default_factory=dict)

    # Agent执行上下文
    agent_contexts: Dict[str, AgentContext] = Field(default_factory=dict)

    # 共享数据
    shared_data: Dict[str, Any] = Field(default_factory=dict)

    # 输出数据
    output_data: Dict[str, Any] = Field(default_factory=dict)

    # 状态跟踪
    status: str = "pending"
    errors: List[str] = Field(default_factory=list)

    def get_agent_context(self, agent_name: str) -> Optional[AgentContext]:
        """获取Agent上下文"""
        return self.agent_contexts.get(agent_name)

    def set_agent_context(self, agent_name: str, context: AgentContext):
        """设置Agent上下文"""
        self.agent_contexts[agent_name] = context

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.shared_data.get(key, default)

    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_data[key] = value

    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task": self.task,
            "task_type": self.task_type,
            "created_at": self.created_at,
            "input_data": self.input_data,
            "agent_contexts": {
                name: ctx.dict() for name, ctx in self.agent_contexts.items()
            },
            "shared_data": self.shared_data,
            "output_data": self.output_data,
            "status": self.status,
            "errors": self.errors,
        }


class ContextCompressor:
    """上下文压缩器 - 参考helloagents的compact_for_planner"""

    @staticmethod
    def compact_question_parse_context(context: WorkflowContext) -> Dict[str, Any]:
        """压缩题目解析上下文"""
        input_data = context.input_data
        return {
            "version": "question_parse_context",
            "task": context.task,
            "task_type": context.task_type,
            "content": ContextCompressor._truncate_text(input_data.get("content", ""), 500),
            "image_descriptions": input_data.get("image_descriptions", [])[:5],
            "source": input_data.get("source", "manual"),
        }

    @staticmethod
    def compact_analysis_context(context: WorkflowContext) -> Dict[str, Any]:
        """压缩分析上下文"""
        input_data = context.input_data
        question = input_data.get("question", {})
        return {
            "version": "analysis_context",
            "task": context.task,
            "task_type": context.task_type,
            "question_id": question.get("id"),
            "content": ContextCompressor._truncate_text(question.get("content", ""), 300),
            "answer": ContextCompressor._truncate_text(question.get("answer", ""), 200),
            "knowledge_points": question.get("knowledge_points", [])[:10],
            "include_similar": input_data.get("include_similar", True),
        }

    @staticmethod
    def compact_test_generation_context(context: WorkflowContext) -> Dict[str, Any]:
        """压缩试卷生成上下文"""
        input_data = context.input_data
        questions = input_data.get("questions", [])
        return {
            "version": "test_generation_context",
            "task": context.task,
            "task_type": context.task_type,
            "title": input_data.get("title", "数学试卷"),
            "question_count": len(questions),
            "questions_summary": [
                {
                    "id": q.get("id"),
                    "content_preview": ContextCompressor._truncate_text(q.get("content", ""), 50),
                    "difficulty": q.get("difficulty"),
                }
                for q in questions[:20]
            ],
            "total_score": input_data.get("total_score", 100),
        }

    @staticmethod
    def compact(context: WorkflowContext) -> Dict[str, Any]:
        """根据任务类型压缩上下文"""
        compressors = {
            "question_parse": ContextCompressor.compact_question_parse_context,
            "analysis": ContextCompressor.compact_analysis_context,
            "test_generation": ContextCompressor.compact_test_generation_context,
        }

        compressor = compressors.get(context.task_type)
        if compressor:
            return compressor(context)

        # 默认压缩
        return {
            "version": "default_context",
            "task": context.task,
            "task_type": context.task_type,
            "input_data": context.input_data,
        }

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        """截断文本"""
        if len(text) <= max_chars:
            return text
        return f"{text[:max_chars]}..."


class ContextBuilder:
    """上下文构建器"""

    @staticmethod
    def build_question_parse_context(
        content: str,
        image_descriptions: Optional[List[str]] = None,
        source: str = "manual",
    ) -> WorkflowContext:
        """构建题目解析上下文"""
        return WorkflowContext(
            task="解析数学题目",
            task_type="question_parse",
            input_data={
                "content": content,
                "image_descriptions": image_descriptions or [],
                "source": source,
            },
        )

    @staticmethod
    def build_question_upload_context(
        content: str,
        image_descriptions: Optional[List[str]] = None,
        source: str = "manual",
    ) -> WorkflowContext:
        """构建题目上传上下文（兼容旧接口）"""
        return ContextBuilder.build_question_parse_context(content, image_descriptions, source)

    @staticmethod
    def build_test_generation_context(
        question_ids: List[int],
        title: str = "数学试卷",
        total_score: int = 100,
    ) -> WorkflowContext:
        """构建试卷生成上下文"""
        return WorkflowContext(
            task="生成数学试卷",
            task_type="test_generation",
            input_data={
                "question_ids": question_ids,
                "title": title,
                "total_score": total_score,
            },
        )

    @staticmethod
    def build_analysis_context(
        question: Dict[str, Any],
        include_similar: bool = True,
    ) -> WorkflowContext:
        """构建题目分析上下文"""
        return WorkflowContext(
            task="分析数学题目",
            task_type="analysis",
            input_data={
                "question": question,
                "include_similar": include_similar,
            },
        )

    @staticmethod
    def build_multi_agent_context(
        task: str,
        task_type: str = "general",
        **kwargs,
    ) -> WorkflowContext:
        """构建多Agent协作上下文"""
        return WorkflowContext(
            task=task,
            task_type=task_type,
            input_data=kwargs,
        )


# 全局上下文构建器
context_builder = ContextBuilder()
context_compressor = ContextCompressor()


class ContextDebugger:
    """上下文调试器 - 参考helloagents的print_summary和print_visualization"""

    @staticmethod
    def print_summary(context: WorkflowContext) -> None:
        """打印上下文摘要"""
        print(f"\n{'='*60}")
        print(f"Context 摘要")
        print(f"{'='*60}")
        print(f"任务: {context.task}")
        print(f"任务类型: {context.task_type}")
        print(f"创建时间: {context.created_at}")
        print(f"状态: {context.status}")

        # 输入数据摘要
        input_data = context.input_data
        print(f"\n输入数据:")
        for key, value in input_data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  - {key}: {value[:100]}...")
            elif isinstance(value, list):
                print(f"  - {key}: [{len(value)} items]")
            else:
                print(f"  - {key}: {value}")

        # 共享数据摘要
        if context.shared_data:
            print(f"\n共享数据:")
            for key, value in context.shared_data.items():
                print(f"  - {key}: {value}")

        # 输出数据摘要
        if context.output_data:
            print(f"\n输出数据:")
            for key, value in context.output_data.items():
                if isinstance(value, dict):
                    print(f"  - {key}: {{...}}")
                else:
                    print(f"  - {key}: {value}")

        # 错误信息
        if context.errors:
            print(f"\n错误:")
            for error in context.errors:
                print(f"  - {error}")

        print(f"{'='*60}\n")

    @staticmethod
    def print_visualization(context: WorkflowContext, limit: int = 8) -> None:
        """打印上下文明细"""
        print(f"\n{'='*60}")
        print(f"Context 明细预览")
        print(f"{'='*60}")

        # 根据任务类型打印不同内容
        if context.task_type == "question_parse":
            ContextDebugger._print_question_parse_detail(context, limit)
        elif context.task_type == "analysis":
            ContextDebugger._print_analysis_detail(context, limit)
        elif context.task_type == "test_generation":
            ContextDebugger._print_test_generation_detail(context, limit)
        else:
            ContextDebugger._print_general_detail(context, limit)

        print(f"{'='*60}\n")

    @staticmethod
    def _print_question_parse_detail(context: WorkflowContext, limit: int) -> None:
        """打印题目解析明细"""
        input_data = context.input_data
        content = input_data.get("content", "")
        image_descriptions = input_data.get("image_descriptions", [])

        print(f"\n题目内容:")
        print(f"  - 长度: {len(content)} 字符")
        print(f"  - 预览: {content[:200]}...")

        if image_descriptions:
            print(f"\n图片描述: {len(image_descriptions)} 张")
            for i, desc in enumerate(image_descriptions[:limit], 1):
                print(f"  - #{i}: {desc[:80]}...")

    @staticmethod
    def _print_analysis_detail(context: WorkflowContext, limit: int) -> None:
        """打印分析明细"""
        input_data = context.input_data
        question = input_data.get("question", {})

        print(f"\n题目信息:")
        print(f"  - ID: {question.get('id')}")
        print(f"  - 内容: {question.get('content', '')[:100]}...")
        print(f"  - 知识点: {question.get('knowledge_points', [])[:5]}")

    @staticmethod
    def _print_test_generation_detail(context: WorkflowContext, limit: int) -> None:
        """打印试卷生成明细"""
        input_data = context.input_data
        questions = input_data.get("questions", [])

        print(f"\n试卷信息:")
        print(f"  - 标题: {input_data.get('title')}")
        print(f"  - 题目数量: {len(questions)}")
        print(f"  - 总分: {input_data.get('total_score')}")

        print(f"\n题目预览:")
        for i, q in enumerate(questions[:limit], 1):
            print(f"  - #{i} {q.get('content', '')[:50]}...")

    @staticmethod
    def _print_general_detail(context: WorkflowContext, limit: int) -> None:
        """打印通用明细"""
        print(f"\n输入数据:")
        for key, value in context.input_data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  - {key}: {value[:100]}...")
            elif isinstance(value, list):
                print(f"  - {key}: [{len(value)} items]")
            else:
                print(f"  - {key}: {value}")


# 全局调试器
context_debugger = ContextDebugger()
