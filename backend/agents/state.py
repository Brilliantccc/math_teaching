"""工作流状态管理"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    """Agent状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResult(BaseModel):
    """Agent执行结果"""
    agent_name: str
    status: AgentStatus
    output: str = ""
    files_modified: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0  # 重试次数


class WorkflowState(BaseModel):
    """工作流状态"""
    task: str
    status: str = "pending"
    current_agent: Optional[str] = None
    completed_agents: List[str] = Field(default_factory=list)
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)
    files_modified: List[str] = Field(default_factory=list)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    def mark_agent_completed(self, agent_name: str, result: AgentResult):
        """标记Agent完成"""
        self.completed_agents.append(agent_name)
        self.agent_results[agent_name] = result
        self.files_modified.extend(result.files_modified)

    def mark_agent_failed(self, agent_name: str, error: str):
        """标记Agent失败"""
        self.errors.append(f"{agent_name}: {error}")
        self.agent_results[agent_name] = AgentResult(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            errors=[error]
        )

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.shared_context.get(key, default)

    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_context[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task": self.task,
            "status": self.status,
            "current_agent": self.current_agent,
            "completed_agents": self.completed_agents,
            "files_modified": self.files_modified,
            "errors": self.errors,
            "shared_context": self.shared_context,
        }
