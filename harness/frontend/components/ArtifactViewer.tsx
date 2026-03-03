"use client";

import { Task, AgentMessage } from "@/types/task";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Code, Eye, Download, Maximize2, ChevronLeft, ChevronRight, FileText, PanelRightOpen, PanelRightClose, ChevronDown, ChevronUp } from "lucide-react";
import remarkGfm from "remark-gfm";
import { getDownloadUrl, getPdfDownloadUrl, getSlidePreviewUrl } from "@/lib/api";

interface ArtifactViewerProps {
  task: Task;
}

interface ToolStep {
  id: string;
  toolName: string;
  arguments?: string;
  result?: string;
}

interface DisplayMessage {
  id: string;
  role: string;
  content: string;
}

// 幻灯片预览组件 - 等比例缩放显示 1280x720 的 HTML 幻灯片
function SlidePreview({ src, title, aspectRatio = '16:9' }: { src: string; title: string; aspectRatio?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [scale, setScale] = useState(0);
  const [key, setKey] = useState(0);

  // 根据宽高比计算原始尺寸
  const slideWidth = aspectRatio === '4:3' ? 1024 : 1280;
  const slideHeight = aspectRatio === '4:3' ? 768 : 720;
  const paddingBottom = aspectRatio === '4:3' ? '75%' : '56.25%';

  useEffect(() => {
    const updateScale = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        if (containerWidth > 0) {
          setScale(containerWidth / slideWidth);
        }
      }
    };

    // 延迟执行确保容器已渲染
    const timer = setTimeout(updateScale, 0);

    const observer = new ResizeObserver(updateScale);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      clearTimeout(timer);
      observer.disconnect();
    };
  }, [slideWidth, aspectRatio]);

  // 当 src 变化时，强制重新加载 iframe
  useEffect(() => {
    setKey((prev: number) => prev + 1);
  }, [src]);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden bg-gray-100 dark:bg-gray-700"
      style={{ paddingBottom }}
    >
      {scale > 0 && (
        <iframe
          key={key}
          ref={iframeRef}
          src={src}
          width={slideWidth}
          height={slideHeight}
          className="absolute top-0 left-0 border-0 bg-white"
          style={{
            transform: `scale(${scale})`,
            transformOrigin: 'top left'
          }}
          sandbox="allow-scripts allow-same-origin"
          title={title}
          loading="lazy"
        />
      )}
    </div>
  );
}

export default function ArtifactViewer({ task }: ArtifactViewerProps) {
  const [previewMode, setPreviewMode] = useState<"code" | "preview">("code");
  const [fullscreen, setFullscreen] = useState(false);
  const [selectedSampleIndex, setSelectedSampleIndex] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedToolSteps, setExpandedToolSteps] = useState<Record<string, boolean>>({});
  const contentRef = useRef<HTMLDivElement>(null);

  const extractSlideLinks = (content: string) => {
    if (!content) return [] as string[];
    const links = new Set<string>();

    // JSON 结构尝试提取
    try {
      const parsed = JSON.parse(content);
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
      // 处理后端发送的 html_files 数组（文件名需要加 slides/ 前缀）
      if (parsed?.html_files && Array.isArray(parsed.html_files)) {
        parsed.html_files.forEach((f: any) => {
          if (typeof f === "string") {
            // 如果文件名不包含路径，添加 slides/ 前缀
            const link = f.includes('/') ? f : `slides/${f}`;
            links.add(link);
          }
        });
      }
    } catch (err) {
      // ignore JSON parse errors; fallback to regex
    }

    // 正则匹配 JSON 代码块中的 html_files
    const jsonBlockRegex = /```json\s*\n([\s\S]*?)\n```/g;
    let jsonMatch;
    while ((jsonMatch = jsonBlockRegex.exec(content)) !== null) {
      try {
        const parsed = JSON.parse(jsonMatch[1]);
        if (parsed?.html_files && Array.isArray(parsed.html_files)) {
          parsed.html_files.forEach((f: any) => {
            if (typeof f === "string") {
              const link = f.includes('/') ? f : `slides/${f}`;
              links.add(link);
            }
          });
        }
      } catch (err) {
        // ignore
      }
    }

    // 正则匹配内容中独立的 {"html_files": [...]} JSON对象（后端progress事件发送的纯JSON）
    const inlineJsonRegex = /\{"html_files"\s*:\s*\[([^\]]*)\]\}/g;
    let inlineMatch;
    while ((inlineMatch = inlineJsonRegex.exec(content)) !== null) {
      try {
        const parsed = JSON.parse(inlineMatch[0]);
        if (parsed?.html_files && Array.isArray(parsed.html_files)) {
          parsed.html_files.forEach((f: any) => {
            if (typeof f === "string") {
              const link = f.includes('/') ? f : `slides/${f}`;
              links.add(link);
            }
          });
        }
      } catch (err) {
        // ignore
      }
    }

    // 正则匹配 "Successfully wrote to slides/slide_XX.html" 或绝对路径
    const successRegex = /Successfully wrote to (?:.*\/)?(slides\/slide_\d+\.html)/gi;
    let match;
    while ((match = successRegex.exec(content)) !== null) {
      links.add(match[1]);
    }

    // 正则匹配 inspect_slide 调用中的 html_file
    const inspectRegex = /"html_file"\s*:\s*"(slides\/slide_\d+\.html)"/gi;
    while ((match = inspectRegex.exec(content)) !== null) {
      links.add(match[1]);
    }

    return Array.from(links);
  };

  const extractFirstHtmlPath = (text: string) => {
    // 只匹配 "Successfully wrote to slides/slide_XX.html" 格式
    const match = text.match(/Successfully wrote to (slides\/slide_\d+\.html)/i);
    return match ? match[1] : null;
  };

  const withVersion = (url: string) => {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}v=${task.updatedAt}`;
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
          const previewUrl = withVersion(
            getSlidePreviewUrl(task.id, htmlPath, hasMultipleSamples ? selectedSampleIndex : undefined)
          );
          return (
            <div className="space-y-2">
              {syntaxNode}
              <div className="rounded-lg border border-gray-700 overflow-hidden bg-black">
                <SlidePreview
                  src={previewUrl}
                  title={`slide-preview-${htmlPath}`}
                  aspectRatio={task.aspectRatio}
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
      return (
        <p
          className={`bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3 mb-3 shadow-sm ${
            className || ""
          }`}
          {...rest}
        >
          {children}
        </p>
      );
    },
    img(props: any) {
      const src = String(props?.src || "");
      const decoded = (() => {
        try {
          return decodeURIComponent(src);
        } catch {
          return src;
        }
      })();
      const normalized = decoded.split("?")[0];
      const name = normalized.split("/").pop() || normalized || "unknown-image";
      return (
        <div className="mb-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-3">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">图片</div>
          <div className="mt-1 text-sm text-gray-800 dark:text-gray-200 break-all">{name}</div>
        </div>
      );
    },
  };

  const stepMarkdownComponents = {
    p(props: any) {
      const { children } = props;
      return <p className="mb-2 text-sm leading-6 text-gray-800 dark:text-gray-200">{children}</p>;
    },
    ul(props: any) {
      const { children } = props;
      return <ul className="mb-2 list-disc pl-5 text-sm text-gray-800 dark:text-gray-200">{children}</ul>;
    },
    ol(props: any) {
      const { children } = props;
      return <ol className="mb-2 list-decimal pl-5 text-sm text-gray-800 dark:text-gray-200">{children}</ol>;
    },
    li(props: any) {
      const { children } = props;
      return <li className="mb-1">{children}</li>;
    },
    code(props: any) {
      const { className, children } = props;
      const content = String(children || "");
      const isBlock = /language-(\w+)/.test(className || "");
      if (isBlock) {
        return (
          <pre className="mb-2 whitespace-pre-wrap break-all text-xs leading-5 text-gray-700 dark:text-gray-300 font-mono">
            {content}
          </pre>
        );
      }
      return <code className="font-mono text-xs text-gray-700 dark:text-gray-300">{content}</code>;
    },
    img(props: any) {
      const src = String(props?.src || "");
      const decoded = (() => {
        try {
          return decodeURIComponent(src);
        } catch {
          return src;
        }
      })();
      const normalized = decoded.split("?")[0];
      const name = normalized.split("/").pop() || normalized || "unknown-image";
      return <p className="mb-2 text-sm text-gray-700 dark:text-gray-300">图片: {name}</p>;
    },
  };

  const normalizeRole = (role?: string) => (role || "assistant").toLowerCase();

  const shouldShowContent = (message: AgentMessage) => {
    const role = normalizeRole(message.role);
    const content = (message.content || "").trim();
    if (!content) return false;
    if (role === "assistant") {
      if (content.startsWith("[") && content.includes("arguments")) return false;
      if (content.includes("Function(")) return false;
      if (content.includes("Tool Call:")) return false;
    }
    return true;
  };

  const stripRolePrefix = (content: string, role: string) => {
    if (!content) return "";
    if (role === "tool") {
      return content.replace(/^[^\n]*\*\*Tool\*\*:\s*/i, "").trim();
    }
    return content;
  };

  const formatJsonLike = (value?: string) => {
    if (!value) return "";
    try {
      return JSON.stringify(JSON.parse(value), null, 2);
    } catch (err) {
      return value;
    }
  };

  const getRoleBadge = (role: string) => {
    if (role === "assistant") return "🤖 Assistant";
    if (role === "tool") return "📝 Tool";
    if (role === "system") return "⚙️ System";
    if (role === "user") return "👤 User";
    return "💬 Message";
  };

  const getSampleMessages = (): AgentMessage[] => {
    if (task.samples.length === 0) return [];
    if (hasMultipleSamples && selectedSample) return selectedSample.messages || [];
    return task.samples.flatMap((s) => s.messages || []);
  };

  const buildDisplayData = (messages: AgentMessage[]): { toolSteps: ToolStep[]; textMessages: DisplayMessage[] } => {
    const toolSteps: ToolStep[] = [];
    const textMessages: DisplayMessage[] = [];
    const pendingStepIndices: number[] = [];

    messages.forEach((message, idx) => {
      const role = normalizeRole(message.role);
      const content = message.content || "";
      const toolCalls = message.toolCalls || [];

      toolCalls.forEach((toolCall, callIdx) => {
        toolSteps.push({
          id: `${idx}-${callIdx}`,
          toolName: toolCall.name || "unknown",
          arguments: toolCall.arguments,
        });
        pendingStepIndices.push(toolSteps.length - 1);
      });

      if (role === "tool" && content.trim()) {
        const pendingStepIndex = pendingStepIndices.shift();
        const stripped = stripRolePrefix(content, role);
        if (pendingStepIndex !== undefined) {
          toolSteps[pendingStepIndex].result = toolSteps[pendingStepIndex].result
            ? `${toolSteps[pendingStepIndex].result}\n\n${stripped}`
            : stripped;
          return;
        }
        toolSteps.push({
          id: `${idx}-orphan`,
          toolName: "unknown",
          result: stripped,
        });
        return;
      }

      if (shouldShowContent(message)) {
        textMessages.push({
          id: `text-${idx}`,
          role,
          content,
        });
      }
    });

    return { toolSteps, textMessages };
  };

  // 自动滚动到底部
  useEffect(() => {
    if (contentRef.current && task.status === "running") {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [task.samples, task.status]);

  // 从 filePath 中提取短 task ID
  const extractShortTaskId = (filePath?: string): string | null => {
    if (!filePath) return null;
    // filePath 格式: /xxx/workspace/20260228/247796aa/presentation.pptx
    const parts = filePath.split('/');
    // 短 ID 是倒数第二个部分
    if (parts.length >= 2) {
      return parts[parts.length - 2];
    }
    return null;
  };

  // 获取当前选中的样本
  const selectedSample = task.samples[selectedSampleIndex];
  const hasMultipleSamples = task.samples.length > 1;
  const completedSamples = task.samples.filter(s => s.status === "completed");

  useEffect(() => {
    setExpandedToolSteps({});
  }, [task.id, selectedSampleIndex]);

  // 提取幻灯片链接和对应的短 ID
  // 优先从 filePath 提取，如果没有则使用 task.id 的前8位（与后端 DeepPresenter 一致）
  const slideLinksWithIds: { link: string; shortId: string }[] = [];
  task.samples.forEach((s) => {
    const shortId = extractShortTaskId(s.filePath) || task.id.slice(0, 8);
    const artifactLinks = extractSlideLinks(s.artifact?.content || "");
    const contentLinks = extractSlideLinks(s.content || "");
    [...artifactLinks, ...contentLinks].forEach(link => {
      if (!slideLinksWithIds.some(item => item.link === link && item.shortId === shortId)) {
        slideLinksWithIds.push({ link, shortId });
      }
    });
  });

  // 当前选中样本的幻灯片链接（用于右侧栏显示）
  const selectedSampleSlideLinks: { link: string; shortId: string }[] = [];
  if (selectedSample) {
    const shortId = extractShortTaskId(selectedSample.filePath) || task.id.slice(0, 8);
    const artifactLinks = extractSlideLinks(selectedSample.artifact?.content || "");
    const contentLinks = extractSlideLinks(selectedSample.content || "");
    [...artifactLinks, ...contentLinks].forEach(link => {
      if (!selectedSampleSlideLinks.some(item => item.link === link && item.shortId === shortId)) {
        selectedSampleSlideLinks.push({ link, shortId });
      }
    });
  }

  // 调试信息
  console.log('[ArtifactViewer] selectedSampleIndex:', selectedSampleIndex);
  console.log('[ArtifactViewer] task.samples.length:', task.samples.length);
  console.log('[ArtifactViewer] selectedSample:', selectedSample);
  console.log('[ArtifactViewer] selectedSampleSlideLinks:', selectedSampleSlideLinks);
  console.log('[ArtifactViewer] slideLinksWithIds:', slideLinksWithIds);
  console.log('[ArtifactViewer] extractSlideLinks test:', {
    artifactContent: selectedSample?.artifact?.content,
    contentSample: selectedSample?.content?.substring(0, 500),
    extractedFromArtifact: extractSlideLinks(selectedSample?.artifact?.content || ""),
    extractedFromContent: extractSlideLinks(selectedSample?.content || "")
  });

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

  const handleDownloadPdf = (sampleIndex?: number) => {
    const url = getPdfDownloadUrl(task.id, sampleIndex);
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
  const sampleMessages = getSampleMessages();
  const { toolSteps, textMessages } = buildDisplayData(sampleMessages);
  const systemMessages = textMessages.filter((m) => m.role === "system");
  const nonSystemMessages = textMessages.filter((m) => m.role !== "system");
  const hasStructuredMessages = sampleMessages.length > 0;

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
          ) : task.artifact || completedSamples.length > 0 ? (
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
              onClick={() => handleDownloadPdf(hasMultipleSamples ? selectedSampleIndex : undefined)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title={hasMultipleSamples ? `下载当前样本 PDF (样本 ${selectedSampleIndex + 1})` : "下载 PDF"}
            >
              <FileText size={18} />
            </button>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
              sidebarOpen
                ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                : "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
            }`}
            title={sidebarOpen ? "关闭幻灯片预览" : "打开幻灯片预览"}
          >
            {sidebarOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
            <span className="text-sm font-medium">
              预览 {slideLinksWithIds.length > 0 ? `(${slideLinksWithIds.length})` : ""}
            </span>
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
      <div className="flex">
        <div
          ref={contentRef}
          className={`overflow-auto flex-1 ${sidebarOpen ? 'w-1/2' : 'w-full'}`}
          style={{ maxHeight: fullscreen ? "calc(100vh - 8rem)" : "600px" }}
        >
        {/* 显示交互过程（运行中或有样本内容时） */}
        {(task.status === "running" || sampleContent || hasStructuredMessages) && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            {hasStructuredMessages ? (
              <div className="space-y-3">
                {systemMessages.map((message) => (
                  <div
                    key={message.id}
                    className="border border-zinc-300 dark:border-zinc-700 rounded-lg p-3 bg-zinc-100 dark:bg-zinc-900/60"
                  >
                    <div className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-2">
                      {getRoleBadge(message.role)}
                    </div>
                    <div className="prose dark:prose-invert max-w-none prose-sm">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={markdownComponents}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}

                {toolSteps.map((step, index) => {
                  const stepId = step.id;
                  const expanded = !!expandedToolSteps[stepId];
                  return (
                    <div
                      key={`tool-step-${stepId}`}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                    >
                      <button
                        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        onClick={() => {
                          setExpandedToolSteps((prev) => ({ ...prev, [stepId]: !prev[stepId] }));
                        }}
                      >
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                          步骤 {index + 1}: 调用工具 `{step.toolName}`
                        </span>
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                      {expanded && (
                        <div className="p-4 space-y-3 bg-white dark:bg-gray-900">
                          {step.arguments && (
                            <div className="rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-900/70 p-3">
                              <p className="text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-2">参数</p>
                              <pre className="whitespace-pre-wrap break-all text-xs leading-5 text-gray-700 dark:text-gray-300 font-mono">
                                {formatJsonLike(step.arguments)}
                              </pre>
                            </div>
                          )}
                          <div className="rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-900/60 p-3">
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">返回结果</p>
                            {step.result ? (
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={stepMarkdownComponents}
                              >
                                {step.result}
                              </ReactMarkdown>
                            ) : (
                              <div className="text-sm text-gray-500 dark:text-gray-400">暂无返回结果</div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}

                {nonSystemMessages.map((message) => (
                  <div
                    key={message.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-white dark:bg-gray-900"
                  >
                    <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                      {getRoleBadge(message.role)}
                    </div>
                    <div className="prose dark:prose-invert max-w-none prose-sm">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={markdownComponents}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}

                {toolSteps.length === 0 && nonSystemMessages.length === 0 && systemMessages.length === 0 && (
                  <div className="text-sm text-gray-500 dark:text-gray-400">正在初始化...</div>
                )}
              </div>
            ) : (
              <div className="prose dark:prose-invert max-w-none prose-sm">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {sampleContent || "正在初始化..."}
                </ReactMarkdown>
              </div>
            )}
            {task.status === "running" && (
              <div className="mt-4 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span>正在生成 PPT...</span>
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
                sandbox="allow-scripts allow-same-origin"
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
                                    handleDownloadPdf(index);
                                  }}
                                  className="px-3 py-1 bg-gray-900 hover:bg-gray-800 text-white text-sm rounded flex items-center gap-1 transition-colors"
                                >
                                  <FileText size={14} />
                                  下载 PDF
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
                          onClick={() => handleDownloadPdf()}
                        className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <FileText size={18} />
                        下载 PDF
                      </button>
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

      {/* 右侧幻灯片预览侧栏 */}
      {sidebarOpen && (
        <div
          className="w-1/2 border-l border-gray-200 dark:border-gray-700 overflow-auto bg-gray-50 dark:bg-gray-900"
          style={{ maxHeight: fullscreen ? "calc(100vh - 8rem)" : "600px" }}
        >
          <div className="p-4">
            <h5 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-3">
              幻灯片预览 {selectedSampleSlideLinks.length > 0 ? `(${selectedSampleSlideLinks.length} 页)` : ""}
              {hasMultipleSamples && ` - 样本 ${selectedSampleIndex + 1}`}
            </h5>
            {selectedSampleSlideLinks.length > 0 ? (
              <div className="space-y-3">
                {selectedSampleSlideLinks.map((item, idx) => {
                  const basePreviewUrl = hasMultipleSamples
                    ? getSlidePreviewUrl(task.id, item.link, selectedSampleIndex)
                    : getSlidePreviewUrl(item.shortId, item.link);
                  const previewUrl = withVersion(basePreviewUrl);
                  return (
                    <div
                      key={`sidebar-${item.link}-${idx}`}
                      className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-800"
                    >
                      <SlidePreview
                        src={previewUrl}
                        title={`slide-sidebar-${idx}`}
                        aspectRatio={task.aspectRatio}
                      />
                      <div className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {idx + 1}. {item.link}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                <PanelRightOpen size={48} className="mb-3 opacity-50" />
                <p className="text-sm">暂无幻灯片</p>
                <p className="text-xs mt-1">生成完成后将在此显示预览</p>
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
