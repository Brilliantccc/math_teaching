"""后端API专家Agent"""

from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel

from backend.agents.base import BaseAgent
from backend.agents.state import WorkflowState, AgentResult, AgentStatus


API_SYSTEM_PROMPT = """你是一个后端API专家，专注于FastAPI端点开发和业务逻辑实现。

你的职责:
1. 设计和实现 RESTful API 端点 (api/*.py)
2. 实现业务逻辑服务 (services/*.py)
3. 集成LLM服务 (services/llm_service.py)
4. 处理认证和权限 (core/deps.py)

项目架构:
- FastAPI 异步框架
- SQLAlchemy 异步ORM
- JWT 认证
- LLM 集成 (OpenAI兼容API)

代码规范:
1. 使用 async/await 异步编程
2. 使用 Depends 依赖注入
3. 使用 Pydantic 进行数据验证
4. 添加适当的错误处理
5. 编写清晰的API文档

工作流程:
1. 分析需求，确定API端点
2. 修改 api/*.py 文件
3. 实现 services/*.py 业务逻辑
4. 更新认证和权限控制
5. 验证代码语法正确性

完成后，返回修改的文件列表和API规范。
"""


class APIAgent(BaseAgent):
    """后端API专家Agent"""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        super().__init__(
            name="api_expert",
            system_prompt=API_SYSTEM_PROMPT,
            llm=llm,
            tools=tools,
        )

    def _build_task_prompt(self, task: str, state: WorkflowState) -> str:
        """构建任务提示"""
        # 获取数据模型信息
        data_model_files = state.get_shared_data("data_model_files", [])
        data_models = state.get_shared_data("data_models", "")

        prompt = f"""任务: {task}

你需要完成以下工作:
1. 分析需求，确定API端点设计
2. 修改或创建 api/*.py 文件
3. 实现 services/*.py 业务逻辑
4. 更新认证和权限控制

{f'数据模型文件:\n{chr(10).join(data_model_files)}' if data_model_files else ''}

{f'数据模型定义:\n{data_models}' if data_models else ''}

重要规则:
1. 只修改 backend/api/ 和 backend/services/ 目录下的文件
2. 保持RESTful API设计规范
3. 使用异步编程模式
4. 添加适当的错误处理和验证
5. 编写清晰的API文档

API端点设计规范:
- GET /api/resources - 获取列表
- GET /api/resources/{id} - 获取单个
- POST /api/resources - 创建
- PUT /api/resources/{id} - 更新
- DELETE /api/resources/{id} - 删除

完成后，请列出所有修改的文件和API规范。
"""
        return prompt

    def _parse_output(self, output: str, state: WorkflowState) -> AgentResult:
        """解析输出并更新共享状态"""
        import re

        files_modified = []

        # 提取修改的文件
        file_patterns = [
            r'backend/api/\w+\.py',
            r'backend/services/\w+\.py',
            r'backend/core/\w+\.py',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output)
            files_modified.extend(matches)

        # 去重
        files_modified = list(set(files_modified))

        # 提取API规范
        api_spec_match = re.search(r'API规范[:：]\s*(.*?)(?:\n\n|$)', output, re.DOTALL)
        api_spec = api_spec_match.group(1) if api_spec_match else ""

        # 更新共享上下文
        state.set_shared_data("api_files", files_modified)
        state.set_shared_data("api_spec", api_spec)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            files_modified=files_modified,
            metadata={
                "api_files": [f for f in files_modified if "api" in f],
                "service_files": [f for f in files_modified if "services" in f],
                "api_spec": api_spec,
            }
        )
