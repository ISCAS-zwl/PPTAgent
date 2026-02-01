from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from app.models.task import (
    Task,
    Sample,
    CreateTaskRequest,
    CreateTaskResponse,
    TaskStatus,
)
from app.services.task_service import TaskService
from app.tasks.task_processor import task_queue
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["tasks"])


@router.post("/task/create", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    """创建新任务"""
    # 验证样本数量
    if request.sample_count > settings.max_sample_count:
        raise HTTPException(
            status_code=400,
            detail=f"Sample count exceeds maximum of {settings.max_sample_count}",
        )

    # 生成任务 ID
    task_id = str(uuid.uuid4())

    # 创建样本
    samples = [
        Sample(
            id=f"{task_id}-sample-{i}",
            status=TaskStatus.IDLE,
        )
        for i in range(request.sample_count)
    ]

    # 创建任务对象
    task = Task(
        id=task_id,
        prompt=request.prompt,
        status=TaskStatus.IDLE,
        samples=samples,
        options=request.options or {},
    )

    # 保存到 Redis
    await TaskService.create_task(task)

    # 添加到任务队列
    await task_queue.put(task)

    return CreateTaskResponse(task_id=task_id, status="created")


@router.get("/task/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """获取任务详情"""
    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks", response_model=List[Task])
async def list_tasks(limit: int = 50):
    """列出所有任务"""
    tasks = await TaskService.list_tasks(limit)
    return tasks


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await TaskService.delete_task(task_id)
    return {"status": "deleted", "task_id": task_id}
