# PPTAgent 项目架构文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
│                    (http://localhost:3000)                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTP/WebSocket
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      Next.js 前端                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Components (React)                                   │  │
│  │  - SearchBox: 搜索框                                  │  │
│  │  - TaskGrid: 任务列表                                 │  │
│  │  - TaskStatusBar: 状态栏                              │  │
│  │  - ArtifactViewer: 结果查看器                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State Management (Zustand)                          │  │
│  │  - tasks: 任务列表                                    │  │
│  │  - ws: WebSocket 连接                                 │  │
│  │  - selectedTaskId: 当前选中任务                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ REST API / WebSocket
                 │
┌────────────────▼────────────────────────────────────────────┐
│                     FastAPI 后端                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Routes                                           │  │
│  │  - POST /api/task/create: 创建任务                    │  │
│  │  - GET /api/task/{id}: 获取任务                       │  │
│  │  - GET /api/tasks: 列出任务                           │  │
│  │  - WS /ws: WebSocket 连接                             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services                                             │  │
│  │  - TaskService: 任务管理                              │  │
│  │  - WebSocketManager: WebSocket 管理                   │  │
│  │  - PPTAgentIntegration: PPTAgent 集成                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Task Processor                                       │  │
│  │  - 异步任务队列                                       │  │
│  │  - 并行样本处理                                       │  │
│  │  - Artifact 生成                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │
┌────────────────▼────────────────────────────────────────────┐
│                         Redis                                │
│  - 任务状态缓存                                              │
│  - 任务队列                                                  │
│  - 会话管理                                                  │
└──────────────────────────────────────────────────────────────┘
                 │
                 │
┌────────────────▼────────────────────────────────────────────┐
│                      PPTAgent 核心                           │
│  - PPT 生成                                                  │
│  - 文档分析                                                  │
│  - 质量评估                                                  │
└──────────────────────────────────────────────────────────────┘
```

## 数据流

### 1. 任务创建流程

```
用户输入 → SearchBox → API POST /api/task/create
                              ↓
                        创建 Task 对象
                              ↓
                        保存到 Redis
                              ↓
                        添加到任务队列
                              ↓
                        返回 task_id
                              ↓
                        前端添加到本地状态
                              ↓
                        WebSocket 订阅任务
```

### 2. 任务处理流程

```
任务队列 → TaskProcessor.process_task()
                ↓
          更新状态为 RUNNING
                ↓
          WebSocket 推送状态
                ↓
     ┌──────────┴──────────┐
     │                     │
单样本处理          多样本并行处理
     │                     │
     │              asyncio.gather()
     │                     │
     └──────────┬──────────┘
                ↓
          流式推送内容
                ↓
          生成 Artifact
                ↓
          更新状态为 COMPLETED
                ↓
          WebSocket 推送完成
```

### 3. WebSocket 消息流

```
客户端                    服务器
  │                         │
  ├─ subscribe ────────────>│
  │                         │
  │<──── subscribed ────────┤
  │                         │
  │<──── status ────────────┤ (任务状态更新)
  │                         │
  │<──── chunk ─────────────┤ (流式内容)
  │                         │
  │<──── progress ──────────┤ (进度更新)
  │                         │
  │<──── complete ──────────┤ (任务完成)
  │                         │
```

## 核心模块说明

### 前端模块

#### 1. TaskStore (store/taskStore.ts)
- 管理全局任务状态
- WebSocket 连接管理
- 任务订阅和更新
- 消息处理分发

#### 2. SearchBox (components/SearchBox.tsx)
- 用户输入界面
- 样本数量选择
- 任务创建请求

#### 3. TaskGrid (components/TaskGrid.tsx)
- 任务列表展示
- 状态可视化
- 进度显示
- 多样本网格

#### 4. ArtifactViewer (components/ArtifactViewer.tsx)
- Markdown 渲染
- 代码高亮
- HTML 预览（沙箱）
- 下载功能

### 后端模块

#### 1. TaskService (services/task_service.py)
- Redis 操作封装
- 任务 CRUD
- 状态管理

#### 2. WebSocketManager (services/websocket_manager.py)
- 连接管理
- 订阅机制
- 消息广播
- 断线处理

#### 3. TaskProcessor (tasks/task_processor.py)
- 异步任务处理
- 并行样本生成
- 进度跟踪
- Artifact 生成

#### 4. PPTAgentIntegration (services/pptagent_integration.py)
- PPTAgent 接口封装
- PPT 生成
- 文档分析
- 质量评估

## 技术实现细节

### 1. 状态管理

使用 Zustand 实现轻量级状态管理：

```typescript
interface TaskStore {
  tasks: Task[];
  ws: WebSocket | null;
  selectedTaskId: string | null;

  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  connectWebSocket: () => void;
}
```

### 2. WebSocket 通信

#### 消息类型

- `status`: 任务状态更新
- `chunk`: 流式内容推送
- `progress`: 进度更新
- `complete`: 任务完成
- `error`: 错误信息

#### 订阅机制

```python
class ConnectionManager:
    active_connections: Set[WebSocket]
    task_subscriptions: Dict[str, Set[WebSocket]]

    async def subscribe_task(websocket, task_id)
    async def send_to_task_subscribers(task_id, message)
```

### 3. 并行处理

使用 asyncio.gather 实现多样本并行：

```python
async def _process_multiple_samples(task: Task):
    async def process_sample(sample: Sample):
        # 处理单个样本
        pass

    await asyncio.gather(*[
        process_sample(sample)
        for sample in task.samples
    ])
```

### 4. Redis 数据结构

```
task:{task_id}          # Hash: 任务详情
tasks                   # Sorted Set: 任务列表（按时间排序）
```

## 扩展指南

### 添加新的任务类型

1. 在 `models/task.py` 中扩展 `TaskStatus` 或 `ArtifactType`
2. 在 `TaskProcessor` 中添加处理逻辑
3. 在前端添加对应的 UI 组件

### 集成新的 AI 模型

1. 在 `services/` 创建新的集成模块
2. 实现统一的接口
3. 在 `TaskProcessor` 中调用

### 添加认证授权

1. 后端添加 JWT 中间件
2. 前端添加 token 管理
3. WebSocket 连接时验证 token

## 性能优化建议

### 前端优化

1. **代码分割**: 使用 Next.js 动态导入
2. **虚拟滚动**: 大量任务时使用虚拟列表
3. **防抖节流**: 搜索输入使用防抖
4. **缓存策略**: 使用 SWR 或 React Query

### 后端优化

1. **连接池**: Redis 连接池配置
2. **并发限制**: 限制同时处理的任务数
3. **消息批处理**: WebSocket 消息批量发送
4. **缓存预热**: 常用数据提前加载

## 监控和日志

### 日志级别

- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

### 监控指标

- 任务创建速率
- 任务完成时间
- WebSocket 连接数
- Redis 内存使用
- API 响应时间

## 安全考虑

1. **输入验证**: 所有用户输入都需验证
2. **XSS 防护**: HTML 渲染使用沙箱 iframe
3. **CORS 配置**: 限制允许的源
4. **速率限制**: API 请求频率限制
5. **认证授权**: 生产环境必须启用

## 部署清单

- [ ] 配置环境变量
- [ ] 设置 Redis 密码
- [ ] 配置 CORS 白名单
- [ ] 启用 HTTPS
- [ ] 配置日志收集
- [ ] 设置监控告警
- [ ] 备份策略
- [ ] 负载均衡
- [ ] CDN 配置
- [ ] 性能测试
