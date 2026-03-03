export type TaskStatus = 'idle' | 'running' | 'collecting' | 'completed' | 'failed';

export interface Artifact {
  type: 'html' | 'code' | 'markdown' | 'ppt';
  content: string;
  language?: string;
}

export interface ToolCall {
  name: string;
  arguments?: string;
}

export interface AgentMessage {
  content: string;
  role?: string;  // system, user, assistant, tool
  toolCalls?: ToolCall[];
}

export interface Sample {
  id: string;
  content: string;
  messages?: AgentMessage[];
  status: TaskStatus;
  progress: number;
  createdAt: number;
  filePath?: string;  // 生成的文件路径
  artifact?: Artifact;  // 样本的 artifact
}

export interface Task {
  id: string;
  prompt: string;
  status: TaskStatus;
  samples: Sample[];
  progress: number;
  createdAt: number;
  updatedAt: number;
  error?: string;
  artifact?: Artifact;
  pages?: string;
  outputType?: string;
  uploadedFileId?: string;
  aspectRatio?: string;  // 幻灯片尺寸比例
}

export interface WebSocketMessage {
  type: 'status' | 'chunk' | 'complete' | 'error' | 'progress';
  taskId: string;
  sampleId?: string;
  content?: string;
  status?: TaskStatus;
  progress?: number;
  error?: string;
  artifact?: Task['artifact'];
  filePath?: string;
  // 新增字段用于显示 Agent 交互过程
  role?: string;  // system, user, assistant, tool
  toolCalls?: ToolCall[];
}

export interface CreateTaskRequest {
  prompt: string;
  sampleCount?: number;
  pages?: string;
  outputType?: string;
  uploadedFileId?: string;
  aspectRatio?: string;  // 幻灯片尺寸比例
  options?: {
    template?: string;
    style?: string;
  };
}

export interface CreateTaskResponse {
  taskId: string;
  status: string;
}

export interface UploadedFile {
  fileId: string;
  filename: string;
  size: number;
}

export interface UploadResponse {
  status: string;
  files: UploadedFile[];
}
