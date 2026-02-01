"use client";

import { useTaskStore } from "@/store/taskStore";
import { motion } from "framer-motion";
import { Loader2, CheckCircle, XCircle, Clock, FileText } from "lucide-react";
import { Task } from "@/types/task";

const statusIcons = {
  idle: Clock,
  running: Loader2,
  collecting: Loader2,
  completed: CheckCircle,
  failed: XCircle,
};

const statusColors = {
  idle: "text-gray-400",
  running: "text-blue-600",
  collecting: "text-purple-600",
  completed: "text-green-600",
  failed: "text-red-600",
};

const statusBgColors = {
  idle: "bg-gray-100 dark:bg-gray-700",
  running: "bg-blue-50 dark:bg-blue-900/20",
  collecting: "bg-purple-50 dark:bg-purple-900/20",
  completed: "bg-green-50 dark:bg-green-900/20",
  failed: "bg-red-50 dark:bg-red-900/20",
};

export default function TaskGrid() {
  const { tasks, selectedTaskId, selectTask } = useTaskStore();

  return (
    <div className="space-y-4">
      {tasks.map((task) => (
        <motion.div
          key={task.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border-2 transition-all cursor-pointer ${
            selectedTaskId === task.id
              ? "border-blue-500"
              : "border-transparent hover:border-gray-300 dark:hover:border-gray-600"
          }`}
          onClick={() => selectTask(task.id)}
        >
          <div className="p-4">
            {/* 任务头部 */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-1">
                  {task.prompt}
                </h3>
                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <FileText size={14} />
                  <span>{task.samples.length} 个样本</span>
                  <span>•</span>
                  <span>{new Date(task.createdAt).toLocaleString()}</span>
                </div>
              </div>
              <div
                className={`flex items-center gap-2 px-3 py-1 rounded-full ${
                  statusBgColors[task.status]
                }`}
              >
                {(() => {
                  const Icon = statusIcons[task.status];
                  return (
                    <Icon
                      size={16}
                      className={`${statusColors[task.status]} ${
                        task.status === "running" || task.status === "collecting"
                          ? "animate-spin"
                          : ""
                      }`}
                    />
                  );
                })()}
                <span className={`text-sm font-medium ${statusColors[task.status]}`}>
                  {task.status === "idle" && "等待中"}
                  {task.status === "running" && "运行中"}
                  {task.status === "collecting" && "收集中"}
                  {task.status === "completed" && "已完成"}
                  {task.status === "failed" && "失败"}
                </span>
              </div>
            </div>

            {/* 进度条 */}
            {(task.status === "running" || task.status === "collecting") && (
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                  <span>整体进度</span>
                  <span>{task.progress}%</span>
                </div>
                <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* 样本网格 */}
            {task.samples.length > 1 && (
              <div className="grid grid-cols-2 gap-2">
                {task.samples.map((sample, index) => (
                  <div
                    key={sample.id}
                    className={`p-3 rounded-lg border ${statusBgColors[sample.status]}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                        样本 {index + 1}
                      </span>
                      {(() => {
                        const Icon = statusIcons[sample.status];
                        return (
                          <Icon
                            size={14}
                            className={`${statusColors[sample.status]} ${
                              sample.status === "running" ? "animate-spin" : ""
                            }`}
                          />
                        );
                      })()}
                    </div>
                    {sample.status === "running" && (
                      <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-1">
                        <div
                          className="bg-blue-600 h-1 rounded-full transition-all"
                          style={{ width: `${sample.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 错误信息 */}
            {task.status === "failed" && task.error && (
              <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">{task.error}</p>
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
