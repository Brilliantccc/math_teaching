"""基础Agent类"""

import time
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.state import WorkflowState, AgentResult, AgentStatus
from backend.agents.tools import get_all_tools


# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒
RETRY_BACKOFF = 2  # 指数退避倍数


class BaseAgent:
    """基础Agent类"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        max_retries: int = MAX_RETRIES,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm
        self.tools = tools or get_all_tools()
        self.max_retries = max_retries
        self.last_error: Optional[str] = None
        self.retry_count: int = 0

    def _init_llm(self):
        """初始化LLM（延迟加载）"""
        if self.llm is None:
            from langchain_openai import ChatOpenAI
            from backend.config import settings

            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL_ID or "gpt-3.5-turbo",
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
                temperature=0.3,
            )

    def run(self, task: str, state: WorkflowState) -> AgentResult:
        """执行任务（带重试机制）

        Args:
            task: 任务描述
            state: 工作流状态

        Returns:
            AgentResult: 执行结果
        """
        self._init_llm()
        self.retry_count = 0
        self.last_error = None

        for attempt in range(self.max_retries):
            try:
                # 构建消息
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=self._build_task_prompt(task, state, attempt))
                ]

                # 调用LLM
                response = self.llm.invoke(messages)
                output = response.content

                # 解析输出并生成结果
                result = self._parse_output(output, state)
                result.retry_count = attempt

                print(f"✅ {self.name} 第 {attempt + 1} 次执行成功")
                return result

            except Exception as e:
                self.retry_count = attempt + 1
                self.last_error = str(e)
                delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)

                print(f"⚠️  {self.name} 第 {attempt + 1} 次执行失败: {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"   {delay}秒后重试...")
                    time.sleep(delay)

        # 所有重试都失败
        print(f"❌ {self.name} 执行失败，已重试 {self.max_retries} 次")
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            errors=[f"执行失败（重试{self.max_retries}次后）: {self.last_error}"],
            retry_count=self.retry_count
        )

    def run_with_fallback(
        self,
        task: str,
        state: WorkflowState,
        fallback_output: Optional[str] = None
    ) -> AgentResult:
        """执行任务（带重试和Fallback）

        Args:
            task: 任务描述
            state: 工作流状态
            fallback_output: 失败时的降级输出

        Returns:
            AgentResult: 执行结果
        """
        result = self.run(task, state)

        if result.status == AgentStatus.FAILED and fallback_output:
            print(f"⚠️  {self.name} 使用Fallback方案")
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                output=fallback_output,
                errors=[f"原任务失败，使用Fallback: {self.last_error}"],
                retry_count=self.retry_count
            )

        return result

    def _build_task_prompt(self, task: str, state: WorkflowState, attempt: int = 0) -> str:
        """构建任务提示"""
        retry_hint = ""
        if attempt > 0:
            retry_hint = f"\n\n注意：这是第 {attempt + 1} 次尝试，请仔细检查输出格式。"

        prompt = f"""任务: {task}

当前状态:
- 已完成的Agent: {state.completed_agents}
- 共享上下文: {state.shared_context}

请根据你的职责执行任务。如果需要修改文件，请使用工具完成。

重要规则:
1. 只修改你负责的文件
2. 保持代码风格一致
3. 遵循项目架构规范
4. 完成后返回修改的文件列表
{retry_hint}
"""
        return prompt

    def _parse_output(self, output: str, state: WorkflowState) -> AgentResult:
        """解析LLM输出"""
        # 简单解析，实际项目中可以更复杂
        files_modified = []

        # 尝试从输出中提取修改的文件
        import re
        file_patterns = [
            r'(?:修改|创建|写入)(?:了)?文件[:：]\s*(.+?)(?:\n|$)',
            r'(?:Modified|Created|Updated)\s+files?:\s*(.+?)(?:\n|$)',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                files = [f.strip() for f in match.split(',')]
                files_modified.extend(files)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            files_modified=files_modified
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"
