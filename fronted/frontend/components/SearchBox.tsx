"use client";

import { useState, useRef, useCallback } from "react";
import { Sparkles, Loader2, Upload, X, FileText, FileSliders, Layers, Layout } from "lucide-react";
import { useTaskStore } from "@/store/taskStore";
import { createTask, uploadFiles } from "@/lib/api";
import { Task, UploadedFile } from "@/types/task";

export default function SearchBox() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sampleCount, setSampleCount] = useState(1);
  const [pages, setPages] = useState("auto");
  const [outputType, setOutputType] = useState("freeform");
  const [template, setTemplate] = useState("auto");
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const addTask = useTaskStore((state) => state.addTask);

  // 模板选项
  const templateOptions = ["auto", "beamer", "ucas", "hit", "default", "cip", "thu"];

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      const response = await uploadFiles(Array.from(files));
      if (response.files && response.files.length > 0) {
        setUploadedFile(response.files[0]);
      }
    } catch (error) {
      console.error("Failed to upload file:", error);
      alert(error instanceof Error ? error.message : "文件上传失败，请重试");
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim() || loading) return;

    setLoading(true);
    try {
      const response = await createTask({
        prompt: prompt.trim(),
        sampleCount,
        pages,
        outputType,
        uploadedFileId: uploadedFile?.fileId,
        options: {
          template: outputType === "templates" ? template : undefined,
        },
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
        pages,
        outputType,
        uploadedFileId: uploadedFile?.fileId,
      };

      addTask(task);
      setPrompt("");
      setUploadedFile(null);
    } catch (error) {
      console.error("Failed to create task:", error);
      alert("创建任务失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  // 生成页数选项 (auto + 1-30)
  const pageOptions = ["auto", ...Array.from({ length: 30 }, (_, i) => String(i + 1))];

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      {/* 输入框 */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center gap-2 bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-2 border border-gray-200 dark:border-gray-700">
          <Sparkles className="ml-3 text-purple-500" size={20} />
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
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm outline-none border-none text-gray-700 dark:text-gray-300"
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
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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

      {/* 配置选项区域 */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 页数设置 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <FileSliders size={18} className="text-blue-500" />
              <span className="font-medium text-sm">幻灯片页数 (#pages)</span>
            </div>
            <select
              value={pages}
              onChange={(e) => setPages(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 rounded-xl text-sm outline-none border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-all"
              disabled={loading}
            >
              {pageOptions.map((p) => (
                <option key={p} value={p}>
                  {p === "auto" ? "auto" : p}
                </option>
              ))}
            </select>
          </div>

          {/* 输出类型 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Layers size={18} className="text-purple-500" />
              <span className="font-medium text-sm">输出类型 (output type)</span>
            </div>
            <select
              value={outputType}
              onChange={(e) => setOutputType(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 rounded-xl text-sm outline-none border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-purple-500/30 focus:border-purple-500 transition-all"
              disabled={loading}
            >
              <option value="freeform">自由生成 (freeform)</option>
              <option value="templates">模版 (templates)</option>
            </select>
          </div>

          {/* 模板选择 - 仅在选择模版时显示 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Layout size={18} className="text-green-500" />
              <span className="font-medium text-sm">选择模板 (template)</span>
            </div>
            <select
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              className={`w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-700/50 rounded-xl text-sm outline-none border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-all ${
                outputType !== "templates" ? "opacity-50 cursor-not-allowed" : ""
              }`}
              disabled={loading || outputType !== "templates"}
            >
              {templateOptions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 文件上传区域 */}
        <div className="mt-5 pt-5 border-t border-gray-200 dark:border-gray-700">
          <div
            className={`border-2 border-dashed rounded-xl p-4 text-center transition-all cursor-pointer ${
              isDragging
                ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                : uploadedFile
                ? "border-green-400 bg-green-50 dark:bg-green-900/10"
                : "border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-gray-50 dark:hover:bg-gray-700/30"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !uploadedFile && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.pptx,.ppt"
              onChange={(e) => handleFileUpload(e.target.files)}
            />

            {uploadedFile ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="text-green-500" size={22} />
                <span className="text-gray-700 dark:text-gray-300 font-medium">{uploadedFile.filename}</span>
                <span className="text-gray-500 text-sm">({(uploadedFile.size / 1024).toFixed(1)} KB)</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setUploadedFile(null);
                  }}
                  className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-full transition-colors"
                >
                  <X size={16} className="text-red-500" />
                </button>
              </div>
            ) : uploading ? (
              <div className="flex items-center justify-center gap-2 py-1">
                <Loader2 className="animate-spin text-blue-500" size={22} />
                <span className="text-gray-600 dark:text-gray-400">上传中...</span>
              </div>
            ) : (
              <div className="flex items-center justify-center gap-3 py-1">
                <Upload className="text-gray-400" size={22} />
                <p className="text-gray-600 dark:text-gray-400">
                  拖放文件到此处，或 <span className="text-blue-500 font-medium">点击上传</span>
                </p>
                <span className="text-gray-400 text-sm">
                  (PDF, DOC, DOCX, TXT, PPT, PPTX)
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
