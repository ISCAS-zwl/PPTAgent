from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


def to_camel(string: str) -> str:
    """将 snake_case 转换为 camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class TaskStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COLLECTING = "collecting"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactType(str, Enum):
    HTML = "html"
    CODE = "code"
    MARKDOWN = "markdown"
    PPT = "ppt"


class Artifact(BaseModel):
    type: ArtifactType
    content: str
    language: Optional[str] = None


class Sample(BaseModel):
    id: str
    content: str = ""
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    file_path: Optional[str] = None  # 生成的文件路径
    artifact: Optional["Artifact"] = None  # 样本的 artifact


class Task(BaseModel):
    id: str
    prompt: str
    status: TaskStatus = TaskStatus.IDLE
    samples: List[Sample] = []
    progress: int = 0
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    error: Optional[str] = None
    artifact: Optional[Artifact] = None
    options: Dict[str, Any] = {}
    pages: str = "auto"  # auto, 5, 10, 15, 20
    output_type: str = "freeform"  # freeform (自由生成)
    uploaded_file_id: Optional[str] = None  # 上传文件的 ID


class CreateTaskRequest(BaseModel):
    prompt: str
    sample_count: int = 1
    pages: str = "auto"  # auto, 5, 10, 15, 20
    output_type: str = "freeform"  # freeform (自由生成)
    uploaded_file_id: Optional[str] = None  # 上传文件的 ID
    options: Optional[Dict[str, Any]] = None


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str


class WebSocketMessage(BaseModel):
    """WebSocket 消息模型，序列化时使用 camelCase"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,  # 序列化时使用别名（camelCase）
    )

    type: str  # status, chunk, complete, error, progress
    task_id: str
    sample_id: Optional[str] = None
    content: Optional[str] = None
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    artifact: Optional[Artifact] = None
    # 新增字段用于显示 Agent 交互过程
    role: Optional[str] = None  # system, user, assistant, tool
    tool_calls: Optional[List[Dict[str, Any]]] = None  # 工具调用信息
