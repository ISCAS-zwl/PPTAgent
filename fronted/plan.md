

# AI 任务管理平台开发方案 

## 1. 项目概述

构建一个模仿 Manus 交互体验的 AI 平台，支持任务异步后台执行、多样本并行采样以及独立 Artifact 渲染。

## 2. 技术栈要求

* **Frontend**: Next.js 14+ (App Router), Tailwind CSS, Framer Motion (动画), Lucide React (图标).
* **State Management**: Zustand (用于全局任务状态).
* **Backend/Realtime**: FastAPI (Python) + WebSocket + Redis (状态缓存).
* **Task Queue**: Celery (Python) 或 BullMQ (Node.js).

---

## 3. 核心功能实现逻辑

### Feature 1: 后台运行与状态管理

**要求**: 用户发起请求后无需等待，可关闭页面或切换任务，后端持续处理。

* **任务模型 (Task Model)**:
```typescript
type TaskStatus = 'idle' | 'running' | 'collecting' | 'completed' | 'failed';
interface Task {
  id: string;
  prompt: string;
  status: TaskStatus;
  samples: Sample[]; // 存储多个采样结果
  progress: number;  // 0-100
}

```


* **核心流程**:
1. Frontend 调用 API 发起任务 -> 后端存入 Redis 并返回 `taskId`。
2. 后端 Worker 启动异步进程处理。
3. Frontend 通过 WebSocket 订阅 `task:{taskId}` 频道，接收实时状态更新。



### Feature 2: 多次单条 Request 多次采样

**要求**: 同一个 Prompt 触发多个并发生成过程，并在 UI 上并行展示结果。

* **并行策略**:
* 后端接收到 `sample_count: n` 参数。
* 使用 `asyncio.gather` (Python) 同时发起  个 LLM 请求。


* **流式处理**:
* 每个采样分支分配唯一的 `sampleId`。
* 消息格式: `{"type": "chunk", "sampleId": 1, "content": "..."}`。
* 前端 Zustand store 需根据 `sampleId` 将内容追加到对应的缓冲区。



### Feature 3: Artifact 展示

**要求**: 将生成的代码、HTML 或数据图表在独立面板中渲染。

* **实现方案**:
* **Sandboxed Iframe**: 用于渲染生成的 HTML/JS 代码。
* **Code Block Handler**: 自动识别 Markdown 中的代码块，若为 Web 代码则提供 "Preview" 按钮。
* **UI 布局**: 采用双栏布局。左侧为 Chat 流，右侧为动态渲染区（Artifacts Canvas）。



---

## 4. 任务清单 (Agent 指令)

### Phase 1: 基础 UI 构建

* [ ] 创建 Next.js 项目并配置 Tailwind。
* [ ] 仿照 Manus 首页，实现中心化的搜索框布局和底部的“个性化”卡片。
* [ ] 设计左侧/底部任务状态栏，用于展示“后台运行中”的任务列表。

### Phase 2: 后端异步架构

* [ ] 搭建 FastAPI 服务，集成 WebSocket 支持。
* [ ] 实现 `/api/task/create` 接口，支持异步任务分发。
* [ ] 配置 Redis 用于存储任务的中间状态。

### Phase 3: 多采样流式逻辑

* [ ] 实现前端 Zustand Store，支持按 `taskId` 和 `sampleId` 组织数据。
* [ ] 开发并行采样 UI 组件，能够同时展示  个正在生成的窗口（如 Grid 布局）。

### Phase 4: Artifact 渲染系统

* [ ] 创建 `ArtifactViewer` 组件，支持 Markdown 渲染。
* [ ] 集成 `react-syntax-highlighter`。
* [ ] 实现针对 HTML/Tailwind 代码的实时预览沙箱。

