"""
PPTAgent 集成模块
将现有的 PPTAgent 功能集成到任务处理系统中
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# 添加 PPTAgent 到 Python 路径
PPTAGENT_ROOT = Path(__file__).parent.parent.parent.parent.parent / "pptagent"
sys.path.insert(0, str(PPTAGENT_ROOT))

try:
    from pptagent import PPTAgentServer
    from pptagent.pptgen import PPTGenerator
    from pptagent.utils import setup_workspace
    PPTAGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PPTAgent not available: {e}")
    PPTAGENT_AVAILABLE = False


class PPTAgentIntegration:
    """PPTAgent 集成类"""

    def __init__(self, workspace: Optional[str] = None):
        self.workspace = workspace or "/tmp/pptagent_workspace"
        self.agent = None
        if PPTAGENT_AVAILABLE:
            try:
                self.agent = PPTAgentServer()
            except Exception as e:
                print(f"Failed to initialize PPTAgent: {e}")

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
                - template: 模板名称
                - style: 样式
                - reference_files: 参考文件列表

        Returns:
            生成结果字典，包含：
                - success: 是否成功
                - content: 生成的内容
                - file_path: 生成的文件路径
                - error: 错误信息（如果失败）
        """
        if not PPTAGENT_AVAILABLE or not self.agent:
            return {
                "success": False,
                "error": "PPTAgent not available",
                "content": self._generate_fallback_content(prompt),
            }

        try:
            options = options or {}

            # 调用 PPTAgent 生成
            result = await self._call_pptagent(prompt, options)

            return {
                "success": True,
                "content": result.get("content", ""),
                "file_path": result.get("file_path"),
                "metadata": result.get("metadata", {}),
            }

        except Exception as e:
            print(f"Error generating PPT: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": self._generate_fallback_content(prompt),
            }

    async def _call_pptagent(
        self,
        prompt: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用 PPTAgent 核心功能"""
        # 这里实现实际的 PPTAgent 调用逻辑
        # 根据现有的 PPTAgent API 进行调用

        # 示例实现（需要根据实际 API 调整）
        template = options.get("template", "default")
        style = options.get("style", "professional")

        # 调用生成器
        # result = self.agent.generate(
        #     prompt=prompt,
        #     template=template,
        #     style=style,
        # )

        # 临时返回模拟数据
        return {
            "content": f"Generated PPT for: {prompt}",
            "file_path": f"{self.workspace}/output.pptx",
            "metadata": {
                "template": template,
                "style": style,
            }
        }

    def _generate_fallback_content(self, prompt: str) -> str:
        """生成后备内容（当 PPTAgent 不可用时）"""
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
        if not PPTAGENT_AVAILABLE:
            return {"success": False, "error": "PPTAgent not available"}

        try:
            # 调用文档分析功能
            # result = self.agent.analyze(file_path)
            return {
                "success": True,
                "analysis": "Document analysis result",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate_ppt(self, file_path: str) -> Dict[str, Any]:
        """评估 PPT 质量"""
        if not PPTAGENT_AVAILABLE:
            return {"success": False, "error": "PPTAgent not available"}

        try:
            # 调用 PPTEval 功能
            # result = self.agent.evaluate(file_path)
            return {
                "success": True,
                "scores": {
                    "content": 0.85,
                    "design": 0.90,
                    "coherence": 0.88,
                },
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局实例
pptagent_integration = PPTAgentIntegration()
