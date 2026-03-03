"""
DeepPresenter 集成模块
通过 HTTP API 调用 DeepPresenter Host 容器生成 PPT
"""

import asyncio
import json
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator
from app.core.config import settings


class DeepPresenterIntegration:
    """DeepPresenter HTTP API 集成类"""

    def __init__(self):
        # API 基础 URL，从配置读取
        self.api_base_url = settings.pptagent_docker_url.rstrip("/")
        # 如果配置的是 Gradio 端口 7861，改为 API 端口 8080
        if self.api_base_url.endswith(":7861"):
            self.api_base_url = self.api_base_url.replace(":7861", ":8080")
        self.timeout = httpx.Timeout(600.0, connect=30.0)  # 10分钟超时

    async def check_health(self) -> bool:
        """检查 DeepPresenter API 是否可用"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.get(f"{self.api_base_url}/health")
                return response.status_code == 200
        except Exception as e:
            print(f"DeepPresenter health check failed: {e}")
            return False

    async def generate_ppt(
        self,
        task_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成 PPT（流式返回）

        Args:
            task_id: 任务 ID
            prompt: 用户输入的提示词
            options: 生成选项
                - template: 模板名称
                - num_pages: 页数（auto 或数字）
                - convert_type: 转换类型（freeform 或 templates）
                - attachments: 附件文件路径列表

        Yields:
            生成过程中的消息字典：
                - type: 'message' | 'file' | 'stats' | 'error'
                - role: 'system' | 'user' | 'assistant' | 'tool'
                - content: 消息内容
                - tool_calls: 工具调用信息
                - file_path: 生成的文件路径（type='file'时）
        """
        options = options or {}

        # 构建请求数据
        request_data = {
            "task_id": task_id,
            "prompt": prompt,
            "attachments": options.get("attachments", []),
            "num_pages": options.get("num_pages"),
            "template": options.get("template"),
            "convert_type": options.get("convert_type", "freeform"),
            "powerpoint_type": options.get("powerpoint_type", "16:9"),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 使用 SSE 流式请求
                async with client.stream(
                    "POST",
                    f"{self.api_base_url}/api/generate",
                    json=request_data,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield {
                            "type": "error",
                            "content": f"API error: {response.status_code} - {error_text.decode()}",
                        }
                        return

                    # 解析 SSE 事件
                    buffer = ""
                    event_count = 0
                    print(f"[DeepPresenter] Starting SSE stream for task {task_id}")
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        # 标准化换行符：将 \r\n 转换为 \n
                        buffer = buffer.replace("\r\n", "\n")
                        # SSE 事件以双换行分隔
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            event_data = self._parse_sse_event(event_str)
                            if event_data:
                                event_count += 1
                                event_type = event_data.get('type')
                                # 详细日志
                                if event_type == 'message':
                                    role = event_data.get('role', 'unknown')
                                    content_preview = (event_data.get('content', '') or '')[:100]
                                    tool_calls = event_data.get('tool_calls', [])
                                    print(f"[DeepPresenter] SSE #{event_count} message: role={role}, content={content_preview}..., tool_calls={len(tool_calls)}")
                                elif event_type == 'progress':
                                    print(f"[DeepPresenter] SSE #{event_count} progress: {event_data.get('progress')}%")
                                else:
                                    print(f"[DeepPresenter] SSE #{event_count} {event_type}: {event_data}")
                                yield event_data

                    # 处理流结束时缓冲区中剩余的数据
                    if buffer.strip():
                        event_data = self._parse_sse_event(buffer)
                        if event_data:
                            event_count += 1
                            print(f"[DeepPresenter] Final SSE #{event_count}: {event_data.get('type')}, file_path: {event_data.get('file_path')}")
                            yield event_data

                    print(f"[DeepPresenter] SSE stream ended, total events: {event_count}")

        except httpx.TimeoutException:
            yield {
                "type": "error",
                "content": "Request timeout - PPT generation took too long",
            }
        except httpx.ConnectError as e:
            yield {
                "type": "error",
                "content": f"Cannot connect to DeepPresenter API: {e}",
            }
        except Exception as e:
            print(f"Error in generate_ppt: {e}")
            import traceback
            traceback.print_exc()
            yield {
                "type": "error",
                "content": str(e),
            }

    def _parse_sse_event(self, event_str: str) -> Optional[Dict[str, Any]]:
        """解析 SSE 事件字符串"""
        event_type = None
        data = None

        for line in event_str.split("\n"):
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()

        if data:
            try:
                parsed_data = json.loads(data)
                # 根据事件类型设置 type 字段
                if event_type == "complete":
                    parsed_data["type"] = "file"
                elif event_type == "error":
                    parsed_data["type"] = "error"
                elif event_type == "stats":
                    parsed_data["type"] = "stats"
                elif event_type == "message":
                    parsed_data["type"] = "message"
                elif event_type == "progress":
                    parsed_data["type"] = "progress"
                return parsed_data
            except json.JSONDecodeError:
                return {"type": "message", "content": data}

        return None

    async def generate_ppt_sync(
        self,
        task_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        同步生成 PPT（等待完成后返回）

        Returns:
            结果字典：
                - success: 是否成功
                - file_path: 生成的文件路径
                - error: 错误信息
        """
        options = options or {}

        request_data = {
            "task_id": task_id,
            "prompt": prompt,
            "attachments": options.get("attachments", []),
            "num_pages": options.get("num_pages"),
            "template": options.get("template"),
            "convert_type": options.get("convert_type", "freeform"),
            "powerpoint_type": options.get("powerpoint_type", "16:9"),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/generate/sync",
                    json=request_data,
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                    }

                result = response.json()
                return {
                    "success": result.get("status") == "completed",
                    "file_path": result.get("file_path"),
                    "error": result.get("error"),
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/task/{task_id}"
                )
                if response.status_code == 200:
                    return response.json()
                return {"status": "unknown", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def upload_file(self, file_path: str) -> Optional[str]:
        """
        上传文件到 DeepPresenter 工作空间

        Returns:
            上传后的文件路径，失败返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                with open(file_path, "rb") as f:
                    files = {"file": (Path(file_path).name, f)}
                    response = await client.post(
                        f"{self.api_base_url}/api/upload",
                        files=files,
                    )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("path")
                return None
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

    def get_available_templates(self) -> list[str]:
        """获取可用的模板列表（同步方法）"""
        import asyncio

        async def _get_templates():
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                    response = await client.get(f"{self.api_base_url}/api/templates")
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("templates", [])
                    return []
            except Exception as e:
                print(f"Error getting templates: {e}")
                return []

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步上下文中，创建新任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _get_templates())
                    return future.result(timeout=30)
            else:
                return loop.run_until_complete(_get_templates())
        except Exception as e:
            print(f"Error in get_available_templates: {e}")
            return []

    async def get_available_templates_async(self) -> list[str]:
        """获取可用的模板列表（异步方法）"""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(f"{self.api_base_url}/api/templates")
                if response.status_code == 200:
                    result = response.json()
                    return result.get("templates", [])
                return []
        except Exception as e:
            print(f"Error getting templates: {e}")
            return []

    async def cancel_task(self, task_id: str) -> bool:
        """取消正在运行的任务"""
        # 目前 API 不支持取消，返回 False
        return False

    def get_download_url(self, task_id: str) -> str:
        """获取文件下载 URL"""
        return f"{self.api_base_url}/api/download/{task_id}"


# 全局实例
deeppresenter_integration = DeepPresenterIntegration()
