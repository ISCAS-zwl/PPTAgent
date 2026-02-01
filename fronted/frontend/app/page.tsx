"use client";

import { useEffect } from "react";
import { useTaskStore } from "@/store/taskStore";
import Sidebar from "@/components/Sidebar";
import SearchBox from "@/components/SearchBox";
import TaskStatusBar from "@/components/TaskStatusBar";
import TaskGrid from "@/components/TaskGrid";
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
      <main className={`transition-all duration-300 ease-in-out min-h-screen ${isSidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
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

              {/* 个性化卡片 */}
              <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl">
                <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-3xl mb-3">📊</div>
                  <h3 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">商业报告</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    生成专业的商业分析和数据报告
                  </p>
                </div>
                <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-3xl mb-3">🎓</div>
                  <h3 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">教育培训</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    创建引人入胜的教学课件
                  </p>
                </div>
                <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <div className="text-3xl mb-3">🚀</div>
                  <h3 className="font-semibold mb-2 text-gray-800 dark:text-gray-100">产品发布</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    设计吸引人的产品展示
                  </p>
                </div>
            </div>
          </div>
        )}

        {/* 所有任务视图 */}
        {sidebarView === "all" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 px-4 py-8">
            <div className="space-y-4">


              {tasks.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
                  <p className="text-gray-500 dark:text-gray-400">暂无任务</p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                    点击"新建任务"开始创建
                  </p>
                </div>
              ) : (
                <TaskGrid />
              )}
            </div>
            <div className="lg:sticky lg:top-8 h-fit">
              {selectedTask ? (
                <ArtifactViewer task={selectedTask} />
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
                  选择一个任务查看详情
                </div>
              )}
            </div>
          </div>
        )}

        {/* 搜索视图 */}
        {sidebarView === "search" && (
          <div className="px-4 py-8">
            <div className="max-w-4xl mx-auto">
              <div className="mb-6">
                <SearchBox />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  {tasks.length === 0 ? (
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
                      <p className="text-gray-500 dark:text-gray-400">暂无任务</p>
                    </div>
                  ) : (
                    <TaskGrid />
                  )}
                </div>
                <div className="lg:sticky lg:top-8 h-fit">
                  {selectedTask ? (
                    <ArtifactViewer task={selectedTask} />
                  ) : (
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
                      选择一个任务查看详情
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 底部任务状态栏 */}
      <TaskStatusBar />
    </div>
  );
}
