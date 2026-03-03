from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    """将 snake_case 转换为 camelCase"""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


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
    language: str | None = None


class Sample(BaseModel):
    id: str
    content: str = ""
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    file_path: str | None = None  # 生成的文件路径
    artifact: Optional["Artifact"] = None  # 样本的 artifact


class Task(BaseModel):
    id: str
    prompt: str
    status: TaskStatus = TaskStatus.IDLE
    samples: list[Sample] = []
    progress: int = 0
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    error: str | None = None
    artifact: Artifact | None = None
    options: dict[str, Any] = {}
    pages: str = "auto"  # auto, 5, 10, 15, 20
    output_type: str = "freeform"  # freeform (自由生成)
    uploaded_file_id: str | None = None  # 上传文件的 ID
    aspect_ratio: str = "16:9"  # 幻灯片尺寸比例: 16:9, 4:3, A1, A2, A3, A4


class CreateTaskRequest(BaseModel):
    prompt: str
    sample_count: int = 1
    pages: str = "auto"  # auto, 5, 10, 15, 20
    output_type: str = "freeform"  # freeform (自由生成)
    uploaded_file_id: str | None = None  # 上传文件的 ID
    aspect_ratio: str = "16:9"  # 幻灯片尺寸比例: 16:9, 4:3, A1, A2, A3, A4
    options: dict[str, Any] | None = None


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
    sample_id: str | None = None
    content: str | None = None
    status: TaskStatus | None = None
    progress: int | None = None
    error: str | None = None
    artifact: Artifact | None = None
    file_path: str | None = None
    # 新增字段用于显示 Agent 交互过程
    role: str | None = None  # system, user, assistant, tool
    tool_calls: list[dict[str, Any]] | None = None  # 工具调用信息
