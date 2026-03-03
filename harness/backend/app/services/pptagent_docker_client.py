"""
PPTAgent Docker 客户端
通过 HTTP API 调用 Docker 化的 PPTAgent 服务
"""

import asyncio
import json
from typing import Optional, Dict, Any, AsyncIterator
import httpx
from app.core.config import settings
from app.utils import get_logger

logger = get_logger(__name__)


class PPTAgentDockerClient:
    """
    PPTAgent Docker 客户端
    支持通过 HTTP API 调用 Docker 容器中的 PPTAgent 服务
    """

    def __init__(
        self,
        base_url: str = "http://deeppresenter-host:7861",
        timeout: float = 300.0,
    ):
        """
        初始化 Docker 客户端

        Args:
            base_url: PPTAgent 服务的基础 URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def generate_ppt(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成 PPT

        Args:
            prompt: 用户输入的提示词
            options: 生成选项
                - template: 模板名称
                - style: 样式
                - output_format: 输出格式 (pptx, pdf, markdown)

        Returns:
            生成结果字典，包含：
                - success: 是否成功
                - content: 生成的内容
                - file_path: 生成的文件路径
                - error: 错误信息（如果失败）
        """
        try:
            options = options or {}

            # 方案1: 如果 PPTAgent 提供 REST API
            # 调用 /api/generate 端点
            response = await self._call_api(
                endpoint="/api/generate",
                method="POST",
                data={
                    "prompt": prompt,
                    "template": options.get("template", "default"),
                    "style": options.get("style", "professional"),
                    "output_format": options.get("output_format", "pptx"),
                }
            )

            if response.get("success"):
                return {
                    "success": True,
                    "content": response.get("content", ""),
                    "file_path": response.get("file_path"),
                    "metadata": response.get("metadata", {}),
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error"),
                }

        except Exception as e:
            logger.error(f"Error calling PPTAgent Docker service: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def generate_ppt_stream(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式生成 PPT（支持实时进度更新）

        Args:
            prompt: 用户输入的提示词
            options: 生成选项

        Yields:
            进度更新字典：
                - type: "progress" | "chunk" | "complete" | "error"
                - progress: 进度百分比 (0-100)
                - content: 内容片段
                - error: 错误信息
        """
        try:
            options = options or {}

            # 方案2: 使用 Server-Sent Events (SSE) 或 WebSocket
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate/stream",
                json={
                    "prompt": prompt,
                    "template": options.get("template", "default"),
                    "style": options.get("style", "professional"),
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        yield data

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }

    async def _call_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        调用 PPTAgent API

        Args:
            endpoint: API 端点
            method: HTTP 方法
            data: 请求数据

        Returns:
            API 响应
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
            }
        except Exception as e:
            logger.error(f"API call error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            response = await self._call_api("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        分析文档内容

        Args:
            file_path: 文档路径

        Returns:
            分析结果
        """
        try:
            response = await self._call_api(
                endpoint="/api/analyze",
                method="POST",
                data={"file_path": file_path}
            )
            return response
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def evaluate_ppt(self, file_path: str) -> Dict[str, Any]:
        """
        评估 PPT 质量

        Args:
            file_path: PPT 文件路径

        Returns:
            评估结果
        """
        try:
            response = await self._call_api(
                endpoint="/api/evaluate",
                method="POST",
                data={"file_path": file_path}
            )
            return response
        except Exception as e:
            logger.error(f"PPT evaluation error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# 全局实例
pptagent_docker_client = PPTAgentDockerClient(
    base_url=getattr(settings, "pptagent_docker_url", "http://deeppresenter-host:7861")
)
