"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { useTaskStore } from "@/store/taskStore";
import { createTask } from "@/lib/api";
import { Task } from "@/types/task";

export default function SearchBox() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sampleCount, setSampleCount] = useState(1);
  const addTask = useTaskStore((state) => state.addTask);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();



    // 否则创建新任务
    if (!prompt.trim() || loading) return;

    setLoading(true);
    try {
      const response = await createTask({
        prompt: prompt.trim(),
        sampleCount,
      });

      // 创建本地任务对象
      const task: Task = {
        id: response.taskId,
        prompt: prompt.trim(),
        status: "running",
        samples: Array.from({ length: sampleCount }, (_, i) => ({
          id: `${response.taskId}-sample-${i}`,
          content: "",
          status: "running" as const,
          progress: 0,
          createdAt: Date.now(),
        })),
        progress: 0,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      addTask(task);
      setPrompt("");
    } catch (error) {
      console.error("Failed to create task:", error);
      alert("创建任务失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-2 border border-gray-200 dark:border-gray-700">
          <Search className="ml-3 text-gray-400" size={20} />
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="描述你想要创建的演示文稿..."
            className="flex-1 px-2 py-3 bg-transparent outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
            disabled={loading}
          />
          <div className="flex items-center gap-2 mr-2">
            <select
              value={sampleCount}
              onChange={(e) => setSampleCount(Number(e.target.value))}
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm outline-none border-none"
              disabled={loading}
            >
              <option value={1}>1 个样本</option>
              <option value={2}>2 个样本</option>
              <option value={3}>3 个样本</option>
              <option value={4}>4 个样本</option>
            </select>
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  生成中...
                </>
              ) : (
                "生成"
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
