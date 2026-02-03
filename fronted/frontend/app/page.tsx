"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/store/taskStore";
import Sidebar from "@/components/Sidebar";
import SearchBox from "@/components/SearchBox";
import TaskStatusBar from "@/components/TaskStatusBar";
import ArtifactViewer from "@/components/ArtifactViewer";

export default function Home() {
  const { tasks, connectWebSocket, selectedTaskId, sidebarView, isSidebarCollapsed } = useTaskStore();

  useEffect(() => {
    // 连接 WebSocket
    connectWebSocket();
  }, [connectWebSocket]);

  const selectedTask = tasks.find((t) => t.id === selectedTaskId);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* 左侧边栏 */}
      <Sidebar />

      {/* 主内容区域 - 根据侧边栏状态动态调整左边距 */}
      <main className={`transition-all duration-300 ease-in-out min-h-screen ${isSidebarCollapsed ? 'ml-16' : 'ml-72'}`}>
        {/* 新建任务视图 */}
        {sidebarView === "new" && (
          <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8">
              <div className="text-center mb-8">
                <h2 className="text-4xl font-bold mb-4 text-gray-800 dark:text-gray-100">
                  开始创建你的演示文稿
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-lg">
                  输入你的需求，AI 将为你生成专业的 PPT
                </p>
              </div>
              <SearchBox />
          </div>
        )}

        {/* 任务详情视图 - 当选中任务时显示 */}
        {sidebarView === "all" && (
          <div className="p-6 min-h-screen">
            {selectedTask ? (
              <div className="max-w-5xl mx-auto">
                {/* 任务信息头部 */}
                <div className="mb-6 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          selectedTask.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                          selectedTask.status === 'running' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                          selectedTask.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                          'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {selectedTask.status === 'completed' ? '已完成' :
                           selectedTask.status === 'running' ? '运行中' :
                           selectedTask.status === 'failed' ? '失败' : '空闲'}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                          ID: {selectedTask.id}
                        </span>
                      </div>
                      <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                        {selectedTask.prompt || "未命名任务"}
                      </h1>
                      <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        <span>创建时间: {new Date(selectedTask.createdAt).toLocaleString()}</span>
                        {selectedTask.pages && <span>页数: {selectedTask.pages}</span>}
                        {selectedTask.samples && <span>样本数: {selectedTask.samples.length}</span>}
                      </div>
                    </div>
                  </div>

                  {/* 进度条 */}
                  {selectedTask.status === 'running' && (
                    <div className="mt-4">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-400">生成进度</span>
                        <span className="text-blue-600 dark:text-blue-400">{selectedTask.progress || 0}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${selectedTask.progress || 0}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* 错误信息 */}
                  {selectedTask.error && (
                    <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <p className="text-sm text-red-600 dark:text-red-400">{selectedTask.error}</p>
                    </div>
                  )}
                </div>

                {/* 结果预览 */}
                <ArtifactViewer task={selectedTask} />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center min-h-[60vh]">
                <div className="text-center">
                  <div className="text-6xl mb-4">📋</div>
                  <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    选择一个任务查看详情
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400">
                    从左侧任务列表中选择一个任务，或创建新任务
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* 底部任务状态栏 */}
      <TaskStatusBar />
    </div>
  );
}
