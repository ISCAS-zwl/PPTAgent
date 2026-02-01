# PPTAgent Backend

基于 FastAPI 的 AI 任务管理平台后端服务。

## 技术栈

- **FastAPI** - 现代 Python Web 框架
- **WebSocket** - 实时双向通信
- **Redis** - 任务状态缓存
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器

## 功能特性

- ✅ RESTful API 接口
- ✅ WebSocket 实时通信
- ✅ Redis 状态管理
- ✅ 异步任务处理
- ✅ 多样本并行采样
- ✅ 任务队列管理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

创建 `.env` 文件：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

API_HOST=0.0.0.0
API_PORT=8000

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

MAX_SAMPLE_COUNT=4
DEFAULT_SAMPLE_COUNT=1

PPTAGENT_WORKSPACE=/workspace
```

## 启动服务

### 方式 1: 使用启动脚本

```bash
./start.sh
```

### 方式 2: 手动启动

```bash
# 启动 Redis
redis-server

# 启动 FastAPI
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

启动服务后访问：

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── tasks.py           # 任务相关 API
│   │   └── websocket.py       # WebSocket 端点
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   └── redis.py           # Redis 连接
│   ├── models/                 # 数据模型
│   │   └── task.py            # 任务模型
│   ├── services/               # 业务服务
│   │   ├── task_service.py    # 任务服务
│   │   └── websocket_manager.py # WebSocket 管理
│   ├── tasks/                  # 任务处理
│   │   └── task_processor.py  # 任务处理器
│   └── main.py                 # 应用入口
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量
└── start.sh                    # 启动脚本
```

## API 端点

### 任务管理

#### 创建任务

```http
POST /api/task/create
Content-Type: application/json

{
  "prompt": "创建一个关于 AI 的演示文稿",
  "sample_count": 2,
  "options": {
    "template": "modern",
    "style": "professional"
  }
}
```

响应：

```json
{
  "task_id": "uuid",
  "status": "created"
}
```

#### 获取任务详情

```http
GET /api/task/{task_id}
```

#### 列出所有任务

```http
GET /api/tasks?limit=50
```

#### 删除任务

```http
DELETE /api/task/{task_id}
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// 订阅任务更新
ws.send(JSON.stringify({
  type: 'subscribe',
  task_id: 'task-uuid'
}));

// 接收消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

## WebSocket 消息格式

### 客户端 -> 服务器

```json
{
  "type": "subscribe",
  "task_id": "uuid"
}
```

```json
{
  "type": "unsubscribe",
  "task_id": "uuid"
}
```

### 服务器 -> 客户端

#### 状态更新

```json
{
  "type": "status",
  "task_id": "uuid",
  "status": "running"
}
```

#### 流式内容

```json
{
  "type": "chunk",
  "task_id": "uuid",
  "sample_id": "sample-uuid",
  "content": "生成的内容片段"
}
```

#### 进度更新

```json
{
  "type": "progress",
  "task_id": "uuid",
  "sample_id": "sample-uuid",
  "progress": 50
}
```

#### 完成

```json
{
  "type": "complete",
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "artifact": {
    "type": "markdown",
    "content": "最终生成的内容"
  }
}
```

#### 错误

```json
{
  "type": "error",
  "task_id": "uuid",
  "status": "failed",
  "error": "错误信息"
}
```

## 任务处理流程

1. 客户端通过 API 创建任务
2. 任务被添加到 Redis 和任务队列
3. 后台工作器从队列中取出任务
4. 并行处理多个样本（如果有）
5. 通过 WebSocket 实时推送进度和内容
6. 生成最终的 Artifact
7. 更新任务状态为完成

## 集成 PPTAgent

要集成现有的 PPTAgent 功能，修改 `app/tasks/task_processor.py`：

```python
from pptagent import PPTAgentServer

class TaskProcessor:
    @staticmethod
    async def _generate_artifact(task: Task) -> Artifact:
        # 调用 PPTAgent 生成 PPT
        agent = PPTAgentServer()
        result = await agent.generate_ppt(task.prompt, task.options)

        return Artifact(
            type=ArtifactType.PPT,
            content=result.content,
        )
```

## 开发指南

### 添加新的 API 端点

在 `app/api/` 目录下创建新的路由文件：

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.get("/")
async def my_endpoint():
    return {"message": "Hello"}
```

在 `app/main.py` 中注册路由：

```python
from app.api import my_feature
app.include_router(my_feature.router)
```

### 扩展任务处理逻辑

修改 `app/tasks/task_processor.py` 中的处理方法：

```python
@staticmethod
async def _process_single_sample(task: Task):
    # 自定义处理逻辑
    pass
```

### 添加新的 WebSocket 消息类型

在 `app/models/task.py` 中扩展 `WebSocketMessage` 模型，然后在 `app/api/websocket.py` 中处理新的消息类型。

## 测试

```bash
# 测试 API
curl http://localhost:8000/health

# 创建任务
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试任务", "sample_count": 1}'
```

## 部署

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 使用 Docker Compose

参考项目根目录的 `docker-compose.yml`。

## 故障排除

### Redis 连接失败

确保 Redis 服务正在运行：

```bash
redis-cli ping
```

### WebSocket 连接断开

检查 CORS 配置和防火墙设置。

### 任务处理缓慢

调整任务队列的工作器数量或使用 Celery 进行分布式处理。
