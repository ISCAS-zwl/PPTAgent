import json
from typing import Optional, Dict
from app.core.redis import get_redis
from app.models.task import Task, TaskStatus


class TaskService:
    """任务服务"""

    @staticmethod
    async def create_task(task: Task) -> None:
        """创建任务并存储到 Redis"""
        redis = await get_redis()
        task_key = f"task:{task.id}"
        await redis.set(task_key, task.model_dump_json())
        await redis.expire(task_key, 86400)  # 24小时过期

        # 添加到任务列表
        await redis.zadd("tasks", {task.id: task.created_at})

    @staticmethod
    async def get_task(task_id: str) -> Optional[Task]:
        """获取任务"""
        redis = await get_redis()
        task_key = f"task:{task_id}"
        task_data = await redis.get(task_key)
        if task_data:
            return Task.model_validate_json(task_data)
        return None

    @staticmethod
    async def update_task(task_id: str, updates: Dict) -> None:
        """更新任务"""
        redis = await get_redis()
        task = await TaskService.get_task(task_id)
        if task:
            for key, value in updates.items():
                setattr(task, key, value)
            task_key = f"task:{task_id}"
            await redis.set(task_key, task.model_dump_json())

    @staticmethod
    async def list_tasks(limit: int = 50) -> list[Task]:
        """列出任务"""
        redis = await get_redis()
        task_ids = await redis.zrevrange("tasks", 0, limit - 1)
        tasks = []
        for task_id in task_ids:
            task = await TaskService.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks

    @staticmethod
    async def delete_task(task_id: str) -> None:
        """删除任务"""
        redis = await get_redis()
        task_key = f"task:{task_id}"
        await redis.delete(task_key)
        await redis.zrem("tasks", task_id)
