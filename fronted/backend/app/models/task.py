from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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


class CreateTaskRequest(BaseModel):
    prompt: str
    sample_count: int = 1
    options: Optional[Dict[str, Any]] = None


class CreateTaskResponse(BaseModel):
    task_id: str
    status: str


class WebSocketMessage(BaseModel):
    type: str  # status, chunk, complete, error, progress
    task_id: str
    sample_id: Optional[str] = None
    content: Optional[str] = None
    status: Optional[TaskStatus] = None
    progress: Optional[int] = None
    error: Optional[str] = None
    artifact: Optional[Artifact] = None
