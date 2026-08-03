"""前端组件专家Agent"""

from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel

from backend.agents.base import BaseAgent
from backend.agents.state import WorkflowState, AgentResult, AgentStatus


FRONTEND_SYSTEM_PROMPT = """你是一个前端组件专家，专注于Vue 3组件开发和用户界面设计。

你的职责:
1. 设计和实现 Vue 3 组件 (views/*.vue, components/*.vue)
2. 实现用户界面交互
3. 集成后端API
4. 处理状态管理和路由

项目架构:
- Vue 3 + Composition API + <script setup>
- Ant Design Vue 组件库
- Vue Router 路由管理
- Pinia 状态管理
- TypeScript 类型安全

代码规范:
1. 使用 <script setup> 语法
2. 使用 Composition API
3. 使用 Ant Design Vue 组件
4. 添加适当的TypeScript类型
5. 处理加载状态和错误

工作流程:
1. 分析需求，确定UI组件设计
2. 修改 views/*.vue 文件
3. 创建或修改 components/*.vue
4. 更新 API 调用
5. 验证代码语法正确性

完成后，返回修改的文件列表和UI设计说明。
"""


class FrontendAgent(BaseAgent):
    """前端组件专家Agent"""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        super().__init__(
            name="frontend_expert",
            system_prompt=FRONTEND_SYSTEM_PROMPT,
            llm=llm,
            tools=tools,
        )

    def _build_task_prompt(self, task: str, state: WorkflowState) -> str:
        """构建任务提示"""
        # 获取API规范
        api_spec = state.get_shared_data("api_spec", "")
        api_files = state.get_shared_data("api_files", [])

        prompt = f"""任务: {task}

你需要完成以下工作:
1. 分析需求，确定UI组件设计
2. 修改或创建 views/*.vue 文件
3. 创建或修改 components/*.vue
4. 更新 API 调用和状态管理

{f'API规范:\n{api_spec}' if api_spec else ''}

{f'API文件:\n{chr(10).join(api_files)}' if api_files else ''}

重要规则:
1. 只修改 frontend/src/ 目录下的文件
2. 使用 Vue 3 Composition API
3. 使用 Ant Design Vue 组件
4. 添加适当的TypeScript类型
5. 处理加载状态和错误状态

组件设计规范:
- 使用 <script setup> 语法
- 使用 ref/reactive 管理状态
- 使用 computed 计算属性
- 使用 watch 监听变化
- 使用 onMounted 初始化

完成后，请列出所有修改的文件和UI设计说明。
"""
        return prompt

    def _parse_output(self, output: str, state: WorkflowState) -> AgentResult:
        """解析输出并更新共享状态"""
        import re

        files_modified = []

        # 提取修改的文件
        file_patterns = [
            r'frontend/src/views/\w+/\w+\.vue',
            r'frontend/src/components/\w+/\w+\.vue',
            r'frontend/src/stores/\w+\.ts',
            r'frontend/src/api/\w+\.ts',
            r'frontend/src/router/\w+\.ts',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output)
            files_modified.extend(matches)

        # 去重
        files_modified = list(set(files_modified))

        # 提取UI设计说明
        ui_design_match = re.search(r'UI设计说明[:：]\s*(.*?)(?:\n\n|$)', output, re.DOTALL)
        ui_design = ui_design_match.group(1) if ui_design_match else ""

        # 更新共享上下文
        state.set_shared_data("frontend_files", files_modified)
        state.set_shared_data("ui_design", ui_design)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            files_modified=files_modified,
            metadata={
                "vue_files": [f for f in files_modified if f.endswith(".vue")],
                "ts_files": [f for f in files_modified if f.endswith(".ts")],
                "ui_design": ui_design,
            }
        )
