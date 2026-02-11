import { CreateTaskRequest, CreateTaskResponse, UploadResponse, Task, Sample, Artifact } from "@/types/task";

// 动态获取 API 基础 URL
// 如果环境变量为空，则使用当前页面的 origin（适用于 Nginx 反向代理场景）
function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    return envUrl;
  }
  // 在浏览器环境中，使用当前页面的 origin
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  // 服务端渲染时的默认值
  return 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();

// 转换后端返回的 artifact
function transformArtifact(backendArtifact: any): Artifact | undefined {
  if (!backendArtifact) return undefined;
  return {
    type: backendArtifact.type,
    content: backendArtifact.content,
    language: backendArtifact.language,
  };
}

// 转换后端返回的 snake_case 字段为前端的 camelCase
function transformTask(backendTask: any): Task {
  return {
    id: backendTask.id,
    prompt: backendTask.prompt,
    status: backendTask.status,
    samples: (backendTask.samples || []).map((s: any): Sample => ({
      id: s.id,
      content: s.content || "",
      status: s.status,
      progress: s.progress || 0,
      createdAt: s.created_at ? s.created_at * 1000 : Date.now(),
      filePath: s.file_path,
      artifact: transformArtifact(s.artifact),
    })),
    progress: backendTask.progress || 0,
    createdAt: backendTask.created_at ? backendTask.created_at * 1000 : Date.now(),
    updatedAt: backendTask.updated_at ? backendTask.updated_at * 1000 : Date.now(),
    error: backendTask.error,
    artifact: transformArtifact(backendTask.artifact),
    pages: backendTask.pages,
    outputType: backendTask.output_type,
    uploadedFileId: backendTask.uploaded_file_id,
  };
}

export async function createTask(request: CreateTaskRequest): Promise<CreateTaskResponse> {
  // 转换 camelCase 为 snake_case
  const backendRequest = {
    prompt: request.prompt,
    sample_count: request.sampleCount || 1,
    pages: request.pages || "auto",
    output_type: request.outputType || "freeform",
    uploaded_file_id: request.uploadedFileId,
    options: request.options,
  };

  const response = await fetch(`${API_BASE_URL}/api/task/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(backendRequest),
  });

  if (!response.ok) {
    throw new Error(`Failed to create task: ${response.statusText}`);
  }

  const data = await response.json();
  // 转换 snake_case 为 camelCase
  return {
    taskId: data.task_id,
    status: data.status,
  };
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}`);

  if (!response.ok) {
    throw new Error(`Failed to get task: ${response.statusText}`);
  }

  const data = await response.json();
  return transformTask(data);
}

export async function listTasks(): Promise<Task[]> {
  const response = await fetch(`${API_BASE_URL}/api/tasks`);

  if (!response.ok) {
    throw new Error(`Failed to list tasks: ${response.statusText}`);
  }

  const data = await response.json();
  return data.map(transformTask);
}

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to upload files: ${response.statusText}`);
  }

  return response.json();
}

export function getDownloadUrl(taskId: string, sampleIndex?: number): string {
  if (sampleIndex !== undefined) {
    return `${API_BASE_URL}/api/download/${taskId}?sample=${sampleIndex}`;
  }
  return `${API_BASE_URL}/api/download/${taskId}`;
}

export function getWorkspaceZipUrl(taskId: string, sampleIndex?: number): string {
  if (sampleIndex !== undefined) {
    return `${API_BASE_URL}/api/download/${taskId}/workspace-zip?sample=${sampleIndex}`;
  }
  return `${API_BASE_URL}/api/download/${taskId}/workspace-zip`;
}

export function getSlidePreviewUrl(taskId: string, htmlFile: string, sampleIndex?: number): string {
  const encoded = encodeURIComponent(htmlFile);
  if (sampleIndex !== undefined) {
    return `${API_BASE_URL}/api/preview/slide?task_id=${taskId}&html_file=${encoded}&sample=${sampleIndex}`;
  }
  return `${API_BASE_URL}/api/preview/slide?task_id=${taskId}&html_file=${encoded}`;
}

export async function deleteTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete task: ${response.statusText}`);
  }
}

export async function renameTask(taskId: string, newPrompt: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt: newPrompt }),
  });

  if (!response.ok) {
    throw new Error(`Failed to rename task: ${response.statusText}`);
  }
}

export interface MessageItem {
  content: string;
  role?: string;
  tool_calls?: any[];
}

export async function getTaskMessages(taskId: string): Promise<Record<string, MessageItem[]>> {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}/messages`);

  if (!response.ok) {
    throw new Error(`Failed to get task messages: ${response.statusText}`);
  }

  return response.json();
}

export async function getSampleMessages(taskId: string, sampleId: string): Promise<MessageItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}/messages/${sampleId}`);

  if (!response.ok) {
    throw new Error(`Failed to get sample messages: ${response.statusText}`);
  }

  return response.json();
}
