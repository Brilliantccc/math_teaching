"""工作流编排"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from backend.agents.state import WorkflowState, AgentResult, AgentStatus
from backend.agents.data_model_agent import DataModelAgent
from backend.agents.api_agent import APIAgent
from backend.agents.frontend_agent import FrontendAgent
from backend.agents.pdf_agent import PDFAgent


class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.agents = {
            "data_model": DataModelAgent(),
            "api": APIAgent(),
            "frontend": FrontendAgent(),
            "pdf": PDFAgent(),
        }
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.last_workflow_status: Optional[str] = None
        self.last_workflow_message: str = ""

    async def run_workflow(self, task: str) -> Dict[str, Any]:
        """运行工作流（带Fallback机制）

        Args:
            task: 任务描述

        Returns:
            工作流结果
        """
        total_started_at = time.perf_counter()
        state = WorkflowState(task=task)
        state.status = "running"
        self.last_workflow_status = "running"

        try:
            print(f"\n{'='*60}")
            print(f"🚀 开始工作流执行...")
            print(f"任务: {task[:100]}...")
            print(f"{'='*60}\n")

            # 阶段1: 数据模型专家（必须先执行）
            print("📋 阶段1: 数据模型专家...")
            state.current_agent = "data_model"
            data_model_result = await self._run_agent_with_fallback(
                "data_model", task, state,
                fallback_output="数据模型专家执行失败，跳过此阶段"
            )
            state.mark_agent_completed("data_model", data_model_result)

            # 阶段2: 并行执行其他Agent
            print("🔄 阶段2: 并行执行API和PDF专家...")
            parallel_agents = ["api", "pdf"]
            parallel_tasks = [
                self._run_agent_with_fallback(agent_name, task, state)
                for agent_name in parallel_agents
            ]

            # 并行执行
            parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

            # 处理结果
            for agent_name, result in zip(parallel_agents, parallel_results):
                if isinstance(result, Exception):
                    state.mark_agent_failed(agent_name, str(result))
                else:
                    state.mark_agent_completed(agent_name, result)

            # 阶段3: 前端专家（依赖API规范）
            print("🎨 阶段3: 前端专家...")
            state.current_agent = "frontend"
            frontend_result = await self._run_agent_with_fallback(
                "frontend", task, state,
                fallback_output="前端专家执行失败，跳过此阶段"
            )
            state.mark_agent_completed("frontend", frontend_result)

            state.status = "completed"
            self.last_workflow_status = "completed"
            self.last_workflow_message = f"工作流执行完成，耗时 {time.perf_counter() - total_started_at:.2f}秒"

            print(f"\n{'='*60}")
            print(f"✅ 工作流执行完成")
            print(f"耗时: {time.perf_counter() - total_started_at:.2f}秒")
            print(f"{'='*60}\n")

        except Exception as e:
            state.status = "failed"
            state.errors.append(str(e))
            self.last_workflow_status = "failed"
            self.last_workflow_message = str(e)
            print(f"\n❌ 工作流执行失败: {str(e)}")

        return state.to_dict()

    async def _run_agent_with_fallback(
        self,
        agent_name: str,
        task: str,
        state: WorkflowState,
        fallback_output: Optional[str] = None,
    ) -> AgentResult:
        """运行单个Agent（带Fallback）"""
        agent = self.agents.get(agent_name)
        if not agent:
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.FAILED,
                errors=[f"未知的Agent: {agent_name}"]
            )

        # 使用带Fallback的执行方式
        if fallback_output:
            result = await self._run_agent_in_thread(agent, task, state, fallback_output)
        else:
            result = await self._run_agent_in_thread(agent, task, state)

        return result

    async def _run_agent_in_thread(
        self,
        agent,
        task: str,
        state: WorkflowState,
        fallback_output: Optional[str] = None,
    ) -> AgentResult:
        """在线程池中运行Agent"""
        loop = asyncio.get_event_loop()

        if fallback_output:
            result = await loop.run_in_executor(
                self.executor,
                lambda: agent.run_with_fallback(task, state, fallback_output)
            )
        else:
            result = await loop.run_in_executor(
                self.executor,
                lambda: agent.run(task, state)
            )

        return result

    async def _run_agent(
        self,
        agent_name: str,
        task: str,
        state: WorkflowState
    ) -> AgentResult:
        """运行单个Agent（兼容旧接口）"""
        return await self._run_agent_with_fallback(agent_name, task, state)

    def run_workflow_sync(self, task: str) -> Dict[str, Any]:
        """同步运行工作流（用于API调用）"""
        return asyncio.run(self.run_workflow(task))

    def get_agent_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "agents": {
                name: {
                    "name": agent.name,
                    "class": agent.__class__.__name__,
                    "max_retries": getattr(agent, 'max_retries', 3),
                }
                for name, agent in self.agents.items()
            },
            "max_workers": self.max_workers,
            "last_status": self.last_workflow_status,
            "last_message": self.last_workflow_message,
        }


# 全局实例
workflow_orchestrator = WorkflowOrchestrator()
