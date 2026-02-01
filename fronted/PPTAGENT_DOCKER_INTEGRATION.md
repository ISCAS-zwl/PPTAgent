# PPTAgent Docker 集成方案

## 📋 概述

本文档介绍如何通过 Docker 容器调用 PPTAgent 服务，实现前后端与 Docker 化 PPTAgent 的集成。

## 🏗️ 架构设计

### 集成模式

系统支持三种集成模式：

1. **LOCAL 模式** - 直接调用本地 PPTAgent Python 模块
2. **DOCKER 模式** - 通过 HTTP API 调用 Docker 容器中的 PPTAgent
3. **AUTO 模式** - 自动选择最佳可用模式（推荐）

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (Next.js)                           │
│                   localhost:3000                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  后端 (FastAPI)                              │
│                   localhost:8000                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PPTAgentIntegrationV2 (集成层)                      │   │
│  │  - 模式选择 (AUTO/LOCAL/DOCKER)                      │   │
│  │  - 健康检查                                          │   │
│  │  - 后备方案                                          │   │
│  └────────────┬─────────────────────┬────────────────────┘   │
│               │                     │                        │
│               ↓                     ↓                        │
│  ┌────────────────────┐  ┌──────────────────────────┐       │
│  │  本地 PPTAgent     │  │  PPTAgentDockerClient    │       │
│  │  (Python 模块)     │  │  (HTTP 客户端)           │       │
│  └────────────────────┘  └──────────┬───────────────┘       │
└─────────────────────────────────────┼───────────────────────┘
                                      │ HTTP API
                                      ↓
                    ┌──────────────────────────────────┐
                    │  deeppresenter-host              │
                    │  (Docker 容器)                   │
                    │  localhost:7861                  │
                    │  - Gradio Web UI                 │
                    │  - PPTAgent 核心服务             │
                    └──────────────────────────────────┘
```

## 🔧 实现细节

### 1. Docker 客户端 (pptagent_docker_client.py)

负责通过 HTTP API 与 Docker 化的 PPTAgent 通信：

```python
class PPTAgentDockerClient:
    """PPTAgent Docker 客户端"""

    async def generate_ppt(prompt: str, options: dict) -> dict:
        """调用 Docker 服务生成 PPT"""

    async def generate_ppt_stream(prompt: str) -> AsyncIterator:
        """流式生成（支持实时进度）"""

    async def health_check() -> bool:
        """健康检查"""
```

**关键特性：**
- 使用 `httpx.AsyncClient` 进行异步 HTTP 请求
- 支持流式响应（Server-Sent Events）
- 自动错误处理和重试
- 超时控制（默认 300 秒）

### 2. 集成层 V2 (pptagent_integration_v2.py)

统一的集成接口，支持多种模式：

```python
class PPTAgentIntegrationV2:
    """支持 LOCAL/DOCKER/AUTO 三种模式"""

    def __init__(mode: IntegrationMode = IntegrationMode.AUTO):
        """初始化，自动检测可用服务"""

    async def generate_ppt(prompt: str) -> dict:
        """自动选择最佳模式生成 PPT"""
```

**模式选择逻辑：**
1. 如果指定了 LOCAL/DOCKER，强制使用该模式
2. AUTO 模式下：
   - 优先使用 Docker（更稳定、隔离性好）
   - Docker 不可用时使用本地模块
   - 都不可用时使用后备方案（生成 Markdown 大纲）

### 3. Docker Compose 配置

更新后的 `docker-compose.yml` 支持跨容器通信：

```yaml
services:
  backend:
    environment:
      - PPTAGENT_DOCKER_URL=http://deeppresenter-host:7861
      - PPTAGENT_MODE=docker
    networks:
      - pptagent-network
      - pptagent_default  # 连接到 PPTAgent 主项目网络

networks:
  pptagent_default:
    external: true  # 使用外部网络
```

## 🚀 部署步骤

### 方案 1: 使用现有的 deeppresenter-host 容器

如果 `deeppresenter-host` 已经在运行：

```bash
# 1. 确认 deeppresenter-host 正在运行
docker ps | grep deeppresenter-host

# 2. 获取其网络名称
docker inspect deeppresenter-host | grep NetworkMode

# 3. 更新 docker-compose.yml 中的网络名称
# 将 pptagent_default 改为实际的网络名称

# 4. 启动前后端服务
cd /home/zhongwenliang2024/PPTAgent/fronted
docker-compose up -d --build
```

### 方案 2: 创建共享网络

创建一个共享网络，让所有容器都加入：

```bash
# 1. 创建共享网络
docker network create pptagent-shared-network

# 2. 将 deeppresenter-host 连接到共享网络
docker network connect pptagent-shared-network deeppresenter-host

# 3. 更新 docker-compose.yml
# 将 pptagent_default 改为 pptagent-shared-network

# 4. 启动服务
cd /home/zhongwenliang2024/PPTAgent/fronted
docker-compose up -d --build
```

### 方案 3: 使用 host 网络模式（最简单）

如果不需要网络隔离，可以使用 host 模式：

```yaml
# docker-compose.yml
services:
  backend:
    network_mode: "host"
    environment:
      - PPTAGENT_DOCKER_URL=http://localhost:7861
```

## 📝 配置说明

### 环境变量

在 `backend/.env` 或 `docker-compose.yml` 中配置：

```bash
# PPTAgent Docker 服务地址
PPTAGENT_DOCKER_URL=http://deeppresenter-host:7861

# 集成模式: local, docker, auto
PPTAGENT_MODE=auto

# 工作空间路径
PPTAGENT_WORKSPACE=/workspace
```

### 配置类 (config.py)

```python
class Settings(BaseSettings):
    pptagent_docker_url: str = "http://deeppresenter-host:7861"
    pptagent_mode: str = "auto"  # local, docker, auto
    pptagent_workspace: str = "/workspace"
```

## 🔌 API 接口

### 假设的 PPTAgent Docker API

基于 Gradio 的服务，可能提供以下接口：

```bash
# 健康检查
GET http://deeppresenter-host:7861/health

# 生成 PPT
POST http://deeppresenter-host:7861/api/generate
Content-Type: application/json
{
  "prompt": "创建一个关于 AI 的演示文稿",
  "template": "default",
  "style": "professional",
  "output_format": "pptx"
}

# 流式生成
POST http://deeppresenter-host:7861/api/generate/stream
(Server-Sent Events)

# 文档分析
POST http://deeppresenter-host:7861/api/analyze
{
  "file_path": "/workspace/document.pdf"
}

# PPT 评估
POST http://deeppresenter-host:7861/api/evaluate
{
  "file_path": "/workspace/presentation.pptx"
}
```

**注意：** 实际 API 端点需要根据 deeppresenter-host 的实际实现进行调整。

## 🧪 测试方法

### 1. 测试 Docker 服务可用性

```bash
# 检查容器状态
docker ps | grep deeppresenter-host

# 测试 Web 界面
curl http://localhost:7861

# 测试健康检查（如果有）
curl http://localhost:7861/health
```

### 2. 测试后端集成

```bash
# 启动后端
cd /home/zhongwenliang2024/PPTAgent/fronted
docker-compose up -d backend

# 查看日志
docker-compose logs -f backend

# 应该看到类似输出：
# "Docker PPTAgent service is available"
# 或
# "Using docker mode for PPT generation"
```

### 3. 测试完整流程

```bash
# 创建任务
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于人工智能的演示文稿",
    "sample_count": 1
  }'

# 查看任务状态
curl http://localhost:8000/api/task/{task_id}
```

## 🔍 故障排查

### 问题 1: 无法连接到 deeppresenter-host

**症状：** 日志显示 "Docker PPTAgent service not available"

**解决方案：**
```bash
# 1. 检查容器是否在同一网络
docker network inspect pptagent_default

# 2. 测试网络连通性
docker exec pptagent-backend ping deeppresenter-host

# 3. 如果不通，使用 host 网络或创建共享网络
```

### 问题 2: API 端点不存在

**症状：** HTTP 404 错误

**解决方案：**
1. 检查 deeppresenter-host 的实际 API 端点
2. 查看 Gradio 文档了解 API 结构
3. 更新 `pptagent_docker_client.py` 中的端点路径

### 问题 3: 超时错误

**症状：** Request timeout

**解决方案：**
```python
# 增加超时时间
pptagent_docker_client = PPTAgentDockerClient(
    base_url="http://deeppresenter-host:7861",
    timeout=600.0  # 10 分钟
)
```

## 📊 性能优化

### 1. 连接池配置

```python
# 使用连接池提高性能
self.client = httpx.AsyncClient(
    timeout=timeout,
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10,
    )
)
```

### 2. 缓存结果

```python
# 使用 Redis 缓存生成结果
async def generate_ppt_cached(prompt: str):
    cache_key = f"ppt:{hash(prompt)}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await generate_ppt(prompt)
    await redis.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 3. 并行处理

```python
# 多个样本并行调用
results = await asyncio.gather(*[
    pptagent_docker_client.generate_ppt(prompt, options)
    for _ in range(sample_count)
])
```

## 🔐 安全考虑

### 1. 网络隔离

- 使用独立的 Docker 网络
- 不要暴露 PPTAgent 服务到公网
- 使用防火墙规则限制访问

### 2. 认证授权

```python
# 添加 API 密钥认证
headers = {
    "Authorization": f"Bearer {settings.pptagent_api_key}"
}
response = await self.client.post(url, headers=headers, json=data)
```

### 3. 输入验证

```python
# 验证用户输入
if len(prompt) > 10000:
    raise ValueError("Prompt too long")

# 清理文件路径
file_path = os.path.normpath(file_path)
if not file_path.startswith("/workspace"):
    raise ValueError("Invalid file path")
```

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| [pptagent_docker_client.py](backend/app/services/pptagent_docker_client.py) | Docker HTTP 客户端 |
| [pptagent_integration_v2.py](backend/app/services/pptagent_integration_v2.py) | 统一集成层 |
| [docker-compose.yml](docker-compose.yml) | Docker 编排配置 |
| [config.py](backend/app/core/config.py) | 配置管理 |
| [requirements.txt](backend/requirements.txt) | Python 依赖（包含 httpx） |

## 🎯 下一步

1. **确认 API 端点** - 查看 deeppresenter-host 的实际 API 文档
2. **调整客户端代码** - 根据实际 API 更新请求格式
3. **测试集成** - 完整测试生成流程
4. **性能调优** - 根据实际使用情况优化配置
5. **监控告警** - 添加服务健康监控

## 💡 最佳实践

1. **使用 AUTO 模式** - 让系统自动选择最佳方案
2. **实现后备方案** - 确保服务不可用时仍能提供基础功能
3. **添加健康检查** - 定期检查 Docker 服务状态
4. **日志记录** - 记录所有 API 调用和错误
5. **优雅降级** - Docker 服务故障时自动切换到本地模式

---

**更新时间**: 2026-01-31
**版本**: 1.0.0
