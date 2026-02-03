# DeepPresenter 与前后端集成文档

## 概述

本文档说明如何将 DeepPresenter 的 PPT 生成功能集成到你的前后端系统中。

## 架构设计

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │─────▶│   Backend API   │─────▶│ DeepPresenter   │
│   (Next.js)     │◀─────│   (FastAPI)     │◀─────│   (AgentLoop)   │
│                 │ WS   │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                        │                         │
        │                        │                         │
        ▼                        ▼                         ▼
   用户界面              任务管理/WebSocket          PPT 生成引擎
                           Redis 存储              Research/Design Agent
```

## 核心组件

### 1. DeepPresenter 集成服务

**文件**: `fronted/backend/app/services/deeppresenter_integration.py`

**功能**:
- 封装 DeepPresenter 的 `AgentLoop` 功能
- 提供流式 PPT 生成接口
- 收集 token 使用统计
- 管理活动的生成任务

**主要方法**:
```python
async def generate_ppt(
    task_id: str,
    prompt: str,
    options: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[Dict[str, Any], None]
```

**支持的选项**:
- `template`: 模板名称（auto 或具体模板）
- `num_pages`: 页数（auto 或数字）
- `convert_type`: 转换类型（freeform 或 templates）
- `attachments`: 附件文件列表

### 2. 任务处理器

**文件**: `fronted/backend/app/tasks/task_processor.py`

**修改内容**:
- 使用 `deeppresenter_integration` 替代原有的模拟生成
- 流式处理 Agent 消息并通过 WebSocket 发送到前端
- 处理不同类型的消息：
  - `message`: Agent 消息（system/user/assistant/tool）
  - `file`: 生成的 PPT 文件路径
  - `stats`: Token 使用统计
  - `error`: 错误信息

### 3. 文件上传/下载 API

**文件**: `fronted/backend/app/api/files.py`

**端点**:
- `POST /api/upload`: 上传附件文件
- `GET /api/download/{task_id}`: 下载生成的 PPT
- `GET /api/templates`: 获取可用模板列表

### 4. Docker Compose 配置

**文件**: `docker-compose.yml`

**服务**:
- `redis`: Redis 数据库
- `backend`: FastAPI 后端服务
- `frontend`: Next.js 前端服务
- `deeppresenter-host`: DeepPresenter 独立服务（可选）

## 使用流程

### 1. 启动服务

```bash
# 启动所有服务（前端 + 后端 + Redis）
docker-compose up -d redis backend frontend

# 或启动包括独立 DeepPresenter 服务
docker-compose --profile standalone up -d
```

### 2. 创建任务

前端通过 API 创建任务：

```typescript
const response = await fetch('http://localhost:8000/api/task/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: '创建一个关于人工智能的演示文稿',
    sample_count: 1,
    options: {
      template: 'auto',
      num_pages: 'auto',
      convert_type: 'freeform',
      attachments: []
    }
  })
});
```

### 3. 实时更新

前端通过 WebSocket 接收实时更新：

```typescript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'status':
      // 更新任务状态
      break;
    case 'chunk':
      // 追加内容到显示区域
      break;
    case 'progress':
      // 更新进度条
      break;
    case 'complete':
      // 任务完成，显示下载按钮
      break;
    case 'error':
      // 显示错误信息
      break;
  }
};
```

### 4. 下载结果

```typescript
const downloadUrl = `http://localhost:8000/api/download/${taskId}`;
window.open(downloadUrl, '_blank');
```

## 消息格式

### WebSocket 消息类型

#### 1. 状态更新
```json
{
  "type": "status",
  "task_id": "uuid",
  "status": "running"
}
```

#### 2. 内容块
```json
{
  "type": "chunk",
  "task_id": "uuid",
  "sample_id": "uuid-sample-0",
  "content": "🤖 **Assistant**\n\n正在分析您的需求..."
}
```

#### 3. 进度更新
```json
{
  "type": "progress",
  "task_id": "uuid",
  "sample_id": "uuid-sample-0",
  "progress": 50
}
```

#### 4. 完成
```json
{
  "type": "complete",
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "artifact": {
    "type": "ppt",
    "content": "/opt/workspace/outputs/presentation.pptx",
    "language": "pptx"
  }
}
```

#### 5. 错误
```json
{
  "type": "error",
  "task_id": "uuid",
  "status": "failed",
  "error": "Error message"
}
```

## 环境变量配置

### 后端 (.env)
```bash
# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Workspace
WORKSPACE_DIR=/opt/workspace

# DeepPresenter
DEEPPRESENTER_WORKSPACE_BASE=/opt/workspace
```

### 前端 (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 文件结构

```
PPTAgent/
├── fronted/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── tasks.py          # 任务 API
│   │   │   │   ├── websocket.py      # WebSocket API
│   │   │   │   └── files.py          # 文件 API (新增)
│   │   │   ├── services/
│   │   │   │   ├── deeppresenter_integration.py  # DeepPresenter 集成 (新增)
│   │   │   │   ├── task_service.py
│   │   │   │   └── websocket_manager.py
│   │   │   ├── tasks/
│   │   │   │   └── task_processor.py  # 任务处理器 (已修改)
│   │   │   └── main.py               # FastAPI 应用 (已修改)
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── frontend/
│       ├── app/
│       ├── components/
│       ├── store/
│       ├── Dockerfile
│       └── package.json
├── deeppresenter/                     # DeepPresenter 源码
├── workspace/                         # 共享工作空间
│   ├── uploads/                       # 上传文件
│   └── outputs/                       # 生成文件
└── docker-compose.yml                 # Docker 编排 (已修改)
```

## 关键特性

### 1. 流式处理
- 实时显示 Agent 的思考过程
- 显示工具调用和执行结果
- 渐进式更新进度

### 2. 消息格式化
- 使用 Emoji 区分不同角色
- 工具调用以 JSON 格式显示
- Markdown 渲染支持

### 3. Token 统计
- 分别统计 Research Agent 和 Design Agent
- 显示输入/输出/总计 tokens
- 显示使用的模型名称

### 4. 错误处理
- 捕获并显示生成过程中的错误
- 任务失败时更新状态
- 通过 WebSocket 通知前端

## 测试

### 1. 测试后端 API
```bash
# 健康检查
curl http://localhost:8000/health

# 创建任务
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试 PPT", "sample_count": 1}'

# 获取模板列表
curl http://localhost:8000/api/templates
```

### 2. 测试 WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
```

## 故障排除

### 1. DeepPresenter 不可用
**症状**: 错误消息 "DeepPresenter not available"

**解决方案**:
- 检查 `deeppresenter` 目录是否存在
- 确认 Python 路径配置正确
- 检查依赖是否安装完整

### 2. WebSocket 连接失败
**症状**: 前端无法连接到 WebSocket

**解决方案**:
- 检查 CORS 配置
- 确认后端服务正在运行
- 检查防火墙设置

### 3. 文件下载失败
**症状**: 无法下载生成的 PPT

**解决方案**:
- 检查文件路径是否正确
- 确认工作空间目录权限
- 检查文件是否真正生成

## 下一步

1. **前端增强**:
   - 添加文件上传组件
   - 实现模板选择器
   - 添加进度可视化

2. **后端优化**:
   - 添加任务取消功能
   - 实现任务队列优先级
   - 添加更多错误处理

3. **功能扩展**:
   - 支持多样本并行生成
   - 添加 PPT 预览功能
   - 实现历史记录管理

## 参考资料

- [DeepPresenter 文档](../deeppresenter/README.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Next.js 文档](https://nextjs.org/docs)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
