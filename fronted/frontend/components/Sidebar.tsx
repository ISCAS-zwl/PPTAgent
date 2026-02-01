"use client";

import { useTaskStore } from "@/store/taskStore";
import { PlusCircle, List, Search, ChevronLeft, ChevronRight } from "lucide-react";
import type { SidebarView } from "@/store/taskStore";

export default function Sidebar() {
  const {
    tasks,
    sidebarView,
    isSidebarCollapsed,
    setSidebarView,
    toggleSidebar
  } = useTaskStore();

  const menuItems = [
    {
      id: "new" as SidebarView,
      icon: PlusCircle,
      label: "新建任务",
      count: null,
    },
    {
      id: "all" as SidebarView,
      icon: List,
      label: "所有任务",
      count: tasks.length,
    },
    {
      id: "search" as SidebarView,
      icon: Search,
      label: "搜索",
      count: null,
    },
  ];

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-white dark:bg-gray-900
        border-r border-gray-200 dark:border-gray-800
        transition-all duration-300 ease-in-out z-40
        ${isSidebarCollapsed ? "w-16" : "w-64"}
      `}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-800">
        {!isSidebarCollapsed && (
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            PPTAgent
          </h1>
        )}
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label={isSidebarCollapsed ? "展开侧边栏" : "收起侧边栏"}
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          ) : (
            <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          )}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="p-2 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = sidebarView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setSidebarView(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-all duration-200
                ${
                  isActive
                    ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                }
                ${isSidebarCollapsed ? "justify-center" : ""}
              `}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-blue-600 dark:text-blue-400" : ""}`} />
              {!isSidebarCollapsed && (
                <>
                  <span className="flex-1 text-left font-medium">{item.label}</span>
                  {item.count !== null && (
                    <span
                      className={`
                        px-2 py-0.5 text-xs rounded-full font-medium
                        ${
                          isActive
                            ? "bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300"
                            : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                        }
                      `}
                    >
                      {item.count}
                    </span>
                  )}
                </>
              )}
            </button>
          );
        })}
      </nav>

      {/* Status Info */}
      {!isSidebarCollapsed && (
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-800">
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>运行中</span>
              <span className="font-medium text-green-600 dark:text-green-400">
                {tasks.filter((t) => t.status === "running").length}
              </span>
            </div>
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>已完成</span>
              <span className="font-medium text-blue-600 dark:text-blue-400">
                {tasks.filter((t) => t.status === "completed").length}
              </span>
            </div>
            <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
              <span>失败</span>
              <span className="font-medium text-red-600 dark:text-red-400">
                {tasks.filter((t) => t.status === "failed").length}
              </span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
