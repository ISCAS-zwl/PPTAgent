# PPTAgent Frontend

基于 Next.js 14 的 AI 任务管理平台前端应用。

## 技术栈

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS** - 样式框架
- **Framer Motion** - 动画库
- **Zustand** - 状态管理
- **Lucide React** - 图标库
- **React Markdown** - Markdown 渲染
- **React Syntax Highlighter** - 代码高亮

## 功能特性

- ✅ 后台任务异步执行
- ✅ 实时 WebSocket 连接
- ✅ 多样本并行采样
- ✅ Artifact 渲染系统
- ✅ 响应式设计
- ✅ 暗色模式支持

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 构建生产版本

```bash
npm run build
npm start
```

## 项目结构

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 根布局
│   ├── page.tsx           # 首页
│   └── globals.css        # 全局样式
├── components/            # React 组件
│   ├── SearchBox.tsx      # 搜索框
│   ├── TaskGrid.tsx       # 任务网格
│   ├── TaskStatusBar.tsx  # 任务状态栏
│   └── ArtifactViewer.tsx # Artifact 查看器
├── store/                 # Zustand 状态管理
│   └── taskStore.ts       # 任务状态
├── types/                 # TypeScript 类型定义
│   └── task.ts            # 任务类型
├── lib/                   # 工具函数
│   └── api.ts             # API 调用
└── public/                # 静态资源
```

## 核心功能说明

### 1. 任务管理

使用 Zustand 管理全局任务状态，支持：
- 创建新任务
- 实时更新任务状态
- 多样本并行处理
- WebSocket 实时通信

### 2. Artifact 渲染

支持多种内容类型：
- HTML 预览（沙箱 iframe）
- Markdown 渲染
- 代码高亮显示
- 全屏查看模式

### 3. WebSocket 通信

实时接收后端推送的消息：
- 任务状态更新
- 流式内容推送
- 进度更新
- 错误处理

## 开发指南

### 添加新组件

在 `components/` 目录下创建新组件：

```tsx
"use client";

export default function MyComponent() {
  return <div>My Component</div>;
}
```

### 扩展状态管理

在 `store/taskStore.ts` 中添加新的状态和操作：

```typescript
interface TaskStore {
  // 添加新状态
  myState: string;

  // 添加新操作
  setMyState: (value: string) => void;
}
```

### API 调用

在 `lib/api.ts` 中添加新的 API 函数：

```typescript
export async function myApiCall() {
  const response = await fetch(`${API_BASE_URL}/api/my-endpoint`);
  return response.json();
}
```
