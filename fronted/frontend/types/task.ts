export type TaskStatus = 'idle' | 'running' | 'collecting' | 'completed' | 'failed';

export interface Sample {
  id: string;
  content: string;
  status: TaskStatus;
  progress: number;
  createdAt: number;
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
  artifact?: {
    type: 'html' | 'code' | 'markdown' | 'ppt';
    content: string;
    language?: string;
  };
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
}

export interface CreateTaskRequest {
  prompt: string;
  sampleCount?: number;
  options?: {
    template?: string;
    style?: string;
  };
}

export interface CreateTaskResponse {
  taskId: string;
  status: string;
}
