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
          </motion.div>
        ) : (
          /* 折叠状态：只显示一个小按钮 */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex justify-center"
          >
            <button
              onClick={() => setIsExpanded(true)}
              className="flex items-center gap-2 px-4 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 border-b-0 rounded-t-lg shadow-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              title="展开任务进度"
            >
              <Loader2 className="animate-spin text-blue-600" size={14} />
              <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                {runningTasks.length} 个任务运行中
              </span>
              <ChevronUp size={14} className="text-gray-500 dark:text-gray-400" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
