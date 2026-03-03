from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Any
import asyncio
import os
import shutil
import uuid
import tempfile
import zipfile
from pathlib import Path
from app.core.config import settings
from urllib.parse import unquote

router = APIRouter(prefix="/api", tags=["files"])

# 文件上传目录
UPLOAD_DIR = Path(settings.pptagent_workspace) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 生成文件目录
OUTPUT_DIR = Path(settings.pptagent_workspace) / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".pptx", ".ppt"}


def _resolve_generated_file_path(task: Any, sample: int = None) -> Path:
    """解析任务/样本生成文件路径并校验存在性。"""
    file_path = None

    if sample is not None:
        if sample < 0 or sample >= len(task.samples):
            raise HTTPException(status_code=400, detail=f"Invalid sample index: {sample}")

        sample_obj = task.samples[sample]
        if hasattr(sample_obj, "file_path") and sample_obj.file_path:
            file_path = sample_obj.file_path
        else:
            file_paths = task.options.get("generated_file_paths", [])
            if sample < len(file_paths):
                file_path = file_paths[sample]

    if not file_path:
        file_path = task.options.get("generated_file_path")

    if not file_path:
        raise HTTPException(status_code=404, detail="No file generated for this task")

    if file_path.startswith("/opt/workspace"):
        file_path = file_path.replace("/opt/workspace", settings.pptagent_workspace, 1)

    target_file = Path(file_path)
    if not target_file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {target_file}")

    return target_file


async def _run_command(command: list[str]) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return (
        process.returncode,
        stdout.decode(errors="ignore"),
        stderr.decode(errors="ignore"),
    )


async def _ensure_pdf_file(source_file: Path) -> Path:
    """确保存在可下载 PDF：源文件是 PDF 直接返回，否则尝试从 PPT/PPTX 转换。"""
    ext = source_file.suffix.lower()
    if ext == ".pdf":
        return source_file
    if ext not in {".pptx", ".ppt"}:
        raise HTTPException(status_code=400, detail=f"Unsupported source file type: {ext}")

    pdf_path = source_file.with_suffix(".pdf")
    if pdf_path.exists():
        try:
            if pdf_path.stat().st_size > 0 and pdf_path.stat().st_mtime >= source_file.stat().st_mtime:
                return pdf_path
        except OSError:
            pass

    errors: list[str] = []

    unoconvert_path = shutil.which("unoconvert")
    if unoconvert_path:
        code, stdout, stderr = await _run_command([unoconvert_path, str(source_file), str(pdf_path)])
        if code == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
            return pdf_path
        errors.append(stderr.strip() or stdout.strip() or f"unoconvert exited with code {code}")

    soffice_path = shutil.which("soffice")
    if soffice_path:
        with tempfile.TemporaryDirectory(prefix="soffice-profile-") as profile_dir:
            profile_uri = Path(profile_dir).as_uri()
            code, stdout, stderr = await _run_command(
                [
                    soffice_path,
                    f"-env:UserInstallation={profile_uri}",
                    "--headless",
                    "--convert-to",
                    "pdf",
                    str(source_file),
                    "--outdir",
                    str(source_file.parent),
                ]
            )
        if code == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
            return pdf_path
        errors.append(stderr.strip() or stdout.strip() or f"soffice exited with code {code}")

    if not unoconvert_path and not soffice_path:
        detail = "PDF converter not found. Please install soffice or unoconvert."
    else:
        detail = "Failed to convert PPT to PDF: " + " | ".join(err for err in errors if err)
    raise HTTPException(status_code=500, detail=detail)


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

    target_file = _resolve_generated_file_path(task, sample)

    # 根据文件扩展名确定 MIME 类型
    filename = target_file.name
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        media_type = "application/pdf"
    elif ext in [".pptx", ".ppt"]:
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    else:
        media_type = "application/octet-stream"

    # 返回文件
    return FileResponse(
        path=target_file,
        filename=filename,
        media_type=media_type,
    )


@router.get("/download/{task_id}/pdf")
async def download_pdf_file(task_id: str, sample: int = None):
    """下载生成文件对应的 PDF 版本（按需从 PPT/PPTX 转换）。"""
    from app.services.task_service import TaskService

    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    source_file = _resolve_generated_file_path(task, sample)
    pdf_file = await _ensure_pdf_file(source_file)

    return FileResponse(
        path=pdf_file,
        filename=pdf_file.name,
        media_type="application/pdf",
    )


@router.get("/download/{task_id}/workspace-zip")
async def download_workspace_zip(task_id: str, background_tasks: BackgroundTasks, sample: int = None):
    """打包单次 PPT 生成所在目录为 ZIP，排除 history/.history 目录及隐藏文件。"""
    from app.services.task_service import TaskService

    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    target_file = _resolve_generated_file_path(task, sample)
    base_dir = target_file.parent

    if not base_dir.exists():
        raise HTTPException(status_code=404, detail=f"Workspace folder not found: {base_dir}")

    tmp_dir = Path(tempfile.gettempdir())
    zip_path = tmp_dir / f"{task_id}-workspace.zip"

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                # 排除 history/.history 目录和隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() != 'history']
                for fname in files:
                    if fname.startswith('.'):
                        continue
                    full_path = Path(root) / fname
                    if full_path.is_file():
                        rel_path = full_path.relative_to(base_dir)
                        zipf.write(full_path, rel_path)

    except Exception as e:
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workspace zip: {e}")

    background_tasks.add_task(lambda p=zip_path: p.unlink(missing_ok=True))

    return FileResponse(
        path=zip_path,
        filename=f"{task_id}-workspace.zip",
        media_type="application/zip",
        background=background_tasks,
    )


@router.get("/preview/slide")
async def preview_slide(task_id: str, html_file: str, sample: int = None):
    """预览单页 HTML（用于 inspect_slide 实时查看）。"""
    from app.services.task_service import TaskService

    # html_file 可能是 URL 编码，需解码
    html_file = unquote(html_file)

    # 首先尝试从任务服务获取任务信息
    task = await TaskService.get_task(task_id)
    base_dir = None

    if task:
        file_path = None

        # 与下载逻辑一致，确定基准目录
        if sample is not None:
            if sample < 0 or sample >= len(task.samples):
                raise HTTPException(status_code=400, detail=f"Invalid sample index: {sample}")
            sample_obj = task.samples[sample]
            if hasattr(sample_obj, 'file_path') and sample_obj.file_path:
                file_path = sample_obj.file_path
            else:
                file_paths = task.options.get("generated_file_paths", [])
                if sample < len(file_paths):
                    file_path = file_paths[sample]

        if not file_path:
            file_path = task.options.get("generated_file_path")

        if file_path:
            if file_path.startswith("/opt/workspace"):
                file_path = file_path.replace("/opt/workspace", settings.pptagent_workspace, 1)
            base_dir = Path(file_path).parent.resolve()

    # 如果无法从任务获取基准目录，尝试直接定位任务目录
    if not base_dir:
        workspace_root = Path(settings.pptagent_workspace).resolve()
        task_dir = None

        try:
            # 搜索所有日期目录下的任务目录
            for date_dir in workspace_root.iterdir():
                if not date_dir.is_dir() or date_dir.name.startswith('.'):
                    continue
                possible = date_dir / task_id
                if possible.is_dir():
                    task_dir = possible
                    break
        except Exception:
            task_dir = None

        if not task_dir:
            raise HTTPException(status_code=404, detail="Task directory not found")

        base_dir = task_dir.resolve()

    # 构建HTML文件路径
    candidate = Path(html_file)
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()

    # 仅允许访问基准目录下文件
    try:
        candidate.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid html_file path")

    if not candidate.exists() or candidate.suffix.lower() != ".html":
        raise HTTPException(status_code=404, detail="HTML file not found")

    # 读取HTML内容并重写图片路径
    with open(candidate, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 重写相对路径的图片为API路径
    import re

    sample_suffix = f"?sample={sample}" if sample is not None else ""

    def append_sample_query(url: str) -> str:
        if sample is None:
            return url
        if "sample=" in url:
            return url
        return f"{url}{'&' if '?' in url else '?'}sample={sample}"

    def replace_relative_img_src(match):
        full_match = match.group(0)
        src_value = match.group(1)

        # 直接返回外链与 data URI
        if src_value.startswith(('http://', 'https://', 'data:')):
            return full_match

        # 对已有 API 资源路径补充 sample 参数（多样本预览时）
        if src_value.startswith('/api/preview/asset/'):
            new_src = append_sample_query(src_value)
            return f'src="{new_src}"'

        if src_value.startswith('/api/'):
            return full_match

        # 处理相对路径
        if src_value.startswith('../'):
            # ../assets/image.png -> assets/image.png
            relative_path = src_value.replace('../', '')
            new_src = f"/api/preview/asset/{task_id}/{relative_path}{sample_suffix}"
            return f'src="{new_src}"'
        elif src_value.startswith('./'):
            # ./image.png -> slides/image.png (假设HTML在slides目录)
            relative_path = src_value.replace('./', 'slides/')
            new_src = f"/api/preview/asset/{task_id}/{relative_path}{sample_suffix}"
            return f'src="{new_src}"'
        elif not src_value.startswith('/'):
            # image.png -> slides/image.png
            new_src = f"/api/preview/asset/{task_id}/slides/{src_value}{sample_suffix}"
            return f'src="{new_src}"'

        return full_match

    # 替换所有img src属性
    html_content = re.sub(r'src="([^"]+)"', replace_relative_img_src, html_content)
    html_content = re.sub(r"src='([^']+)'", lambda m: replace_relative_img_src(m).replace('"', "'"), html_content)

    # 处理CSS中的background-image和url()
    def replace_css_url(match):
        full_match = match.group(0)
        url_value = match.group(1).strip('\'"')

        # 跳过 HTTP 路径或 data URI
        if url_value.startswith(('http://', 'https://', 'data:')):
            return full_match

        # 对已有 API 资源路径补充 sample 参数（多样本预览时）
        if url_value.startswith('/api/preview/asset/'):
            new_url = append_sample_query(url_value)
            return f'url("{new_url}")'

        if url_value.startswith('/api/'):
            return full_match

        # 处理绝对路径（如 /opt/workspace/...）
        if url_value.startswith('/opt/workspace/'):
            # 提取相对于工作区的路径
            # /opt/workspace/20260301/6dba2423/image.png -> image.png
            parts = url_value.split('/')
            if len(parts) >= 5:
                # 找到短ID后面的路径部分
                short_id_index = -1
                for i, part in enumerate(parts):
                    if len(part) == 8 and i >= 4:  # 短ID通常是8位
                        short_id_index = i
                        break
                if short_id_index > 0 and short_id_index + 1 < len(parts):
                    relative_path = '/'.join(parts[short_id_index + 1:])
                    new_url = f"/api/preview/asset/{task_id}/{relative_path}{sample_suffix}"
                    return f'url("{new_url}")'
            return full_match

        # 处理相对路径
        if url_value.startswith('../'):
            relative_path = url_value.replace('../', '')
            new_url = f"/api/preview/asset/{task_id}/{relative_path}{sample_suffix}"
            return f'url("{new_url}")'
        elif url_value.startswith('./'):
            relative_path = url_value.replace('./', 'slides/')
            new_url = f"/api/preview/asset/{task_id}/{relative_path}{sample_suffix}"
            return f'url("{new_url}")'
        elif not url_value.startswith('/'):
            new_url = f"/api/preview/asset/{task_id}/slides/{url_value}{sample_suffix}"
            return f'url("{new_url}")'

        return full_match

    # 替换CSS中的url()
    html_content = re.sub(r'url\(["\']?([^)]+?)["\']?\)', replace_css_url, html_content)

    # 返回修改后的HTML内容
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f"inline; filename=\"{candidate.name}\"",
        },
    )


@router.get("/preview/asset/{task_id}/{asset_path:path}")
async def preview_asset(task_id: str, asset_path: str, sample: int = None):
    """代理任务工作区中的静态资源（图片、CSS、JS等）。

    Args:
        task_id: 任务 ID
        asset_path: 资源相对路径（如 assets/image.png）
        sample: 样本索引（可选，用于多样本任务）
    """
    from app.services.task_service import TaskService

    # asset_path 可能是 URL 编码，需解码
    asset_path = unquote(asset_path)

    # 首先尝试从任务服务获取任务信息
    task = await TaskService.get_task(task_id)
    base_dir = None

    if task:
        file_path = None

        # 与下载逻辑一致，确定基准目录
        if sample is not None:
            if sample < 0 or sample >= len(task.samples):
                raise HTTPException(status_code=400, detail=f"Invalid sample index: {sample}")
            sample_obj = task.samples[sample]
            if hasattr(sample_obj, 'file_path') and sample_obj.file_path:
                file_path = sample_obj.file_path
            else:
                file_paths = task.options.get("generated_file_paths", [])
                if sample < len(file_paths):
                    file_path = file_paths[sample]

        if not file_path:
            file_path = task.options.get("generated_file_path")

        if file_path:
            if file_path.startswith("/opt/workspace"):
                file_path = file_path.replace("/opt/workspace", settings.pptagent_workspace, 1)
            base_dir = Path(file_path).parent.resolve()

    # 如果无法从任务获取基准目录，尝试直接定位任务目录
    if not base_dir:
        workspace_root = Path(settings.pptagent_workspace).resolve()
        task_dir = None

        try:
            # 搜索所有日期目录下的任务目录
            for date_dir in workspace_root.iterdir():
                if not date_dir.is_dir() or date_dir.name.startswith('.'):
                    continue
                possible = date_dir / task_id
                if possible.is_dir():
                    task_dir = possible
                    break
        except Exception:
            task_dir = None

        if not task_dir:
            raise HTTPException(status_code=404, detail="Task directory not found")

        base_dir = task_dir.resolve()

    # 构建资源文件路径
    candidate = Path(asset_path)
    if not candidate.is_absolute():
        candidate = (base_dir / asset_path).resolve()

    # 安全检查：仅允许访问基准目录下文件
    try:
        candidate.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset path")

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    # 根据文件扩展名确定 MIME 类型
    ext = candidate.suffix.lower()
    mime_types = {
        # 图片
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".ico": "image/x-icon",
        # 样式和脚本
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        # 字体
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        # 其他
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }
    media_type = mime_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=candidate,
        filename=candidate.name,
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
