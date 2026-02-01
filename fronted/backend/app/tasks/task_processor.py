import asyncio
import uuid
from typing import List
from app.models.task import Task, Sample, TaskStatus, WebSocketMessage, Artifact, ArtifactType
from app.services.task_service import TaskService
from app.services.websocket_manager import manager
from app.services.pptagent_integration import pptagent_integration


class TaskProcessor:
    """任务处理器"""

    @staticmethod
    async def process_task(task: Task):
        """处理任务 - 主入口"""
        try:
            # 更新任务状态为运行中
            await TaskService.update_task(task.id, {"status": TaskStatus.RUNNING})
            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="status",
                    task_id=task.id,
                    status=TaskStatus.RUNNING,
                ),
            )

            # 如果有多个样本，并行处理
            if len(task.samples) > 1:
                await TaskProcessor._process_multiple_samples(task)
            else:
                await TaskProcessor._process_single_sample(task)

            # 生成最终的 Artifact
            artifact = await TaskProcessor._generate_artifact(task)

            # 更新任务为完成状态
            await TaskService.update_task(
                task.id,
                {
                    "status": TaskStatus.COMPLETED,
                    "progress": 100,
                    "artifact": artifact.model_dump() if artifact else None,
                },
            )

            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="complete",
                    task_id=task.id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    artifact=artifact,
                ),
            )

        except Exception as e:
            error_msg = str(e)
            await TaskService.update_task(
                task.id,
                {"status": TaskStatus.FAILED, "error": error_msg},
            )
            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="error",
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=error_msg,
                ),
            )

    @staticmethod
    async def _process_single_sample(task: Task):
        """处理单个样本"""
        sample = task.samples[0]

        # 模拟 PPT 生成过程
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.5)  # 模拟处理时间

            # 更新样本进度
            sample.progress = progress
            await TaskService.update_task(task.id, {"samples": [sample.model_dump()]})

            # 发送进度更新
            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="progress",
                    task_id=task.id,
                    sample_id=sample.id,
                    progress=progress,
                ),
            )

            # 模拟流式内容生成
            if progress % 20 == 0:
                chunk = f"正在生成 PPT... 进度 {progress}%\n"
                sample.content += chunk
                await manager.send_to_task_subscribers(
                    task.id,
                    WebSocketMessage(
                        type="chunk",
                        task_id=task.id,
                        sample_id=sample.id,
                        content=chunk,
                    ),
                )

        sample.status = TaskStatus.COMPLETED

    @staticmethod
    async def _process_multiple_samples(task: Task):
        """并行处理多个样本"""
        async def process_sample(sample: Sample):
            for progress in range(0, 101, 10):
                await asyncio.sleep(0.3)  # 模拟处理时间

                sample.progress = progress
                await manager.send_to_task_subscribers(
                    task.id,
                    WebSocketMessage(
                        type="progress",
                        task_id=task.id,
                        sample_id=sample.id,
                        progress=progress,
                    ),
                )

                if progress % 20 == 0:
                    chunk = f"样本 {sample.id} 进度 {progress}%\n"
                    sample.content += chunk
                    await manager.send_to_task_subscribers(
                        task.id,
                        WebSocketMessage(
                            type="chunk",
                            task_id=task.id,
                            sample_id=sample.id,
                            content=chunk,
                        ),
                    )

            sample.status = TaskStatus.COMPLETED

        # 并行处理所有样本
        await asyncio.gather(*[process_sample(sample) for sample in task.samples])

        # 更新任务中的样本
        await TaskService.update_task(
            task.id,
            {"samples": [s.model_dump() for s in task.samples]},
        )

    @staticmethod
    async def _generate_artifact(task: Task) -> Artifact:
        """生成最终的 Artifact"""
        # 尝试使用 PPTAgent 生成
        result = await pptagent_integration.generate_ppt(
            prompt=task.prompt,
            options=task.options
        )

        if result.get("success"):
            # PPTAgent 生成成功
            content = result.get("content", "")
            file_path = result.get("file_path")

            # 如果生成了 PPT 文件，返回 PPT 类型
            if file_path and file_path.endswith(".pptx"):
                return Artifact(
                    type=ArtifactType.PPT,
                    content=content,
                    language="pptx",
                )
            else:
                return Artifact(
                    type=ArtifactType.MARKDOWN,
                    content=content,
                )
        else:
            # PPTAgent 不可用或失败，使用后备方案
            content = f"""# {task.prompt}

## 生成结果

这是根据您的需求生成的演示文稿内容。

### 样本数量: {len(task.samples)}

"""
            for i, sample in enumerate(task.samples, 1):
                content += f"\n#### 样本 {i}\n\n{sample.content}\n"

            content += """

## 下一步

您可以：
1. 下载生成的内容
2. 继续编辑和优化
3. 导出为 PPT 格式

---

*由 PPTAgent 自动生成*
"""

            return Artifact(
                type=ArtifactType.MARKDOWN,
                content=content,
            )


# 创建后台任务队列
task_queue: asyncio.Queue = asyncio.Queue()


async def task_worker():
    """后台任务工作器"""
    while True:
        try:
            task = await task_queue.get()
            await TaskProcessor.process_task(task)
            task_queue.task_done()
        except Exception as e:
            print(f"Error in task worker: {e}")


async def start_task_worker():
    """启动任务工作器"""
    asyncio.create_task(task_worker())
