from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
import os
import shutil
import uuid
from pathlib import Path
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["files"])

# 文件上传目录
UPLOAD_DIR = Path(settings.pptagent_workspace) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 生成文件目录
OUTPUT_DIR = Path(settings.pptagent_workspace) / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".pptx", ".ppt"}


@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """上传文件"""
    uploaded_files = []

    try:
        for file in files:
            # 检查文件扩展名
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {ext}。允许的类型: {', '.join(ALLOWED_EXTENSIONS)}",
                )

            # 生成唯一文件 ID
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}{ext}"
            file_path = UPLOAD_DIR / safe_filename

            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "safe_filename": safe_filename,
                "path": str(file_path),
                "size": os.path.getsize(file_path),
            })

        return {
            "status": "success",
            "files": uploaded_files,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{task_id}")
async def download_file(task_id: str, sample: int = None):
    """下载生成的 PPT/PDF 文件

    Args:
        task_id: 任务 ID
        sample: 样本索引（可选，用于多样本任务）
    """
    from app.services.task_service import TaskService

    # 获取任务信息
    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    file_path = None

    # 如果指定了样本索引，获取该样本的文件路径
    if sample is not None:
        if sample < 0 or sample >= len(task.samples):
            raise HTTPException(status_code=400, detail=f"Invalid sample index: {sample}")

        sample_obj = task.samples[sample]
        # 优先从样本的 file_path 获取
        if hasattr(sample_obj, 'file_path') and sample_obj.file_path:
            file_path = sample_obj.file_path
        else:
            # 尝试从 options 中的 generated_file_paths 获取
            file_paths = task.options.get("generated_file_paths", [])
            if sample < len(file_paths):
                file_path = file_paths[sample]

    # 如果没有指定样本或样本没有文件，使用任务的默认文件路径
    if not file_path:
        file_path = task.options.get("generated_file_path")

    if not file_path:
        raise HTTPException(status_code=404, detail="No file generated for this task")

    # 转换路径：DeepPresenter 容器使用 /opt/workspace，后端容器使用 /workspace
    if file_path.startswith("/opt/workspace"):
        file_path = file_path.replace("/opt/workspace", settings.pptagent_workspace, 1)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    # 根据文件扩展名确定 MIME 类型
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext in [".pptx", ".ppt"]:
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    else:
        media_type = "application/octet-stream"

    # 返回文件
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/templates")
async def list_templates():
    """获取可用的模板列表"""
    from app.services.deeppresenter_integration import deeppresenter_integration

    templates = deeppresenter_integration.get_available_templates()
    return {
        "templates": templates,
    }
