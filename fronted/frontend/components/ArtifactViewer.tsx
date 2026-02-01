"use client";

import { Task } from "@/types/task";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Code, Eye, Download, Maximize2 } from "lucide-react";
import remarkGfm from "remark-gfm";

interface ArtifactViewerProps {
  task: Task;
}

export default function ArtifactViewer({ task }: ArtifactViewerProps) {
  const [previewMode, setPreviewMode] = useState<"code" | "preview">("code");
  const [fullscreen, setFullscreen] = useState(false);

  const handleDownload = () => {
    if (!task.artifact) return;

    const blob = new Blob([task.artifact.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${task.id}.${task.artifact.type === "html" ? "html" : "txt"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!task.artifact && task.samples.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">等待生成结果...</p>
      </div>
    );
  }

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden ${
        fullscreen ? "fixed inset-4 z-50" : ""
      }`}
    >
      {/* 头部工具栏 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-800 dark:text-gray-100">
          {task.artifact ? "生成结果" : "实时预览"}
        </h3>
        <div className="flex items-center gap-2">
          {task.artifact?.type === "html" && (
            <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setPreviewMode("code")}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  previewMode === "code"
                    ? "bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100"
                    : "text-gray-600 dark:text-gray-400"
                }`}
              >
                <Code size={16} />
              </button>
              <button
                onClick={() => setPreviewMode("preview")}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  previewMode === "preview"
                    ? "bg-white dark:bg-gray-600 text-gray-800 dark:text-gray-100"
                    : "text-gray-600 dark:text-gray-400"
                }`}
              >
                <Eye size={16} />
              </button>
            </div>
          )}
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="下载"
          >
            <Download size={18} />
          </button>
          <button
            onClick={() => setFullscreen(!fullscreen)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="全屏"
          >
            <Maximize2 size={18} />
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="overflow-auto" style={{ maxHeight: fullscreen ? "calc(100vh - 8rem)" : "600px" }}>
        {task.artifact ? (
          <>
            {/* HTML 预览 */}
            {task.artifact.type === "html" && previewMode === "preview" && (
              <iframe
                srcDoc={task.artifact.content}
                className="w-full h-full min-h-[500px] border-0"
                sandbox="allow-scripts"
                title="Preview"
              />
            )}

            {/* 代码显示 */}
            {(task.artifact.type !== "html" || previewMode === "code") && (
              <div className="p-4">
                {task.artifact.type === "markdown" ? (
                  <div className="prose dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code(props) {
                          const { node, className, children, ...rest } = props;
                          const match = /language-(\w+)/.exec(className || "");
                          const inline = !match;
                          return !inline && match ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus}
                              language={match[1]}
                              PreTag="div"
                            >
                              {String(children).replace(/\n$/, "")}
                            </SyntaxHighlighter>
                          ) : (
                            <code className={className} {...rest}>
                              {children}
                            </code>
                          );
                        },
                      }}
                    >
                      {task.artifact.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <SyntaxHighlighter
                    language={task.artifact.language || "text"}
                    style={vscDarkPlus}
                    showLineNumbers
                  >
                    {task.artifact.content}
                  </SyntaxHighlighter>
                )}
              </div>
            )}
          </>
        ) : (
          // 显示样本内容
          <div className="p-4 space-y-4">
            {task.samples.map((sample, index) => (
              <div key={sample.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">样本 {index + 1}</h4>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {sample.progress}%
                  </span>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                  {sample.content || "生成中..."}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
