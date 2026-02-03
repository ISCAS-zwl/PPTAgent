"use client";

import { useEffect, useState, useRef } from "react";
import { useTaskStore } from "@/store/taskStore";
import { PlusCircle, Search, ChevronLeft, ChevronRight, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { listTasks, deleteTask as deleteTaskApi, renameTask as renameTaskApi } from "@/lib/api";
import { Task } from "@/types/task";

export default function Sidebar() {
  const {
    tasks,
    selectedTaskId,
    isSidebarCollapsed,
    searchQuery,
    setSearchQuery,
    setSidebarView,
    selectTask,
    toggleSidebar,
    setTasks,
    deleteTask,
    renameTask,
  } = useTaskStore();

  // 下拉菜单状态
  const [menuOpenTaskId, setMenuOpenTaskId] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const menuRef = useRef<HTMLDivElement>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  // 加载任务列表
  useEffect(() => {
    const loadTasks = async () => {
      try {
        const taskList = await listTasks();
        setTasks(taskList);
      } catch (error) {
        console.error("Failed to load tasks:", error);
      }
    };
    loadTasks();
  }, [setTasks]);

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpenTaskId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // 重命名输入框聚焦
  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [isRenaming]);

  // 根据任务名称过滤任务
  const filteredTasks = searchQuery.trim()
    ? tasks.filter((task) =>
        (task.prompt || "").toLowerCase().includes(searchQuery.toLowerCase())
      )
    : tasks;

  // 点击新建任务
  const handleNewTask = () => {
    selectTask(null);
    setSidebarView("new");
  };

  // 点击任务项
  const handleTaskClick = (task: Task) => {
    selectTask(task.id);
    setSidebarView("all");
  };

  // 打开菜单
  const handleMenuClick = (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    setMenuOpenTaskId(menuOpenTaskId === taskId ? null : taskId);
  };

  // 删除任务
  const handleDelete = async (e: React.MouseEvent, taskId: string) => {
    e.stopPropagation();
    setMenuOpenTaskId(null);
    try {
      await deleteTaskApi(taskId);
      deleteTask(taskId);
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  // 开始重命名
  const handleStartRename = (e: React.MouseEvent, task: Task) => {
    e.stopPropagation();
    setMenuOpenTaskId(null);
    setIsRenaming(task.id);
    setRenameValue(task.prompt || "");
  };

  // 确认重命名
  const handleConfirmRename = async (taskId: string) => {
    if (renameValue.trim()) {
      try {
        await renameTaskApi(taskId, renameValue.trim());
        renameTask(taskId, renameValue.trim());
      } catch (error) {
        console.error("Failed to rename task:", error);
      }
    }
    setIsRenaming(null);
    setRenameValue("");
  };

  // 取消重命名
  const handleCancelRename = () => {
    setIsRenaming(null);
    setRenameValue("");
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500";
      case "completed":
        return "bg-blue-500";
      case "failed":
        return "bg-red-500";
      default:
        return "bg-gray-400";
    }
  };

  // 格式化时间
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "刚刚";
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString();
  };

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-white dark:bg-gray-900
        border-r border-gray-200 dark:border-gray-800
        transition-all duration-300 ease-in-out z-40
        flex flex-col
        ${isSidebarCollapsed ? "w-16" : "w-72"}
      `}
    >
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
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

      {/* New Task Button */}
      <div className="p-3 flex-shrink-0">
        <button
          onClick={handleNewTask}
          className={`
            w-full flex items-center gap-3 px-4 py-3 rounded-xl
            bg-gradient-to-r from-blue-600 to-purple-600 text-white
            hover:from-blue-700 hover:to-purple-700
            transition-all duration-200 shadow-md hover:shadow-lg
            ${isSidebarCollapsed ? "justify-center px-2" : ""}
          `}
        >
          <PlusCircle className="w-5 h-5 flex-shrink-0" />
          {!isSidebarCollapsed && (
            <span className="font-medium">新建任务</span>
          )}
        </button>
      </div>

      {/* Search Box */}
      {!isSidebarCollapsed && (
        <div className="px-3 pb-3 flex-shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索任务名称..."
              className="w-full pl-10 pr-4 py-2.5 bg-gray-100 dark:bg-gray-800 rounded-lg
                text-sm text-gray-800 dark:text-gray-200
                placeholder-gray-400 dark:placeholder-gray-500
                outline-none focus:ring-2 focus:ring-blue-500/50
                transition-all duration-200"
            />
          </div>
        </div>
      )}

      {/* All Tasks Section */}
      {!isSidebarCollapsed && (
        <div className="flex-1 flex flex-col min-h-0">
          <div className="px-4 py-2 flex-shrink-0">
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              所有任务 ({filteredTasks.length})
            </h2>
          </div>

          {/* Task List */}
          <div className="flex-1 overflow-y-auto px-2 pb-4">
            {filteredTasks.length === 0 ? (
              <div className="px-3 py-8 text-center">
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  {searchQuery ? "未找到匹配的任务" : "暂无任务"}
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className={`
                      relative group w-full text-left px-3 py-3 rounded-lg
                      transition-all duration-200 cursor-pointer
                      ${
                        selectedTaskId === task.id
                          ? "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800"
                          : "hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent"
                      }
                    `}
                    onClick={() => handleTaskClick(task)}
                  >
                    <div className="flex items-start gap-2">
                      {/* Status Indicator */}
                      <div
                        className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${getStatusColor(
                          task.status
                        )}`}
                      />
                      <div className="flex-1 min-w-0">
                        {/* Task ID */}
                        <p className="text-xs font-mono text-gray-500 dark:text-gray-400 truncate">
                          {task.id.slice(0, 8)}...
                        </p>
                        {/* Task Title/Prompt - 可编辑 */}
                        {isRenaming === task.id ? (
                          <input
                            ref={renameInputRef}
                            type="text"
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onBlur={() => handleConfirmRename(task.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleConfirmRename(task.id);
                              } else if (e.key === "Escape") {
                                handleCancelRename();
                              }
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-full text-sm font-medium mt-0.5 px-1 py-0.5
                              bg-white dark:bg-gray-700 border border-blue-500 rounded
                              text-gray-800 dark:text-gray-200 outline-none"
                          />
                        ) : (
                          <p
                            className={`text-sm font-medium truncate mt-0.5 ${
                              selectedTaskId === task.id
                                ? "text-blue-700 dark:text-blue-300"
                                : "text-gray-800 dark:text-gray-200"
                            }`}
                          >
                            {task.prompt || "未命名任务"}
                          </p>
                        )}
                        {/* Time */}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {formatTime(task.createdAt)}
                        </p>
                        {/* Progress Bar for Running Tasks */}
                        {task.status === "running" && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                              <span>进度</span>
                              <span>{task.progress || 0}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300"
                                style={{ width: `${task.progress || 0}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 三点菜单按钮 */}
                      <button
                        onClick={(e) => handleMenuClick(e, task.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200
                          dark:hover:bg-gray-700 transition-opacity flex-shrink-0"
                      >
                        <MoreHorizontal className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                      </button>
                    </div>

                    {/* 下拉菜单 */}
                    {menuOpenTaskId === task.id && (
                      <div
                        ref={menuRef}
                        className="absolute right-2 top-10 z-50 w-36 bg-white dark:bg-gray-800
                          rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1"
                      >
                        <button
                          onClick={(e) => handleStartRename(e, task)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700
                            dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <Pencil className="w-4 h-4" />
                          重命名
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, task.id)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600
                            dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                          <Trash2 className="w-4 h-4" />
                          删除
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Collapsed State - Task Count */}
      {isSidebarCollapsed && (
        <div className="flex-1 flex flex-col items-center pt-4">
          <button
            onClick={() => {
              toggleSidebar();
            }}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="搜索任务"
          >
            <Search className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div className="mt-4 text-center">
            <span className="text-lg font-bold text-gray-700 dark:text-gray-300">
              {tasks.length}
            </span>
            <p className="text-xs text-gray-400">任务</p>
          </div>
        </div>
      )}

      {/* Status Info */}
      {!isSidebarCollapsed && (
        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-gray-600 dark:text-gray-400">
                {tasks.filter((t) => t.status === "running").length} 运行中
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-gray-600 dark:text-gray-400">
                {tasks.filter((t) => t.status === "completed").length} 完成
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-gray-600 dark:text-gray-400">
                {tasks.filter((t) => t.status === "failed").length} 失败
              </span>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
