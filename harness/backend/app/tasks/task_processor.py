import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.models.task import (
    Artifact,
    ArtifactType,
    Sample,
    Task,
    TaskStatus,
    WebSocketMessage,
)
from app.services.deeppresenter_integration import deeppresenter_integration
from app.services.task_service import TaskService
from app.services.websocket_manager import manager


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

            # 检查 DeepPresenter API 是否可用
            api_available = await deeppresenter_integration.check_health()

            if api_available:
                # 使用 DeepPresenter 生成 PPT（支持多样本并发）
                await TaskProcessor._process_with_deeppresenter(task)
            else:
                # API 不可用，使用后备方案
                print("DeepPresenter API not available, using fallback")
                await TaskProcessor._process_fallback(task)

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing task {task.id}: {error_msg}")
            import traceback

            traceback.print_exc()

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
    async def _process_with_deeppresenter(task: Task):
        """使用 DeepPresenter API 处理任务（支持多样本并发）"""
        samples = task.samples if task.samples else []

        if not samples:
            raise Exception("No samples to process")

        # 构建基础选项
        base_options = {
            "num_pages": task.pages if task.pages != "auto" else None,
            "convert_type": task.output_type,
            "template": task.options.get("template"),
            "powerpoint_type": task.aspect_ratio,
            "attachments": [],
        }

        # 处理上传的文件
        if task.uploaded_file_id:
            from app.core.config import settings

            upload_dir = Path(settings.pptagent_workspace) / "uploads"
            for file_path in upload_dir.glob(f"{task.uploaded_file_id}*"):
                if file_path.is_file():
                    remote_path = await deeppresenter_integration.upload_file(
                        str(file_path)
                    )
                    if remote_path:
                        base_options["attachments"].append(remote_path)
                    else:
                        base_options["attachments"].append(str(file_path))
                    break

        # 如果只有一个样本，使用原来的逻辑
        if len(samples) == 1:
            await TaskProcessor._process_single_sample(task, samples[0], base_options)
        else:
            # 多样本并发生成
            await TaskProcessor._process_multiple_samples(task, samples, base_options)

    @staticmethod
    async def _process_single_sample(
        task: Task, sample: Sample, options: dict[str, Any]
    ):
        """处理单个样本（原有逻辑）"""
        file_path = None
        token_stats = None
        content_chunks = []

        # 流式处理生成过程
        async for event in deeppresenter_integration.generate_ppt(
            task_id=task.id,
            prompt=task.prompt,
            options=options,
        ):
            event_type = event.get("type")

            if event_type == "message":
                message_content = TaskProcessor._format_message(event)
                if message_content:
                    content_chunks.append(message_content)
                    sample.content = "\n\n".join(content_chunks[-20:])
                    # 持久化消息到 Redis
                    await TaskService.append_message(
                        task.id,
                        sample.id,
                        {
                            "content": message_content,
                            "role": event.get("role"),
                            "tool_calls": event.get("tool_calls"),
                        },
                    )
                    await manager.send_to_task_subscribers(
                        task.id,
                        WebSocketMessage(
                            type="chunk",
                            task_id=task.id,
                            sample_id=sample.id,
                            content=message_content,
                            role=event.get("role"),
                            tool_calls=event.get("tool_calls"),
                        ),
                    )

            elif event_type == "file":
                file_path = event.get("file_path")
                print(f"[TaskProcessor] PPT generated at: {file_path}")

                # 提取 slides 目录路径并发送给前端
                workspace_path = Path(file_path).parent
                slides_dir = workspace_path / "slides"
                if slides_dir.exists():
                    slide_files = sorted(slides_dir.glob("slide_*.html"))
                    if slide_files:
                        slides_info = {
                            "slide_html_dir": str(slides_dir),
                            "html_files": [f.name for f in slide_files],
                        }
                        slides_json = f"```json\n{json.dumps(slides_info, ensure_ascii=False, indent=2)}\n```"
                        content_chunks.append(slides_json)
                        sample.content = "\n\n".join(content_chunks[-20:])
                        # 持久化 slides 信息到 Redis
                        await TaskService.append_message(
                            task.id,
                            sample.id,
                            {"content": slides_json, "role": "system"},
                        )
                        await manager.send_to_task_subscribers(
                            task.id,
                            WebSocketMessage(
                                type="chunk",
                                task_id=task.id,
                                sample_id=sample.id,
                                content=slides_json,
                            ),
                        )

            elif event_type == "stats":
                token_stats = event.get("token_stats", {})

            elif event_type == "progress":
                progress = event.get("progress", 0)
                slides_generated = event.get("slides_generated", 0)
                total_slides = event.get("total_slides", 0)
                phase = event.get("phase", "")
                sample.progress = progress

                # 实时扫描并发送已生成的幻灯片列表
                # 单样本模式：使用 task.id[:8] 作为 shortId（与 DeepPresenter 一致）
                from datetime import datetime

                date_str = datetime.now().strftime("%Y%m%d")
                short_task_id = task.id[:8]
                workspace_path = (
                    Path(settings.pptagent_workspace) / date_str / short_task_id
                )
                slides_dir = workspace_path / "slides"

                if slides_dir.exists():
                    slide_files = sorted(slides_dir.glob("slide_*.html"))
                    if slide_files:
                        slides_info = {"html_files": [f.name for f in slide_files]}
                        slides_json = json.dumps(slides_info, ensure_ascii=False)
                        # 更新 sample.content，确保前端能提取到幻灯片列表
                        # 避免重复添加相同的 JSON
                        if slides_json not in sample.content:
                            content_chunks.append(slides_json)
                            sample.content = "\n\n".join(content_chunks[-20:])
                            # 发送 slides 信息给前端实时渲染
                            await manager.send_to_task_subscribers(
                                task.id,
                                WebSocketMessage(
                                    type="chunk",
                                    task_id=task.id,
                                    sample_id=sample.id,
                                    content=slides_json,
                                ),
                            )

                await manager.send_to_task_subscribers(
                    task.id,
                    WebSocketMessage(
                        type="progress",
                        task_id=task.id,
                        progress=progress,
                        content=f"📊 进度: {progress}% | 已生成 {slides_generated}/{total_slides} 页 | 阶段: {phase}",
                    ),
                )

            elif event_type == "error":
                raise Exception(event.get("content", "Unknown error"))

        # 完成处理
        if file_path:
            artifact = Artifact(
                type=ArtifactType.PPT,
                content=f"PPT 生成完成: {Path(file_path).name}",
                language="pdf" if file_path.endswith(".pdf") else "pptx",
            )
            sample.status = TaskStatus.COMPLETED
            sample.progress = 100
            sample.file_path = file_path
            sample.artifact = artifact

            updated_options = task.options.copy()
            updated_options["generated_file_path"] = file_path
            if token_stats:
                updated_options["token_stats"] = token_stats

            await TaskService.update_task(
                task.id,
                {
                    "status": TaskStatus.COMPLETED,
                    "progress": 100,
                    "artifact": artifact.model_dump(),
                    "options": updated_options,
                    "samples": [sample.model_dump()],
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
                    file_path=file_path,
                ),
            )
        else:
            raise Exception("No file generated")

    @staticmethod
    async def _process_multiple_samples(
        task: Task, samples: list[Sample], base_options: dict[str, Any]
    ):
        """并发处理多个样本"""
        import uuid

        print(
            f"[TaskProcessor] Processing {len(samples)} samples concurrently for task {task.id}"
        )

        # 发送开始消息
        await manager.send_to_task_subscribers(
            task.id,
            WebSocketMessage(
                type="chunk",
                task_id=task.id,
                content=f"🚀 开始并发生成 {len(samples)} 个样本...",
            ),
        )

        # 创建并发任务
        async def process_sample(sample: Sample, sample_index: int) -> dict[str, Any]:
            """处理单个样本的协程"""
            # 使用完全独立的 UUID 作为 task_id，避免 DeepPresenter logger 冲突
            sample_task_id = str(uuid.uuid4())
            short_task_id = sample_task_id[:8]
            file_path = None
            token_stats = None
            content_chunks = []

            # 预设 file_path，让前端可以提取短 ID 进行实时预览
            # 格式: workspace/日期/短ID/presentation.pptx
            from datetime import datetime

            date_str = datetime.now().strftime("%Y%m%d")
            sample.file_path = f"{settings.pptagent_workspace}/{date_str}/{short_task_id}/presentation.pptx"

            # 更新样本状态为运行中
            sample.status = TaskStatus.RUNNING

            # 立即更新任务，让前端获取 file_path
            await TaskService.update_task(
                task.id,
                {
                    "samples": [s.model_dump() for s in samples],
                },
            )

            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="chunk",
                    task_id=task.id,
                    sample_id=sample.id,
                    content="🔄 开始生成...",
                    file_path=sample.file_path,
                ),
            )

            try:
                async for event in deeppresenter_integration.generate_ppt(
                    task_id=sample_task_id,
                    prompt=task.prompt,
                    options=base_options,
                ):
                    event_type = event.get("type")

                    if event_type == "message":
                        message_content = TaskProcessor._format_message(event)
                        if message_content:
                            content_chunks.append(message_content)
                            sample.content = "\n\n".join(content_chunks[-20:])
                            # 持久化消息到 Redis
                            await TaskService.append_message(
                                task.id,
                                sample.id,
                                {
                                    "content": message_content,
                                    "role": event.get("role"),
                                    "tool_calls": event.get("tool_calls"),
                                },
                            )
                            # 发送样本特定的消息
                            await manager.send_to_task_subscribers(
                                task.id,
                                WebSocketMessage(
                                    type="chunk",
                                    task_id=task.id,
                                    sample_id=sample.id,
                                    content=message_content,
                                    role=event.get("role"),
                                    tool_calls=event.get("tool_calls"),
                                ),
                            )

                    elif event_type == "file":
                        file_path = event.get("file_path")
                        print(
                            f"[TaskProcessor] Sample {sample_index + 1} PPT generated at: {file_path}"
                        )

                        # 提取 slides 目录路径并发送给前端
                        workspace_path = Path(file_path).parent
                        slides_dir = workspace_path / "slides"
                        if slides_dir.exists():
                            slide_files = sorted(slides_dir.glob("slide_*.html"))
                            if slide_files:
                                slides_info = {
                                    "slide_html_dir": str(slides_dir),
                                    "html_files": [f.name for f in slide_files],
                                }
                                slides_json = f"```json\n{json.dumps(slides_info, ensure_ascii=False, indent=2)}\n```"
                                content_chunks.append(slides_json)
                                sample.content = "\n\n".join(content_chunks[-20:])
                                # 持久化 slides 信息到 Redis
                                await TaskService.append_message(
                                    task.id,
                                    sample.id,
                                    {"content": slides_json, "role": "system"},
                                )
                                await manager.send_to_task_subscribers(
                                    task.id,
                                    WebSocketMessage(
                                        type="chunk",
                                        task_id=task.id,
                                        sample_id=sample.id,
                                        content=slides_json,
                                    ),
                                )

                    elif event_type == "stats":
                        token_stats = event.get("token_stats", {})

                    elif event_type == "progress":
                        progress = event.get("progress", 0)
                        sample.progress = progress
                        # 发送样本特定的进度
                        await manager.send_to_task_subscribers(
                            task.id,
                            WebSocketMessage(
                                type="progress",
                                task_id=task.id,
                                sample_id=sample.id,
                                progress=progress,
                                content=f"📊 进度: {progress}%",
                            ),
                        )

                    elif event_type == "error":
                        raise Exception(event.get("content", "Unknown error"))

                if file_path:
                    artifact = Artifact(
                        type=ArtifactType.PPT,
                        content=f"PPT 生成完成: {Path(file_path).name}",
                        language="pdf" if file_path.endswith(".pdf") else "pptx",
                    )
                    sample.status = TaskStatus.COMPLETED
                    sample.progress = 100
                    sample.file_path = file_path
                    sample.artifact = artifact

                    # 立即更新任务中的样本状态
                    await TaskService.update_task(
                        task.id,
                        {
                            "samples": [s.model_dump() for s in samples],
                        },
                    )

                    # 发送样本完成消息
                    await manager.send_to_task_subscribers(
                        task.id,
                        WebSocketMessage(
                            type="complete",
                            task_id=task.id,
                            sample_id=sample.id,
                            status=TaskStatus.COMPLETED,
                            progress=100,
                            artifact=artifact,
                            file_path=file_path,
                        ),
                    )

                    return {
                        "success": True,
                        "sample": sample,
                        "file_path": file_path,
                        "token_stats": token_stats,
                    }
                else:
                    raise Exception(f"Sample {sample_index + 1}: No file generated")

            except Exception as e:
                sample.status = TaskStatus.FAILED
                error_msg = str(e)
                await manager.send_to_task_subscribers(
                    task.id,
                    WebSocketMessage(
                        type="chunk",
                        task_id=task.id,
                        sample_id=sample.id,
                        content=f"❌ 生成失败: {error_msg}",
                    ),
                )
                return {
                    "success": False,
                    "sample": sample,
                    "error": error_msg,
                }

        # 并发执行所有样本
        tasks = [process_sample(sample, i) for i, sample in enumerate(samples)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful_samples = []
        failed_samples = []
        all_token_stats = {}

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                samples[i].status = TaskStatus.FAILED
                failed_samples.append((i, str(result)))
            elif result.get("success"):
                successful_samples.append(result["sample"])
                if result.get("token_stats"):
                    all_token_stats[f"sample_{i}"] = result["token_stats"]
            else:
                failed_samples.append((i, result.get("error", "Unknown error")))

        # 计算总体进度
        total_progress = int((len(successful_samples) / len(samples)) * 100)

        # 更新任务状态
        if successful_samples:
            # 至少有一个成功，使用第一个成功样本的 artifact 作为任务的主 artifact
            first_success = successful_samples[0]
            task_artifact = first_success.artifact

            updated_options = task.options.copy()
            updated_options["generated_file_paths"] = [
                s.file_path for s in successful_samples if s.file_path
            ]
            updated_options["token_stats"] = all_token_stats
            updated_options["successful_count"] = len(successful_samples)
            updated_options["failed_count"] = len(failed_samples)

            final_status = (
                TaskStatus.COMPLETED if not failed_samples else TaskStatus.COMPLETED
            )

            await TaskService.update_task(
                task.id,
                {
                    "status": final_status,
                    "progress": total_progress,
                    "artifact": task_artifact.model_dump() if task_artifact else None,
                    "options": updated_options,
                    "samples": [s.model_dump() for s in samples],
                },
            )

            # 发送完成消息
            summary = f"✅ 完成! 成功: {len(successful_samples)}/{len(samples)}"
            if failed_samples:
                summary += f", 失败: {len(failed_samples)}"

            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="complete",
                    task_id=task.id,
                    status=final_status,
                    progress=total_progress,
                    artifact=task_artifact,
                    content=summary,
                ),
            )
        else:
            # 全部失败
            error_msg = f"所有 {len(samples)} 个样本生成失败"
            await TaskService.update_task(
                task.id,
                {
                    "status": TaskStatus.FAILED,
                    "error": error_msg,
                    "samples": [s.model_dump() for s in samples],
                },
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
    def _format_message(event: dict[str, Any]) -> str:
        """格式化消息内容"""
        role = event.get("role", "assistant")
        content = event.get("content", "")
        tool_calls = event.get("tool_calls", [])

        message_parts = []
        role_emoji = {
            "system": "⚙️",
            "user": "👤",
            "assistant": "🤖",
            "tool": "📝",
        }.get(role, "💬")

        # 检查是否应该显示 content
        should_show_content = True
        if content and role == "assistant":
            content_stripped = content.strip()
            if content_stripped.startswith("[") and "arguments" in content_stripped:
                should_show_content = False
            elif "Function(" in content_stripped:
                should_show_content = False

        if content and should_show_content:
            message_parts.append(f"{role_emoji} **{role.title()}**: {content}")

        if tool_calls:
            for tc in tool_calls:
                tool_name = tc.get("name", "unknown")
                tool_args = tc.get("arguments", "")
                message_parts.append(f"🔧 **Tool Call: {tool_name}**")
                if tool_args:
                    try:
                        import json

                        args_dict = json.loads(tool_args)
                        if len(tool_args) < 300:
                            message_parts.append(
                                f"```json\n{json.dumps(args_dict, ensure_ascii=False, indent=2)}\n```"
                            )
                        else:
                            summary = {
                                k: (
                                    v[:50] + "..."
                                    if isinstance(v, str) and len(v) > 50
                                    else v
                                )
                                for k, v in args_dict.items()
                            }
                            message_parts.append(
                                f"```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"
                            )
                    except:
                        if len(tool_args) < 300:
                            message_parts.append(f"```\n{tool_args}\n```")

        return "\n".join(message_parts)

    @staticmethod
    async def _process_fallback(task: Task):
        """后备处理方案（当 DeepPresenter 不可用时）"""
        sample = task.samples[0] if task.samples else None

        # 模拟进度
        for progress in range(0, 101, 20):
            await asyncio.sleep(0.5)

            if sample:
                sample.progress = progress

            await manager.send_to_task_subscribers(
                task.id,
                WebSocketMessage(
                    type="progress",
                    task_id=task.id,
                    sample_id=sample.id if sample else None,
                    progress=progress,
                ),
            )

        # 生成后备内容
        content = f"""# {task.prompt}

## 演示文稿大纲

### 第一部分：引言
- 背景介绍
- 目标说明

### 第二部分：主要内容
- 核心观点 1
- 核心观点 2
- 核心观点 3

### 第三部分：总结
- 关键要点回顾
- 下一步行动

---

*注意：DeepPresenter API 当前不可用，这是自动生成的大纲。*
*请确保 deeppresenter-host 容器正在运行。*
"""

        artifact = Artifact(
            type=ArtifactType.MARKDOWN,
            content=content,
        )

        if sample:
            sample.status = TaskStatus.COMPLETED
            sample.progress = 100
            sample.content = content

        await TaskService.update_task(
            task.id,
            {
                "status": TaskStatus.COMPLETED,
                "progress": 100,
                "artifact": artifact.model_dump(),
                "samples": [sample.model_dump()] if sample else [],
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
            import traceback

            traceback.print_exc()


async def start_task_worker():
    """启动任务工作器"""
    asyncio.create_task(task_worker())
