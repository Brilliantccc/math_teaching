"""PDF导出专家Agent"""

from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel

from backend.agents.base import BaseAgent
from backend.agents.state import WorkflowState, AgentResult, AgentStatus


PDF_SYSTEM_PROMPT = """你是一个PDF导出专家，专注于PDF文档生成和排版设计。

你的职责:
1. 实现PDF生成功能 (utils/pdf_utils.py)
2. 处理LaTeX公式渲染
3. 处理图片嵌入和排版
4. 优化PDF输出质量

项目架构:
- ReportLab PDF生成
- Matplotlib LaTeX渲染
- PIL 图片处理

代码规范:
1. 使用ReportLab生成PDF
2. 处理中文字体支持
3. 优化排版布局
4. 处理图片缩放和定位
5. 支持LaTeX公式渲染

工作流程:
1. 分析需求，确定PDF功能
2. 修改 utils/pdf_utils.py
3. 更新API端点 (api/tests.py)
4. 优化排版和样式
5. 验证代码语法正确性

完成后，返回修改的文件列表和功能说明。
"""


class PDFAgent(BaseAgent):
    """PDF导出专家Agent"""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        super().__init__(
            name="pdf_expert",
            system_prompt=PDF_SYSTEM_PROMPT,
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
1. 分析需求，确定PDF功能
2. 修改 utils/pdf_utils.py
3. 更新API端点 (api/tests.py)
4. 优化排版和样式

{f'数据模型文件:\n{chr(10).join(data_model_files)}' if data_model_files else ''}

{f'数据模型定义:\n{data_models}' if data_models else ''}

重要规则:
1. 只修改 backend/utils/pdf_utils.py 和相关API
2. 支持中文字体显示
3. 处理LaTeX公式渲染
4. 支持图片嵌入
5. 优化PDF排版布局

PDF功能规范:
- 支持A4纸张大小
- 支持中文字体
- 支持LaTeX公式
- 支持图片嵌入
- 支持分页
- 支持页眉页脚

完成后，请列出所有修改的文件和功能说明。
"""
        return prompt

    def _parse_output(self, output: str, state: WorkflowState) -> AgentResult:
        """解析输出并更新共享状态"""
        import re

        files_modified = []

        # 提取修改的文件
        file_patterns = [
            r'backend/utils/pdf_utils\.py',
            r'backend/api/tests\.py',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output)
            files_modified.extend(matches)

        # 去重
        files_modified = list(set(files_modified))

        # 提取功能说明
        feature_match = re.search(r'功能说明[:：]\s*(.*?)(?:\n\n|$)', output, re.DOTALL)
        feature_desc = feature_match.group(1) if feature_match else ""

        # 更新共享上下文
        state.set_shared_data("pdf_files", files_modified)
        state.set_shared_data("pdf_feature", feature_desc)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            files_modified=files_modified,
            metadata={
                "pdf_files": files_modified,
                "feature_desc": feature_desc,
            }
        )
