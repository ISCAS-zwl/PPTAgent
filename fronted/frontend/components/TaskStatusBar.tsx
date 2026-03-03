"use client";

import { useState } from "react";
import { useTaskStore } from "@/store/taskStore";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ChevronUp, ChevronDown } from "lucide-react";

export default function TaskStatusBar() {
  const tasks = useTaskStore((state) => state.tasks);
  const runningTasks = tasks.filter((t) => t.status === "running");
  const [isExpanded, setIsExpanded] = useState(true);

  if (runningTasks.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40">
      <AnimatePresence>
        {isExpanded ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg"
          >
            <div className="max-w-7xl mx-auto px-4 py-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  后台运行中的任务 ({runningTasks.length})
                </h3>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                  title="折叠"
                >
                  <ChevronDown size={18} className="text-gray-500 dark:text-gray-400" />
                </button>
              </div>
              {/* 展开时显示最多3个任务，可滚动 */}
              <div className="space-y-2 max-h-40 overflow-y-auto">
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
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        ) : (
          /* 折叠状态：显示一个更美观的小条 */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-gray-700 dark:bg-gray-600 shadow-lg"
          >
            <button
              onClick={() => setIsExpanded(true)}
              className="w-full flex items-center justify-center gap-3 px-4 py-2 hover:bg-gray-800 dark:hover:bg-gray-700 transition-all"
              title="展开任务进度"
            >
              <Loader2 className="animate-spin text-white" size={16} />
              <span className="text-sm font-medium text-white">
                {runningTasks.length} 个任务运行中
              </span>
              <ChevronUp size={16} className="text-white" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
