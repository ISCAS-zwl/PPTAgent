"""
DeepPresenter API Server
提供 HTTP API 接口供外部系统调用 AgentLoop 生成 PPT
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from deeppresenter.main import AgentLoop
from deeppresenter.utils.config import GLOBAL_CONFIG
from deeppresenter.utils.constants import WORKSPACE_BASE
from deeppresenter.utils.typings import ChatMessage, ConvertType, InputRequest, Role

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepPresenterAPI")

# 创建 FastAPI 应用
app = FastAPI(
    title="DeepPresenter API",
    description="API for PPT generation using DeepPresenter/PPTAgent",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储活跃的任务
active_tasks: Dict[str, Dict[str, Any]] = {}


# ============ Request/Response Models ============

class GenerateRequest(BaseModel):
    """PPT 生成请求"""
    task_id: Optional[str] = None
    prompt: str
    attachments: list[str] = []
    num_pages: Optional[str] = None
    template: Optional[str] = None
    convert_type: str = "freeform"  # freeform | templates
    powerpoint_type: str = "16:9"  # 16:9 | 4:3 | A1


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str  # pending | running | completed | failed
    progress: int = 0
    message: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None


class TemplatesResponse(BaseModel):
    """模板列表响应"""
    templates: list[str]


# ============ Helper Functions ============

def get_convert_type(convert_type_str: str) -> ConvertType:
    """转换类型字符串到枚举"""
    if convert_type_str == "templates":
        return ConvertType.PPTAGENT
    return ConvertType.DEEPPRESENTER


async def generate_ppt_stream(task_id: str, request: GenerateRequest):
    """流式生成 PPT 并通过 SSE 返回进度"""
    try:
        # 更新任务状态
        active_tasks[task_id] = {
            "status": "running",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
        }

        # 创建 AgentLoop
        session_id = f"{datetime.now().strftime('%Y%m%d')}/{task_id[:8]}"
        loop = AgentLoop(session_id=session_id)

        # 创建输入请求
        input_request = InputRequest(
            instruction=request.prompt,
            attachments=request.attachments,
            num_pages=request.num_pages,
            template=request.template if request.template != "auto" else None,
            convert_type=get_convert_type(request.convert_type),
        )

        # 保存文件路径，在循环结束后发送 complete 事件
        file_path = None

        # 进度跟踪
        slides_generated = 0
        total_slides = 10  # 默认估计10页，后续会从 inspect_manuscript 结果中更新
        current_phase = "research"  # research -> design -> convert

        # 流式处理
        async for yield_msg in loop.run(input_request):
            if isinstance(yield_msg, (str, Path)):
                # 文件生成完成 - 保存路径，稍后发送
                file_path = str(yield_msg)
                logger.info(f"[SSE] File path received: {file_path}")
                active_tasks[task_id].update({
                    "status": "completed",
                    "progress": 100,
                    "file_path": file_path,
                })

            elif isinstance(yield_msg, ChatMessage):
                # Agent 消息
                role_value = yield_msg.role.value if hasattr(yield_msg.role, 'value') else str(yield_msg.role)

                message_data = {
                    "type": "message",
                    "role": role_value,
                    "content": yield_msg.text or "",
                }

                # 添加工具调用信息
                if yield_msg.tool_calls:
                    tool_calls_data = []
                    for tool_call in yield_msg.tool_calls:
                        tool_name = tool_call.function.name
                        tool_calls_data.append({
                            "name": tool_name,
                            "arguments": tool_call.function.arguments if hasattr(tool_call.function, "arguments") else "",
                        })

                        # 跟踪进度 - 基于工具调用
                        if tool_name == "generate_slide":
                            # PPTAgent 模式：每次 generate_slide 表示一页完成
                            slides_generated += 1
                            current_phase = "design"
                            # 进度：research 20% + design 70% + convert 10%
                            progress = min(20 + int(70 * slides_generated / total_slides), 90)
                            active_tasks[task_id]["progress"] = progress
                            yield {
                                "event": "progress",
                                "data": json.dumps({
                                    "type": "progress",
                                    "progress": progress,
                                    "slides_generated": slides_generated,
                                    "total_slides": total_slides,
                                    "phase": current_phase,
                                })
                            }
                        elif tool_name == "save_generated_slides":
                            # PPTAgent 模式：保存幻灯片，进入转换阶段
                            current_phase = "convert"
                            active_tasks[task_id]["progress"] = 90
                            yield {
                                "event": "progress",
                                "data": json.dumps({
                                    "type": "progress",
                                    "progress": 90,
                                    "slides_generated": slides_generated,
                                    "total_slides": total_slides,
                                    "phase": current_phase,
                                })
                            }
                        elif tool_name == "finalize" and current_phase == "research":
                            # Research 阶段完成
                            current_phase = "design"
                            active_tasks[task_id]["progress"] = 20
                            yield {
                                "event": "progress",
                                "data": json.dumps({
                                    "type": "progress",
                                    "progress": 20,
                                    "slides_generated": 0,
                                    "total_slides": total_slides,
                                    "phase": current_phase,
                                })
                            }

                    message_data["tool_calls"] = tool_calls_data

                # 检测 tool 消息中的关键信息
                if role_value == "tool" and yield_msg.text:
                    text = yield_msg.text

                    # 检测 inspect_manuscript 返回的实际页数
                    if "num_pages" in text:
                        try:
                            import ast
                            # 尝试解析工具返回的字典
                            tool_result = ast.literal_eval(text) if text.startswith("{") else None
                            if tool_result and isinstance(tool_result, dict) and "num_pages" in tool_result:
                                total_slides = tool_result["num_pages"]
                                logger.info(f"[SSE] Updated total_slides from inspect_manuscript: {total_slides}")
                        except Exception as e:
                            # 尝试用正则提取
                            import re
                            match = re.search(r"['\"]?num_pages['\"]?\s*[:=]\s*(\d+)", text)
                            if match:
                                total_slides = int(match.group(1))
                                logger.info(f"[SSE] Updated total_slides from regex: {total_slides}")

                    # 检测 Design agent 的 HTML 文件生成（freeform 模式）
                    if "slide_" in text and ".html" in text:
                        import re
                        matches = re.findall(r'slide_(\d+)\.html', text)
                        if matches:
                            slide_num = max(int(m) for m in matches)
                            if slide_num > slides_generated:
                                slides_generated = slide_num
                                current_phase = "design"
                                progress = min(20 + int(70 * slides_generated / total_slides), 90)
                                active_tasks[task_id]["progress"] = progress
                                yield {
                                    "event": "progress",
                                    "data": json.dumps({
                                        "type": "progress",
                                        "progress": progress,
                                        "slides_generated": slides_generated,
                                        "total_slides": total_slides,
                                        "phase": current_phase,
                                    })
                                }

                yield {
                    "event": "message",
                    "data": json.dumps(message_data)
                }

        # 收集 token 统计
        logger.info(f"[SSE] Collecting token stats, file_path={file_path}")
        token_stats = collect_token_stats(loop)
        yield {
            "event": "stats",
            "data": json.dumps({
                "type": "stats",
                "token_stats": token_stats,
            })
        }

        # 在最后发送 complete 事件（确保在所有消息之后）
        if file_path:
            logger.info(f"[SSE] Sending complete event with file_path: {file_path}")
            yield {
                "event": "complete",
                "data": json.dumps({
                    "type": "file",
                    "file_path": file_path,
                    "message": "PPT 生成完成",
                })
            }
        else:
            # 如果没有文件路径，发送错误
            logger.warning("[SSE] No file path, sending error event")
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "error",
                    "error": "No file generated",
                })
            }

    except Exception as e:
        logger.error(f"Error generating PPT: {e}")
        import traceback
        traceback.print_exc()

        active_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
        })
        yield {
            "event": "error",
            "data": json.dumps({
                "type": "error",
                "error": str(e),
            })
        }


def collect_token_stats(loop: AgentLoop) -> Dict[str, Any]:
    """收集 token 统计信息"""
    stats = {}
    try:
        if hasattr(loop, "research_agent") and loop.research_agent:
            stats["research_agent"] = {
                "prompt": getattr(loop.research_agent.cost, "prompt", 0),
                "completion": getattr(loop.research_agent.cost, "completion", 0),
                "total": getattr(loop.research_agent.cost, "total", 0),
                "model": loop.config.research_agent.model_name,
            }

        if hasattr(loop, "designagent") and loop.designagent:
            stats["design_agent"] = {
                "prompt": getattr(loop.designagent.cost, "prompt", 0),
                "completion": getattr(loop.designagent.cost, "completion", 0),
                "total": getattr(loop.designagent.cost, "total", 0),
                "model": loop.config.design_agent.model_name,
            }
        elif hasattr(loop, "pptagent") and loop.pptagent:
            stats["ppt_agent"] = {
                "prompt": getattr(loop.pptagent.cost, "prompt", 0),
                "completion": getattr(loop.pptagent.cost, "completion", 0),
                "total": getattr(loop.pptagent.cost, "total", 0),
                "model": loop.config.research_agent.model_name,
            }
    except Exception as e:
        logger.error(f"Error collecting token stats: {e}")
    return stats


# ============ API Endpoints ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "DeepPresenter API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/generate")
async def generate_ppt(request: GenerateRequest):
    """
    生成 PPT（SSE 流式响应）

    返回 Server-Sent Events 流，包含：
    - message: Agent 消息
    - complete: 生成完成，包含文件路径
    - stats: Token 统计
    - error: 错误信息
    """
    task_id = request.task_id or str(uuid.uuid4())

    return EventSourceResponse(
        generate_ppt_stream(task_id, request),
        media_type="text/event-stream",
    )


@app.post("/api/generate/sync")
async def generate_ppt_sync(request: GenerateRequest) -> TaskStatusResponse:
    """
    同步生成 PPT（等待完成后返回）

    注意：此接口会阻塞直到生成完成，可能需要较长时间
    """
    task_id = request.task_id or str(uuid.uuid4())

    try:
        # 创建 AgentLoop
        session_id = f"{datetime.now().strftime('%Y%m%d')}/{task_id[:8]}"
        loop = AgentLoop(session_id=session_id)

        # 创建输入请求
        input_request = InputRequest(
            instruction=request.prompt,
            attachments=request.attachments,
            num_pages=request.num_pages,
            template=request.template if request.template != "auto" else None,
            convert_type=get_convert_type(request.convert_type),
        )

        file_path = None
        async for yield_msg in loop.run(input_request):
            if isinstance(yield_msg, (str, Path)):
                file_path = str(yield_msg)
                break

        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            progress=100,
            file_path=file_path,
            message="PPT 生成完成",
        )

    except Exception as e:
        logger.error(f"Error generating PPT: {e}")
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=str(e),
        )


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """获取任务状态"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task.get("status", "unknown"),
        progress=task.get("progress", 0),
        file_path=task.get("file_path"),
        error=task.get("error"),
    )


@app.get("/api/templates")
async def list_templates() -> TemplatesResponse:
    """获取可用的模板列表"""
    try:
        from pptagent import PPTAgentServer
        templates = PPTAgentServer.list_templates()
        return TemplatesResponse(templates=templates)
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return TemplatesResponse(templates=[])


@app.get("/api/download/{task_id}")
async def download_file(task_id: str):
    """下载生成的文件"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]
    file_path = task.get("file_path")

    if not file_path:
        raise HTTPException(status_code=404, detail="No file generated for this task")

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    filename = Path(file_path).name
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if file_path.endswith(".pdf"):
        media_type = "application/pdf"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到工作空间"""
    try:
        # 创建上传目录
        upload_dir = WORKSPACE_BASE / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix
        safe_filename = f"{file_id}{ext}"
        file_path = upload_dir / safe_filename

        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============ Main Entry ============

def run_server(host: str = "0.0.0.0", port: int = 8080):
    """运行 API 服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys
    host = "0.0.0.0"
    port = 8080

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    run_server(host, port)
