import csv
import math
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP
from filelock import FileLock
from PIL import Image
from pptagent_pptx import Presentation
from pydantic import BaseModel

from deeppresenter.utils.config import DeepPresenterConfig
from deeppresenter.utils.log import info, set_logger, warning

Image.MAX_IMAGE_PIXELS = None  # only reading metadata, no actual decompression

mcp = FastMCP(name="Task")

CONFIG = DeepPresenterConfig.load_from_file(os.getenv("CONFIG_FILE"))


def _rewrite_image_link(match: re.Match[str], md_dir: Path, task_id: str = None) -> str:
    alt_text = match.group(1)
    target = match.group(2).strip()
    if not target:
        return match.group(0)
    parts = re.match(r"([^\s]+)(.*)", target)
    if not parts:
        return match.group(0)
    local_path = parts.group(1).strip("\"'")
    rest = parts.group(2)
    p = Path(local_path)
    if not p.is_absolute() and (md_dir / local_path).exists():
        p = md_dir / local_path
    if not p.exists():
        return match.group(0)

    updated_alt = alt_text
    try:
        with Image.open(p) as img:
            width, height = img.size
        if width > 0 and height > 0 and not re.search(r"\b\d+:\d+\b", updated_alt):
            factor = math.gcd(width, height)
            ratio = f"{width // factor}:{height // factor}"
            updated_alt = f"{updated_alt}, {ratio}" if updated_alt else ratio
    except OSError:
        warning(f"Failed to get image size for {p}")

    # Convert image path to API URL for frontend access
    # If task_id is provided, use API endpoint; otherwise fall back to absolute path
    if task_id:
        # Get relative path from workspace root
        try:
            # Try to find the relative path from the task directory
            abs_path = p.resolve()
            # Extract the relative path after the task_id directory
            path_parts = abs_path.parts
            if task_id in path_parts:
                task_idx = path_parts.index(task_id)
                relative_path = "/".join(path_parts[task_idx + 1:])
                new_path = f"/api/preview/asset/{task_id}/{relative_path}"
            else:
                # Fallback to absolute path if task_id not found in path
                new_path = abs_path.as_posix()
        except Exception as e:
            warning(f"Failed to convert image path to API URL: {e}")
            new_path = p.resolve().as_posix()
    else:
        # Fallback to absolute path for backward compatibility
        new_path = p.resolve().as_posix()

    return f"![{updated_alt}]({new_path}{rest})"


class Todo(BaseModel):
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed", "skipped"]


LOCAL_TODO_CSV_PATH = Path("todo.csv")
LOCAL_TODO_LOCK_PATH = Path(".todo.csv.lock")


def _load_todos() -> list[Todo]:
    """Load todos from CSV file."""
    if not LOCAL_TODO_CSV_PATH.exists():
        return []

    lock = FileLock(LOCAL_TODO_LOCK_PATH)
    with lock:
        with open(LOCAL_TODO_CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [Todo(**row) for row in reader]


def _save_todos(todos: list[Todo]) -> None:
    """Save todos to CSV file."""
    lock = FileLock(LOCAL_TODO_LOCK_PATH)
    with lock:
        with open(LOCAL_TODO_CSV_PATH, "w", encoding="utf-8", newline="") as f:
            if todos:
                fieldnames = ["id", "content", "status"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for todo in todos:
                    writer.writerow(todo.model_dump())


@mcp.tool()
def todo_create(todo_content: str) -> str:
    """
    Create a new todo item and add it to the todo list.

    Args:
        todo_content (str): The content/description of the todo item

    Returns:
        str: Confirmation message with the created todo's ID
    """
    todos = _load_todos()
    new_id = str(len(todos))
    new_todo = Todo(id=new_id, content=todo_content, status="pending")
    todos.append(new_todo)
    _save_todos(todos)
    return f"Todo {new_id} created"


@mcp.tool()
def todo_update(
    idx: int,
    todo_content: str = None,
    status: Literal["completed", "in_progress", "skipped"] = None,
) -> str:
    """
    Update an existing todo item's content or status.

    Args:
        idx (int): The index of the todo item to update
        todo_content (str, optional): New content for the todo item
        status (Literal["completed", "in_progress", "skipped"], optional): New status for the todo item

    Returns:
        str: Confirmation message with the updated todo's ID
    """
    todos = _load_todos()
    assert 0 <= idx < len(todos), f"Invalid todo index: {idx}"

    if todo_content is not None:
        todos[idx].content = todo_content
    if status is not None:
        todos[idx].status = status
    _save_todos(todos)
    return "Todo updated successfully"


@mcp.tool()
def todo_list() -> str | list[Todo]:
    """
    Get the current todo list or check if all todos are completed.

    Returns:
        str | list[Todo]: Either a completion message if all todos are done/skipped,
                         or the current list of todo items
    """
    todos = _load_todos()
    if not todos or all(todo.status in ["completed", "skipped"] for todo in todos):
        LOCAL_TODO_CSV_PATH.unlink(missing_ok=True)
        return "All todos completed"
    else:
        return todos


# @mcp.tool()
def ask_user(question: str) -> str:
    """
    Ask the user a question when encounters an unclear requirement.
    """
    print(f"User input required: {question}")
    return input("Your answer: ")


@mcp.tool()
def thinking(thought: str):
    """This tool is for explicitly reasoning about the current task state and next actions."""
    info(f"Thought: {thought}")
    return thought


@mcp.tool(exclude_args=["agent_name"])
def finalize(outcome: str, agent_name: str = "") -> str:
    """
    When all tasks are finished, call this function to finalize the loop.
    Args:
        outcome (str): The path to the final outcome file or directory.
    """
    # here we conduct some final checks on agent's outcome
    path = Path(outcome)
    assert path.exists(), f"Outcome {outcome} does not exist"

    # Extract task_id from the current working directory
    task_id = None
    try:
        cwd = Path.cwd()
        # Task ID is typically the last directory in the path (e.g., /workspace/20260203/de59c0d0)
        task_id = cwd.name
    except Exception as e:
        warning(f"Failed to extract task_id from working directory: {e}")

    if agent_name == "Research":
        md_dir = path.parent
        assert path.suffix == ".md", (
            f"Outcome file should be a markdown file, got {path.suffix}"
        )
        with open(path, encoding="utf-8") as f:
            content = f.read()

        try:
            content = re.sub(
                r"!\[(.*?)\]\((.*?)\)",
                lambda match: _rewrite_image_link(match, md_dir, task_id),
                content,
            )
            shutil.copyfile(path, md_dir / ("." + path.name))
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            warning(f"Failed to rewrite image links: {e}")

    elif agent_name == "PPTAgent":
        assert path.is_file() and path.suffix == ".pptx", (
            f"Outcome file should be a pptx file, got {path.suffix}"
        )
        prs = Presentation(str(path))
        if len(prs.slides) <= 0:
            return "PPTX file should contain at least one slide"
    elif agent_name == "Design":
        html_files = list(path.glob("*.html"))
        if len(html_files) <= 0:
            return "Outcome path should be a directory containing HTML files"
        if not all(f.stem.startswith("slide_") for f in html_files):
            return "All HTML files should start with 'slide_'"

        # Rewrite image paths in HTML files to use API endpoints
        if task_id:
            try:
                for html_file in html_files:
                    _rewrite_html_image_paths(html_file, task_id)
                info(f"Rewrote image paths in {len(html_files)} HTML files")
            except Exception as e:
                warning(f"Failed to rewrite HTML image paths: {e}")
    else:
        warning(f"Unverifiable agent: {agent_name}")

    if LOCAL_TODO_CSV_PATH.exists():
        LOCAL_TODO_CSV_PATH.unlink()
    if LOCAL_TODO_LOCK_PATH.exists():
        LOCAL_TODO_LOCK_PATH.unlink()

    info(f"Agent {agent_name} finalized the outcome: {outcome}")
    return outcome


def _rewrite_html_image_paths(html_file: Path, task_id: str) -> None:
    """Rewrite absolute image paths in HTML files to use API endpoints.

    Args:
        html_file: Path to the HTML file
        task_id: Task ID for constructing API URLs
    """
    with open(html_file, encoding="utf-8") as f:
        content = f.read()

    # Pattern to match img src attributes with absolute paths
    # Matches: <img src="/opt/workspace/..." or src="/workspace/..."
    def replace_img_src(match):
        full_match = match.group(0)
        src_value = match.group(1)

        # Only process absolute file system paths
        if not (src_value.startswith("/opt/workspace") or src_value.startswith("/workspace")):
            return full_match

        # Extract relative path from the task directory
        try:
            src_path = Path(src_value)
            path_parts = src_path.parts

            # Find task_id in the path
            if task_id in path_parts:
                task_idx = path_parts.index(task_id)
                relative_path = "/".join(path_parts[task_idx + 1:])
                new_src = f"/api/preview/asset/{task_id}/{relative_path}"
                return f'src="{new_src}"'
        except Exception as e:
            warning(f"Failed to convert image path {src_value}: {e}")

        return full_match

    # Replace img src attributes
    content = re.sub(
        r'src="([^"]+)"',
        replace_img_src,
        content
    )

    # Also handle single quotes
    content = re.sub(
        r"src='([^']+)'",
        lambda m: replace_img_src(m).replace('"', "'") if replace_img_src(m) != m.group(0) else m.group(0),
        content
    )

    # Write back to file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    assert len(sys.argv) == 2, "Usage: python task.py <workspace>"
    work_dir = Path(sys.argv[1])
    assert work_dir.exists(), f"Workspace {work_dir} does not exist."
    os.chdir(work_dir)
    set_logger(f"task-{work_dir.stem}", work_dir / ".history" / "task.log")

    mcp.run(show_banner=False)
