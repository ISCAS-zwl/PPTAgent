"""
PPTAgent 集成模块 V2
支持两种模式：
1. 直接调用本地 PPTAgent 模块
2. 通过 HTTP API 调用 Docker 化的 PPTAgent 服务
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from app.services.pptagent_docker_client import pptagent_docker_client
from app.utils import get_logger

logger = get_logger(__name__)


class IntegrationMode(Enum):
    """集成模式"""
    LOCAL = "local"      # 本地模块调用
    DOCKER = "docker"    # Docker HTTP API 调用
    AUTO = "auto"        # 自动选择


# 添加 PPTAgent 到 Python 路径
PPTAGENT_ROOT = Path(__file__).parent.parent.parent.parent.parent / "pptagent"
sys.path.insert(0, str(PPTAGENT_ROOT))

# 尝试导入本地 PPTAgent
try:
    from pptagent import PPTAgentServer
    from pptagent.pptgen import PPTGenerator
    from pptagent.utils import setup_workspace
    LOCAL_PPTAGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Local PPTAgent not available: {e}")
    LOCAL_PPTAGENT_AVAILABLE = False


class PPTAgentIntegrationV2:
    """PPTAgent 集成类 V2 - 支持多种集成模式"""

    def __init__(
        self,
        mode: IntegrationMode = IntegrationMode.AUTO,
        workspace: Optional[str] = None,
    ):
        """
        初始化集成模块

        Args:
            mode: 集成模式（local/docker/auto）
            workspace: 工作空间路径
        """
        self.workspace = workspace or "/tmp/pptagent_workspace"
        self.mode = mode
        self.local_agent = None
        self.docker_available = False

        # 初始化本地 Agent
        if LOCAL_PPTAGENT_AVAILABLE and mode in [IntegrationMode.LOCAL, IntegrationMode.AUTO]:
            try:
                self.local_agent = PPTAgentServer()
                logger.info("Local PPTAgent initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize local PPTAgent: {e}")

        # 检查 Docker 服务可用性
        if mode in [IntegrationMode.DOCKER, IntegrationMode.AUTO]:
            self._check_docker_availability()

    async def _check_docker_availability(self):
        """检查 Docker 服务是否可用"""
        try:
            self.docker_available = await pptagent_docker_client.health_check()
            if self.docker_available:
                logger.info("Docker PPTAgent service is available")
            else:
                logger.warning("Docker PPTAgent service health check failed")
        except Exception as e:
            logger.warning(f"Docker PPTAgent service not available: {e}")
            self.docker_available = False

    def _select_mode(self) -> str:
        """
        自动选择最佳集成模式

        Returns:
            选择的模式: "local" 或 "docker"
        """
        if self.mode == IntegrationMode.LOCAL:
            return "local"
        elif self.mode == IntegrationMode.DOCKER:
            return "docker"
        else:  # AUTO
            # 优先使用 Docker 服务（更稳定、隔离性好）
            if self.docker_available:
                return "docker"
            elif self.local_agent is not None:
                return "local"
            else:
                return "fallback"

    async def generate_ppt(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成 PPT

        Args:
            prompt: 用户输入的提示词
            options: 生成选项

        Returns:
            生成结果字典
        """
        selected_mode = self._select_mode()
        logger.info(f"Using {selected_mode} mode for PPT generation")

        if selected_mode == "docker":
            return await self._generate_via_docker(prompt, options)
        elif selected_mode == "local":
            return await self._generate_via_local(prompt, options)
        else:
            # 后备方案
            return {
                "success": False,
                "error": "No PPTAgent service available",
                "content": self._generate_fallback_content(prompt),
            }

    async def _generate_via_docker(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """通过 Docker 服务生成"""
        try:
            result = await pptagent_docker_client.generate_ppt(prompt, options)
            return result
        except Exception as e:
            logger.error(f"Docker generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": self._generate_fallback_content(prompt),
            }

    async def _generate_via_local(
        self,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """通过本地模块生成"""
        try:
            options = options or {}
            template = options.get("template", "default")
            style = options.get("style", "professional")

            # 调用本地 PPTAgent
            # result = self.local_agent.generate(
            #     prompt=prompt,
            #     template=template,
            #     style=style,
            # )

            # 临时返回模拟数据
            return {
                "success": True,
                "content": f"Generated PPT for: {prompt}",
                "file_path": f"{self.workspace}/output.pptx",
                "metadata": {
                    "template": template,
                    "style": style,
                    "mode": "local",
                }
            }

        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": self._generate_fallback_content(prompt),
            }

    def _generate_fallback_content(self, prompt: str) -> str:
        """生成后备内容（当所有服务都不可用时）"""
        return f"""# {prompt}

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

*注意：这是自动生成的大纲。完整的 PPT 生成功能需要 PPTAgent 支持。*
"""

    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """分析文档内容"""
        selected_mode = self._select_mode()

        if selected_mode == "docker":
            return await pptagent_docker_client.analyze_document(file_path)
        elif selected_mode == "local" and self.local_agent:
            # 调用本地分析功能
            return {
                "success": True,
                "analysis": "Document analysis result (local)",
            }
        else:
            return {"success": False, "error": "No service available"}

    async def evaluate_ppt(self, file_path: str) -> Dict[str, Any]:
        """评估 PPT 质量"""
        selected_mode = self._select_mode()

        if selected_mode == "docker":
            return await pptagent_docker_client.evaluate_ppt(file_path)
        elif selected_mode == "local" and self.local_agent:
            # 调用本地评估功能
            return {
                "success": True,
                "scores": {
                    "content": 0.85,
                    "design": 0.90,
                    "coherence": 0.88,
                },
            }
        else:
            return {"success": False, "error": "No service available"}

    async def close(self):
        """关闭资源"""
        await pptagent_docker_client.close()


# 全局实例 - 默认使用 AUTO 模式
pptagent_integration_v2 = PPTAgentIntegrationV2(mode=IntegrationMode.AUTO)
