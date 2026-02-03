"use client";

import { create } from 'zustand';
import { Task, Sample, WebSocketMessage, TaskStatus } from '@/types/task';

export type SidebarView = "new" | "all" | "search";

interface TaskStore {
  tasks: Task[];
  selectedTaskId: string | null;
  ws: WebSocket | null;
  sidebarView: SidebarView;
  searchQuery: string;
  isSidebarCollapsed: boolean;
  subscribedTaskIds: Set<string>;

  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  updateSample: (taskId: string, sampleId: string, updates: Partial<Sample>) => void;
  appendSampleContent: (taskId: string, sampleId: string, content: string) => void;
  selectTask: (taskId: string | null) => void;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  setSidebarView: (view: SidebarView) => void;
  setSearchQuery: (query: string) => void;
  toggleSidebar: () => void;
  getFilteredTasks: () => Task[];
  deleteTask: (taskId: string) => void;
  renameTask: (taskId: string, newPrompt: string) => void;
  subscribeTask: (taskId: string) => void;
  subscribeRunningTasks: () => void;
}

// 动态获取 WebSocket URL
// 如果环境变量为空，则根据当前页面的 origin 自动生成（适用于 Nginx 反向代理场景）
function getWsUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_WS_URL;
  if (envUrl) {
    return envUrl;
  }
  // 在浏览器环境中，根据当前页面的 origin 生成 WebSocket URL
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }
  // 服务端渲染时的默认值
  return 'ws://localhost:8000/ws';
}

const WS_URL = getWsUrl();

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  selectedTaskId: null,
  ws: null,
  sidebarView: "new",
  searchQuery: "",
  isSidebarCollapsed: false,
  subscribedTaskIds: new Set<string>(),

  setTasks: (tasks) => {
    set({ tasks });
    // 自动订阅运行中的任务
    setTimeout(() => get().subscribeRunningTasks(), 100);
  },

  addTask: (task) => {
    set((state) => ({
      tasks: [task, ...state.tasks],
      selectedTaskId: task.id,
      sidebarView: "all", // Switch to all tasks view after creating
    }));
    // 订阅任务更新
    const { ws } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'subscribe', task_id: task.id }));
    }
  },

  updateTask: (taskId, updates) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId
          ? { ...task, ...updates, updatedAt: Date.now() }
          : task
      ),
    }));
  },

  updateSample: (taskId, sampleId, updates) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId
          ? {
              ...task,
              samples: task.samples.map((sample) =>
                sample.id === sampleId ? { ...sample, ...updates } : sample
              ),
              updatedAt: Date.now(),
            }
          : task
      ),
    }));
  },

  appendSampleContent: (taskId, sampleId, content) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId
          ? {
              ...task,
              samples: task.samples.map((sample) =>
                sample.id === sampleId
                  ? { ...sample, content: sample.content + content }
                  : sample
              ),
              updatedAt: Date.now(),
            }
          : task
      ),
    }));
  },

  selectTask: (taskId) => {
    set({ selectedTaskId: taskId });
    // 选择任务时自动订阅
    if (taskId) {
      get().subscribeTask(taskId);
    }
  },

  connectWebSocket: () => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
      // 连接成功后订阅运行中的任务
      set({ ws });
      setTimeout(() => get().subscribeRunningTasks(), 100);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        get().handleWebSocketMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // 清空订阅列表，重连后重新订阅
      set({ subscribedTaskIds: new Set<string>() });
      // 尝试重连
      setTimeout(() => {
        if (get().ws?.readyState === WebSocket.CLOSED) {
          get().connectWebSocket();
        }
      }, 3000);
    };
  },

  disconnectWebSocket: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null });
    }
  },

  handleWebSocketMessage: (message) => {
    // 后端使用 snake_case，前端使用 camelCase，需要转换
    const type = message.type;
    const taskId = message.taskId || (message as any).task_id;
    const sampleId = message.sampleId || (message as any).sample_id;
    const { content, status, progress, error, artifact } = message;

    console.log(`[WebSocket] Received message: type=${type}, taskId=${taskId?.slice(0, 8)}, sampleId=${sampleId?.slice(0, 16) || 'none'}, content length=${content?.length || 0}`);

    if (!taskId) return;

    switch (type) {
      case 'status':
        if (status) {
          get().updateTask(taskId, { status });
        }
        break;

      case 'chunk':
        if (content) {
          const task = get().tasks.find(t => t.id === taskId);
          console.log(`[WebSocket] Processing chunk for task ${taskId.slice(0, 8)}, task found: ${!!task}, samples: ${task?.samples?.length || 0}`);

          if (task) {
            if (task.samples.length > 0) {
              // 如果指定了 sampleId，追加到对应样本；否则追加到第一个样本
              const targetSampleId = sampleId || task.samples[0].id;
              get().appendSampleContent(taskId, targetSampleId, content + "\n\n");
            } else {
              // 如果没有样本，创建一个临时样本来存储内容
              console.log(`[WebSocket] No samples found, creating temporary sample`);
              set((state) => ({
                tasks: state.tasks.map((t) =>
                  t.id === taskId
                    ? {
                        ...t,
                        samples: [{
                          id: `${taskId}-sample-0`,
                          content: content + "\n\n",
                          status: 'running' as const,
                          progress: 0,
                          createdAt: Date.now(),
                        }],
                        updatedAt: Date.now(),
                      }
                    : t
                ),
              }));
            }
          }
        }
        break;

      case 'progress':
        if (progress !== undefined) {
          if (sampleId) {
            // 更新特定样本的进度
            get().updateSample(taskId, sampleId, { progress, status: 'running' });
          } else {
            // 更新任务整体进度
            get().updateTask(taskId, { progress });
          }
        }
        break;

      case 'complete':
        // 更新任务完成状态
        const updates: Partial<Task> = {
          status: 'completed',
          progress: 100,
        };
        if (artifact) {
          updates.artifact = artifact;
        }
        get().updateTask(taskId, updates);

        // 如果有 sampleId，也更新对应样本的状态
        if (sampleId) {
          get().updateSample(taskId, sampleId, {
            status: 'completed',
            progress: 100,
            artifact,
          });
        }
        break;

      case 'error':
        get().updateTask(taskId, {
          status: 'failed',
          error: error || 'Unknown error',
        });
        // 如果有 sampleId，也更新对应样本的状态
        if (sampleId) {
          get().updateSample(taskId, sampleId, {
            status: 'failed',
          });
        }
        break;
    }
  },

  setSidebarView: (view) => {
    set({ sidebarView: view });
  },

  setSearchQuery: (query) => {
    set({ searchQuery: query });
  },

  toggleSidebar: () => {
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed }));
  },

  getFilteredTasks: () => {
    const { tasks, searchQuery } = get();
    if (!searchQuery.trim()) {
      return tasks;
    }

    const query = searchQuery.toLowerCase();
    return tasks.filter((task) =>
      task.prompt.toLowerCase().includes(query) ||
      task.id.toLowerCase().includes(query) ||
      task.status.toLowerCase().includes(query)
    );
  },

  deleteTask: (taskId) => {
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== taskId),
      selectedTaskId: state.selectedTaskId === taskId ? null : state.selectedTaskId,
    }));
  },

  renameTask: (taskId, newPrompt) => {
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId
          ? { ...task, prompt: newPrompt, updatedAt: Date.now() }
          : task
      ),
    }));
  },

  subscribeTask: (taskId) => {
    const { ws, subscribedTaskIds } = get();
    if (ws && ws.readyState === WebSocket.OPEN && !subscribedTaskIds.has(taskId)) {
      ws.send(JSON.stringify({ type: 'subscribe', task_id: taskId }));
      subscribedTaskIds.add(taskId);
      set({ subscribedTaskIds: new Set(subscribedTaskIds) });
    }
  },

  subscribeRunningTasks: () => {
    const { tasks, ws, subscribedTaskIds } = get();
    if (ws && ws.readyState === WebSocket.OPEN) {
      const runningTasks = tasks.filter(t => t.status === 'running' || t.status === 'idle');
      runningTasks.forEach(task => {
        if (!subscribedTaskIds.has(task.id)) {
          ws.send(JSON.stringify({ type: 'subscribe', task_id: task.id }));
          subscribedTaskIds.add(task.id);
        }
      });
      set({ subscribedTaskIds: new Set(subscribedTaskIds) });
    }
  },

}));
