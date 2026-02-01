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

  // Actions
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

}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  selectedTaskId: null,
  ws: null,
  sidebarView: "new",
  searchQuery: "",
  isSidebarCollapsed: false,

  addTask: (task) => {
    set((state) => ({
      tasks: [task, ...state.tasks],
      selectedTaskId: task.id,
      sidebarView: "all", // Switch to all tasks view after creating
    }));
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
  },

  connectWebSocket: () => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected');
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
      // 尝试重连
      setTimeout(() => {
        if (get().ws?.readyState === WebSocket.CLOSED) {
          get().connectWebSocket();
        }
      }, 3000);
    };

    set({ ws });
  },

  disconnectWebSocket: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null });
    }
  },

  handleWebSocketMessage: (message) => {
    const { type, taskId, sampleId, content, status, progress, error, artifact } = message;

    switch (type) {
      case 'status':
        if (status) {
          get().updateTask(taskId, { status });
        }
        break;

      case 'chunk':
        if (sampleId && content) {
          get().appendSampleContent(taskId, sampleId, content);
        }
        break;

      case 'progress':
        if (progress !== undefined) {
          if (sampleId) {
            get().updateSample(taskId, sampleId, { progress });
          } else {
            get().updateTask(taskId, { progress });
          }
        }
        break;

      case 'complete':
        get().updateTask(taskId, {
          status: 'completed',
          progress: 100,
          artifact,
        });
        break;

      case 'error':
        get().updateTask(taskId, {
          status: 'failed',
          error: error || 'Unknown error',
        });
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


}));
