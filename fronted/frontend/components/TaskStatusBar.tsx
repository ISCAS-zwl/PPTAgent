"use client";

import { useTaskStore } from "@/store/taskStore";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export default function TaskStatusBar() {
  const tasks = useTaskStore((state) => state.tasks);
  const runningTasks = tasks.filter((t) => t.status === "running");

  if (runningTasks.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg z-40">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            后台运行中的任务 ({runningTasks.length})
          </h3>
        </div>
        <div className="space-y-2 max-h-32 overflow-y-auto">
          <AnimatePresence>
            {runningTasks.map((task) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <Loader2 className="animate-spin text-blue-600" size={16} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 dark:text-gray-200 truncate">
                    {task.prompt}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-blue-600 to-purple-600 h-1.5 rounded-full transition-all"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {task.progress}%
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
