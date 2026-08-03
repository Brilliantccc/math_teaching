"""数据模型专家Agent"""

from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel

from backend.agents.base import BaseAgent
from backend.agents.state import WorkflowState, AgentResult, AgentStatus


DATA_MODEL_SYSTEM_PROMPT = """你是一个数据模型专家，专注于数据库模型设计和Schema定义。

你的职责:
1. 设计和修改数据库模型 (models/*.py)
2. 定义Pydantic Schema (schemas/*.py)
3. 处理数据库迁移 (database.py)
4. 确保数据类型正确性和一致性

项目架构:
- 使用 SQLAlchemy 异步ORM
- 使用 Pydantic v2 进行数据验证
- 数据库: SQLite (通过 aiosqlite)

代码规范:
1. 模型字段使用 Mapped 类型注解
2. 所有模型继承自 Base
3. Schema 使用 Pydantic BaseModel
4. 为 JSON 字段提供默认值
5. 添加必要的关系定义

工作流程:
1. 分析需求，确定需要修改的模型
2. 修改 models/*.py 文件
3. 更新 schemas/*.py 文件
4. 如需要，更新 database.py 迁移
5. 验证代码语法正确性

完成后，返回修改的文件列表和简要说明。
"""


class DataModelAgent(BaseAgent):
    """数据模型专家Agent"""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        super().__init__(
            name="data_model_expert",
            system_prompt=DATA_MODEL_SYSTEM_PROMPT,
            llm=llm,
            tools=tools,
        )

    def _build_task_prompt(self, task: str, state: WorkflowState) -> str:
        """构建任务提示"""
        # 获取相关上下文
        api_spec = state.get_shared_data("api_spec", "")
        existing_models = state.get_shared_data("existing_models", "")

        prompt = f"""任务: {task}

你需要完成以下工作:
1. 分析需求，确定数据模型变更
2. 修改或创建 models/*.py 文件
3. 更新 schemas/*.py 文件
4. 如需要，更新 database.py 迁移

{f'API规范参考:\n{api_spec}' if api_spec else ''}

{f'现有模型:\n{existing_models}' if existing_models else ''}

重要规则:
1. 只修改 backend/models/ 和 backend/schemas/ 目录下的文件
2. 保持与现有模型的一致性
3. 为新字段提供合理的默认值
4. 使用 JSON 字段存储复杂数据（如列表、字典）
5. 添加必要的索引和关系

完成后，请列出所有修改的文件。
"""
        return prompt

    def _parse_output(self, output: str, state: WorkflowState) -> AgentResult:
        """解析输出并更新共享状态"""
        import re

        files_modified = []

        # 提取修改的文件
        file_patterns = [
            r'backend/models/\w+\.py',
            r'backend/schemas/\w+\.py',
            r'backend/database\.py',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output)
            files_modified.extend(matches)

        # 去重
        files_modified = list(set(files_modified))

        # 更新共享上下文
        state.set_shared_data("data_model_files", files_modified)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            files_modified=files_modified,
            metadata={
                "models_modified": [f for f in files_modified if "models" in f],
                "schemas_modified": [f for f in files_modified if "schemas" in f],
            }
        )
