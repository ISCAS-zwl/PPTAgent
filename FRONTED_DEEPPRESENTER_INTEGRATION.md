# Fronted 与 DeepPresenter 集成文档

## 概述

本文档描述了如何将 `fronted` 路径下的前后端系统与 `deeppresenter` 集成，实现完整的 PPT 生成功能。

## 架构说明

### 系统组件

1. **Frontend (Next.js)** - 位于 `fronted/frontend/`
   - 提供用户界面
   - 通过 WebSocket 实时接收生成进度
   - 支持文件上传和下载

2. **Backend (FastAPI)** - 位于 `fronted/backend/`
   - RESTful API 服务
   - WebSocket 服务用于实时通信
   - 任务队列管理
   - 集成 DeepPresenter

3. **DeepPresenter** - 位于 `deeppresenter/`
   - AI Agent 系统
   - PPT 生成核心逻辑
   - 支持多种模板和生成模式

4. **Redis**
   - 任务状态存储
   - 会话管理

### 数据流

```
用户输入 → Frontend → Backend API → Task Queue → DeepPresenter AgentLoop → PPT 文件
                                          ↓
                                    WebSocket 实时反馈
```

## 集成实现

### 1. Backend 集成 DeepPresenter

#### 文件结构

```
fronted/backend/
├── app/
│   ├── api/
│   │   ├── tasks.py          # 任务 API
│   │   ├── websocket.py      # WebSocket 端点
│   │   └── files.py          # 文件上传/下载
│   ├── services/
│   │   ├── deeppresenter_integration.py  # DeepPresenter 集成
│   │   ├── task_service.py
│   │   └── websocket_manager.py
│   ├── tasks/
│   │   └── task_processor.py  # 任务处理器
│   └── main.py
├── requirements.txt
└── Dockerfile
```

#### 核心集成代码

**deeppresenter_integration.py** ([fronted/backend/app/services/deeppresenter_integration.py](fronted/backend/app/services/deeppresenter_integration.py))

```python
class DeepPresenterIntegration:
    """DeepPresenter 集成类"""

    async def generate_ppt(
        self,
        task_id: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成 PPT（流式返回）

        Yields:
            - type: 'message' - Agent 消息
            - type: 'file' - 文件生成完成
            - type: 'stats' - Token 统计
            - type: 'error' - 错误信息
        """
```

**task_processor.py** ([fronted/backend/app/tasks/task_processor.py](fronted/backend/app/tasks/task_processor.py))

```python
async def _process_single_sample(task: Task):
    """处理单个样本 - 使用 DeepPresenter"""
    async for message in deeppresenter_integration.generate_ppt(
        task_id=task.id,
        prompt=task.prompt,
        options=task.options,
    ):
        # 处理不同类型的消息
        if message['type'] == 'message':
            # 发送 Agent 消息到前端
        elif message['type'] == 'file':
            # 文件生成完成
        elif message['type'] == 'stats':
            # Token 统计
```

### 2. 依赖配置

#### requirements.txt

已添加 DeepPresenter 所需的所有依赖：

```txt
# 原有依赖
fastapi==0.109.0
uvicorn[standard]==0.27.0
...

# DeepPresenter 依赖
aiohttp>=3.9.0
arxiv>=2.2.0
colorlog>=6.9.0
docker>=7.1.0
jsonlines>=4.0.0
openai>=1.108.2
playwright>=1.55.0
pptagent>=0.2.18
python-pptx>=0.6.21
...
```

#### Dockerfile

已更新以支持 DeepPresenter 的系统依赖：

```dockerfile
# 安装系统依赖（包括 DeepPresenter 需要的依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    wget \
    nodejs \
    npm \
    imagemagick \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright 浏览器
RUN playwright install chromium && \
    playwright install-deps chromium
```

### 3. Docker Compose 配置

#### docker-compose.yml

```yaml
services:
  # Redis 服务
  redis:
    image: docker.1ms.run/library/redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - pptagent-network

  # 后端 API 服务
  backend:
    build:
      context: ./fronted/backend
    ports:
      - "8000:8000"
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
      WORKSPACE_DIR: /opt/workspace
      DEEPPRESENTER_WORKSPACE_BASE: /opt/workspace
      PYTHONPATH: /app:/usr/src/pptagent
    volumes:
      - ~/pptagent_workspace:/opt/workspace
      - ./fronted/backend:/app
      - ./deeppresenter:/usr/src/pptagent/deeppresenter  # 挂载 deeppresenter
    depends_on:
      - redis
    networks:
      - pptagent-network

  # 前端服务
  frontend:
    build:
      context: ./fronted/frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws
    depends_on:
      - backend
    networks:
      - pptagent-network

networks:
  pptagent-network:
    driver: bridge
```

## 使用方法

### 1. 启动服务

```bash
# 构建并启动所有服务
docker-compose up --build

# 或者分别启动
docker-compose up redis -d
docker-compose up backend -d
docker-compose up frontend -d
```

### 2. 访问服务

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 3. 创建 PPT 任务

#### 通过前端界面

1. 访问 http://localhost:3000
2. 点击"新建任务"
3. 输入提示词，例如："制作一个关于人工智能的演示文稿"
4. 选择选项：
   - 页数：auto 或指定数字
   - 输出类型：freeform（自由生成）或 templates（使用模板）
   - 模板：如果选择 templates，可以选择具体模板
5. 上传附件（可选）
6. 点击"生成"

#### 通过 API

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "制作一个关于人工智能的演示文稿",
    "options": {
      "num_pages": "auto",
      "convert_type": "freeform",
      "template": "auto"
    }
  }'
```

### 4. 实时监控进度

前端会通过 WebSocket 实时接收：
- Agent 消息（研究、设计过程）
- 工具调用信息
- 进度更新
- Token 使用统计
- 最终文件路径

### 5. 下载生成的 PPT

```bash
# 通过 API 下载
curl -O "http://localhost:8000/api/download/{task_id}"

# 或在前端界面点击下载按钮
```

## API 端点

### 任务管理

- `POST /api/tasks` - 创建新任务
- `GET /api/tasks` - 获取所有任务
- `GET /api/tasks/{task_id}` - 获取任务详情
- `DELETE /api/tasks/{task_id}` - 删除任务

### 文件管理

- `POST /api/upload` - 上传附件
- `GET /api/download/{task_id}` - 下载生成的 PPT
- `GET /api/templates` - 获取可用模板列表

### WebSocket

- `WS /ws` - WebSocket 连接，用于实时接收任务更新

## 配置选项

### 环境变量

在 `fronted/backend/.env` 中配置：

```env
# Redis
REDIS_HOST=localhost
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

### DeepPresenter 配置

在 `deeppresenter/deeppresenter/config.yaml` 中配置：

```yaml
# 模型配置
research_agent:
  endpoints:
    - base_url: "your_api_url"
      model: "your_model"
      api_key: "your_api_key"

design_agent:
  endpoints:
    - base_url: "your_api_url"
      model: "your_model"
      api_key: "your_api_key"
```

## 生成选项说明

### num_pages
- `"auto"`: 自动确定页数
- `"5"`, `"10"`, 等: 指定页数

### convert_type
- `"freeform"`: 自由生成模式（使用 DeepPresenter）
  - 更灵活，AI 自主设计布局
  - 适合创意性内容

- `"templates"`: 模板模式（使用 PPTAgent）
  - 使用预定义模板
  - 更规范，适合商务场景

### template
- `"auto"`: 自动选择模板
- 具体模板名称：使用指定模板（仅在 templates 模式下有效）

## 工作流程详解

### 1. 任务创建
```
用户提交 → Backend 创建任务 → 存储到 Redis → 加入任务队列
```

### 2. 任务处理
```
Task Worker 取出任务
    ↓
创建 AgentLoop 实例
    ↓
Research Agent 研究内容
    ↓
Design Agent 设计布局
    ↓
生成 HTML/PDF
    ↓
转换为 PPTX
    ↓
保存文件
```

### 3. 实时反馈
```
每个步骤 → 生成消息 → WebSocket 推送 → 前端显示
```

## 故障排查

### 1. DeepPresenter 导入失败

**问题**: `ModuleNotFoundError: No module named 'deeppresenter'`

**解决方案**:
- 检查 docker-compose.yml 中的 volume 挂载
- 确保 PYTHONPATH 包含 `/usr/src/pptagent`
- 重新构建容器: `docker-compose build backend`

### 2. Playwright 浏览器未安装

**问题**: `Executable doesn't exist at /ms-playwright/chromium-*/chrome-linux/chrome`

**解决方案**:
- 确保 Dockerfile 中执行了 `playwright install chromium`
- 重新构建镜像

### 3. 文件权限问题

**问题**: 无法写入 workspace 目录

**解决方案**:
```bash
# 确保 workspace 目录有正确的权限
mkdir -p ~/pptagent_workspace
chmod 777 ~/pptagent_workspace
```

### 4. Redis 连接失败

**问题**: `ConnectionError: Error connecting to Redis`

**解决方案**:
- 确保 Redis 服务正在运行
- 检查网络配置
- 验证环境变量 `REDIS_HOST` 和 `REDIS_PORT`

## 性能优化

### 1. 并发处理

可以在 `task_processor.py` 中调整并发数：

```python
# 增加 worker 数量
async def start_task_worker(num_workers: int = 3):
    for _ in range(num_workers):
        asyncio.create_task(task_worker())
```

### 2. 缓存优化

- 使用 Redis 缓存模板列表
- 缓存常用的研究结果

### 3. 资源限制

在 docker-compose.yml 中添加资源限制：

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

## 扩展功能

### 1. 添加新的生成模式

在 `deeppresenter_integration.py` 中扩展：

```python
async def generate_with_custom_mode(self, ...):
    # 自定义生成逻辑
    pass
```

### 2. 支持更多文件格式

修改 `files.py` 添加新的导出格式：

```python
@router.get("/export/{task_id}/{format}")
async def export_file(task_id: str, format: str):
    # 支持 PDF, HTML 等格式
    pass
```

### 3. 批量处理

实现批量任务处理功能：

```python
@router.post("/api/tasks/batch")
async def create_batch_tasks(requests: List[TaskRequest]):
    # 批量创建任务
    pass
```

## 总结

通过以上集成，fronted 系统已经完全连接到 deeppresenter，实现了：

✅ 完整的 PPT 生成流程
✅ 实时进度反馈
✅ 文件上传和下载
✅ 多种生成模式支持
✅ Token 使用统计
✅ 容器化部署

现在可以通过前端界面或 API 直接使用 DeepPresenter 的强大功能来生成专业的 PPT！
