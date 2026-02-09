"use client";

import { Task, Sample, Artifact } from "@/types/task";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Code, Eye, Download, Maximize2, ChevronLeft, ChevronRight, Archive } from "lucide-react";
import remarkGfm from "remark-gfm";
import { getDownloadUrl, getWorkspaceZipUrl, getSlidePreviewUrl } from "@/lib/api";

interface ArtifactViewerProps {
  task: Task;
}

export default function ArtifactViewer({ task }: ArtifactViewerProps) {
  const [previewMode, setPreviewMode] = useState<"code" | "preview">("code");
  const [fullscreen, setFullscreen] = useState(false);
  const [selectedSampleIndex, setSelectedSampleIndex] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);

  const extractSlideLinks = (artifact?: Artifact) => {
    if (!artifact || !artifact.content) return [] as string[];
    const links = new Set<string>();

    // JSON 结构尝试提取
    try {
      const parsed = JSON.parse(artifact.content);
      if (Array.isArray(parsed)) {
        parsed.forEach((item) => {
          if (typeof item === "string") {
            links.add(item);
          } else if (item?.html_file) {
            links.add(item.html_file);
          }
        });
      }
      if (parsed?.slides && Array.isArray(parsed.slides)) {
        parsed.slides.forEach((s: any) => {
          if (typeof s === "string") links.add(s);
          if (s?.html_file) links.add(s.html_file);
        });
      }
      if (parsed?.html_file) links.add(parsed.html_file);
      if (parsed?.html_files && Array.isArray(parsed.html_files)) {
        parsed.html_files.forEach((f: any) => typeof f === "string" && links.add(f));
      }
    } catch (err) {
      // ignore JSON parse errors; fallback to regex
    }

    // 正则匹配 slides/*.html
    const regex = /slides\/[A-Za-z0-9_-]+\.html/gi;
    let match;
    while ((match = regex.exec(artifact.content)) !== null) {
      links.add(match[0]);
    }

    return Array.from(links);
  };

  const extractFirstHtmlPath = (text: string) => {
    const match = text.match(/html_file\"?\s*:\s*\"?([^"\s]+\.html)\"?|\b(slides?\/[A-Za-z0-9._-]+\.html)/i);
    return match ? (match[1] || match[2]) : null;
  };

  const markdownComponents = {
    code(props: any) {
      const { className, children, ...rest } = props;
      const match = /language-(\w+)/.exec(className || "");
      const inline = !match;
      if (!inline && match) {
        const raw = String(children).replace(/\n$/, "");
        const htmlPath = extractFirstHtmlPath(raw);
        const syntaxNode = (
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={match[1]}
            PreTag="div"
            customStyle={{ fontSize: "12px" }}
          >
            {raw}
          </SyntaxHighlighter>
        );

        if (htmlPath) {
          const previewUrl = getSlidePreviewUrl(task.id, htmlPath, hasMultipleSamples ? selectedSampleIndex : undefined);
          return (
            <div className="space-y-2">
              {syntaxNode}
              <div className="rounded-lg border border-gray-700 overflow-hidden bg-black">
                <iframe
                  src={previewUrl}
                  className="w-full h-80 border-0 bg-white"
                  sandbox="allow-scripts"
                  title={`slide-preview-${htmlPath}`}
                />
                <div className="px-3 py-2 text-xs text-gray-200 break-all">{htmlPath}</div>
              </div>
            </div>
          );
        }

        return syntaxNode;
      }

      return (
        <code
          className={`${className} px-1.5 py-0.5 rounded border border-gray-700 bg-black text-amber-200`}
          {...rest}
        >
          {children}
        </code>
      );
    },
    strong(props: any) {
      const { children } = props;
      const text = String(children);
      if (text.includes("Assistant") || text.includes("🤖")) {
        return <strong className="text-blue-600 dark:text-blue-400">{children}</strong>;
      }
      if (text.includes("Tool") || text.includes("🔧") || text.includes("📝")) {
        return <strong className="text-green-600 dark:text-green-400">{children}</strong>;
      }
      if (text.includes("System") || text.includes("⚙️")) {
        return <strong className="text-purple-600 dark:text-purple-400">{children}</strong>;
      }
      return <strong>{children}</strong>;
    },
    p(props: any) {
      const { className, children, ...rest } = props;
      const text = Array.isArray(children) ? children.map((c: any) => (typeof c === "string" ? c : "")).join("") : String(children || "");
      const htmlPath = extractFirstHtmlPath(text);

      if (htmlPath) {
        const previewUrl = getSlidePreviewUrl(task.id, htmlPath, hasMultipleSamples ? selectedSampleIndex : undefined);
        return (
          <div className="mb-3 space-y-2">
            <div
              className={`bg-neutral-900 text-white border border-black rounded-lg px-3 py-2 shadow-sm ${
                className || ""
              }`}
              {...rest}
            >
              {children}
            </div>
            <div className="rounded-lg border border-gray-700 overflow-hidden bg-black">
              <iframe
                src={previewUrl}
                className="w-full h-80 border-0 bg-white"
                sandbox="allow-scripts"
                title={`slide-preview-${htmlPath}`}
              />
              <div className="px-3 py-2 text-xs text-gray-200 break-all">{htmlPath}</div>
            </div>
          </div>
        );
      }

      return (
        <p
          className={`bg-neutral-900 text-white border border-black rounded-lg px-3 py-2 mb-3 shadow-sm ${
            className || ""
          }`}
          {...rest}
        >
          {children}
        </p>
      );
    },
  };

  // 自动滚动到底部
  useEffect(() => {
    if (contentRef.current && task.status === "running") {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [task.samples, task.status]);

  // 获取当前选中的样本
  const selectedSample = task.samples[selectedSampleIndex];
  const hasMultipleSamples = task.samples.length > 1;
  const completedSamples = task.samples.filter(s => s.status === "completed");
  const slideLinksFromTask = extractSlideLinks(task.artifact);
  const slideLinksFromSamples = task.samples.flatMap((s) => extractSlideLinks(s.artifact));

  const handleDownload = (sampleIndex?: number) => {
    // 如果指定了样本索引，下载该样本的文件
    if (sampleIndex !== undefined && task.samples[sampleIndex]?.artifact?.type === "ppt") {
      const downloadUrl = getDownloadUrl(task.id, sampleIndex);
      window.open(downloadUrl, "_blank");
      return;
    }

    if (!task.artifact) return;

    // 如果是 PPT 类型，优先下载实际生成的文件
    if (task.artifact.type === "ppt" && task.status === "completed") {
      // 使用后端 API 下载实际的 PPT/PDF 文件
      const downloadUrl = getDownloadUrl(task.id);
      window.open(downloadUrl, "_blank");
      return;
    }

    // 其他类型下载文本内容
    const blob = new Blob([task.artifact.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${task.id}.${task.artifact.type === "html" ? "html" : "txt"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadWorkspaceZip = (sampleIndex?: number) => {
    const url = getWorkspaceZipUrl(task.id, sampleIndex);
    window.open(url, "_blank");
  };

  // 获取样本内容用于显示
  const getSampleContent = () => {
    if (task.samples.length === 0) return "";
    // 如果有多个样本，只显示当前选中样本的内容
    if (hasMultipleSamples && selectedSample) {
      return selectedSample.content;
    }
    return task.samples.map(s => s.content).join("\n");
  };

  if (!task.artifact && task.samples.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">等待生成结果...</p>
      </div>
    );
  }

  const sampleContent = getSampleContent();

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden ${
        fullscreen ? "fixed inset-4 z-50" : ""
      }`}
    >
      {/* 头部工具栏 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-800 dark:text-gray-100">
          {task.status === "running" ? (
            <span className="flex items-center gap-2">
              <span className="animate-pulse">🔄</span> 生成中...
              {hasMultipleSamples && ` (${completedSamples.length}/${task.samples.length} 完成)`}
            </span>
          ) : task.artifact ? (
            hasMultipleSamples ? `生成结果 (${completedSamples.length} 个样本)` : "生成结果"
          ) : (
            "实时预览"
          )}
        </h3>
        <div className="flex items-center gap-2">
          {/* 多样本选择器 */}
          {hasMultipleSamples && (
            <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setSelectedSampleIndex(Math.max(0, selectedSampleIndex - 1))}
                disabled={selectedSampleIndex === 0}
                className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="px-2 text-sm font-medium min-w-[80px] text-center">
                样本 {selectedSampleIndex + 1}/{task.samples.length}
              </span>
              <button
                onClick={() => setSelectedSampleIndex(Math.min(task.samples.length - 1, selectedSampleIndex + 1))}
                disabled={selectedSampleIndex === task.samples.length - 1}
                className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
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
          {task.artifact && (
            <button
              onClick={() => handleDownload()}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="下载 PPT/PDF"
            >
              <Download size={18} />
            </button>
          )}
          {task.artifact?.type === "ppt" && (
            <button
              onClick={() => handleDownloadWorkspaceZip(hasMultipleSamples ? selectedSampleIndex : undefined)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title={hasMultipleSamples ? `下载当前样本工作区 ZIP (样本 ${selectedSampleIndex + 1})` : "下载工作区压缩包"}
            >
              <Archive size={18} />
            </button>
          )}
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
      <div
        ref={contentRef}
        className="overflow-auto"
        style={{ maxHeight: fullscreen ? "calc(100vh - 8rem)" : "600px" }}
      >
        {/* 显示交互过程（运行中或有样本内容时） */}
        {(task.status === "running" || sampleContent) && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="prose dark:prose-invert max-w-none prose-sm">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {sampleContent || "正在初始化..."}
              </ReactMarkdown>
            </div>
            {task.status === "running" && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                    <span>正在生成 PPT...</span>
                  </div>
                  <span className="font-medium">{task.progress || 0}%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                    style={{ width: `${task.progress || 0}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* 显示最终结果 */}
        {task.artifact && (
          <div className="p-4">
            {/* HTML 预览 */}
            {task.artifact.type === "html" && previewMode === "preview" && (
              <iframe
                srcDoc={task.artifact.content}
                className="w-full h-full min-h-[500px] border-0"
                sandbox="allow-scripts"
                title="Preview"
              />
            )}

            {/* PPT 完成提示 */}
            {task.artifact.type === "ppt" && (
              <div className="space-y-4">
                {/* 多样本结果展示 */}
                {hasMultipleSamples ? (
                  <div className="space-y-3">
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-2xl">✅</span>
                        <div>
                          <h4 className="font-medium text-green-800 dark:text-green-200">
                            多样本生成完成
                          </h4>
                          <p className="text-sm text-green-600 dark:text-green-400">
                            成功生成 {completedSamples.length}/{task.samples.length} 个样本
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* 样本列表 */}
                    <div className="grid gap-3">
                      {task.samples.map((sample, index) => (
                        <div
                          key={sample.id}
                          className={`border rounded-lg p-3 transition-colors cursor-pointer ${
                            index === selectedSampleIndex
                              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                              : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                          }`}
                          onClick={() => setSelectedSampleIndex(index)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">
                                {sample.status === "completed" ? "✅" :
                                 sample.status === "running" ? "🔄" :
                                 sample.status === "failed" ? "❌" : "⏳"}
                              </span>
                              <span className="font-medium">样本 {index + 1}</span>
                              {sample.status === "running" && (
                                <span className="text-sm text-gray-500">({sample.progress}%)</span>
                              )}
                            </div>
                            {sample.status === "completed" && sample.artifact && (
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownload(index);
                                  }}
                                  className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded flex items-center gap-1 transition-colors"
                                >
                                  <Download size={14} />
                                  下载 PPTX
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDownloadWorkspaceZip(index);
                                  }}
                                  className="px-3 py-1 bg-gray-900 hover:bg-gray-800 text-white text-sm rounded flex items-center gap-1 transition-colors"
                                >
                                  <Archive size={14} />
                                  工作区 ZIP
                                </button>
                              </div>
                            )}
                          </div>
                          {sample.artifact && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 ml-7">
                              {sample.artifact.content}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  /* 单样本结果展示 */
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">✅</span>
                      <div>
                        <h4 className="font-medium text-green-800 dark:text-green-200">
                          PPT 生成完成
                        </h4>
                        <p className="text-sm text-green-600 dark:text-green-400">
                          {task.artifact.content}
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-3">
                      <button
                        onClick={() => handleDownload()}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <Download size={18} />
                        下载 PPTX
                      </button>
                      <button
                          onClick={() => handleDownloadWorkspaceZip()}
                        className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <Archive size={18} />
                        下载工作区 ZIP
                      </button>
                    </div>
                  </div>
                )}

                  {/* HTML 页预览 */}
                  {(slideLinksFromTask.length > 0 || slideLinksFromSamples.length > 0) && (
                    <div className="space-y-2">
                      <h5 className="text-sm font-semibold text-gray-800 dark:text-gray-200">页面预览 (HTML)</h5>
                      <div className="grid gap-3 md:grid-cols-2">
                        {[...slideLinksFromTask, ...slideLinksFromSamples].map((link, idx) => (
                          <div
                            key={`${link}-${idx}`}
                            className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-black"
                          >
                            <iframe
                              src={link}
                              className="w-full h-64 border-0 bg-white"
                              sandbox="allow-scripts allow-same-origin"
                              title={`slide-${idx}`}
                            />
                            <div className="px-3 py-2 text-xs bg-gray-900 text-gray-100 break-all">
                              {link}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            )}

            {/* 代码/Markdown 显示 */}
            {task.artifact.type !== "html" && task.artifact.type !== "ppt" && (
              <>
                {task.artifact.type === "markdown" ? (
                  <div className="prose dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
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
              </>
            )}

            {/* HTML 代码显示 */}
            {task.artifact.type === "html" && previewMode === "code" && (
              <SyntaxHighlighter
                language="html"
                style={vscDarkPlus}
                showLineNumbers
              >
                {task.artifact.content}
              </SyntaxHighlighter>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
