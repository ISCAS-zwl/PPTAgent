import { CreateTaskRequest, CreateTaskResponse } from "@/types/task";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createTask(request: CreateTaskRequest): Promise<CreateTaskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/task/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to create task: ${response.statusText}`);
  }

  return response.json();
}

export async function getTask(taskId: string) {
  const response = await fetch(`${API_BASE_URL}/api/task/${taskId}`);

  if (!response.ok) {
    throw new Error(`Failed to get task: ${response.statusText}`);
  }

  return response.json();
}

export async function listTasks() {
  const response = await fetch(`${API_BASE_URL}/api/tasks`);

  if (!response.ok) {
    throw new Error(`Failed to list tasks: ${response.statusText}`);
  }

  return response.json();
}
