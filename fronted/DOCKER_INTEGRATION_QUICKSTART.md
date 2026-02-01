# PPTAgent Docker 集成 - 快速开始

## 🚀 快速部署

### 前提条件

确保 `deeppresenter-host` 容器正在运行：

```bash
docker ps | grep deeppresenter-host
# 应该看到: deeppresenter-host ... Up ... 0.0.0.0:7861->7861/tcp
```

### 方法 1: 使用共享网络（推荐）

```bash
# 1. 创建共享网络
docker network create pptagent-shared-network

# 2. 连接现有的 deeppresenter-host 到共享网络
docker network connect pptagent-shared-network deeppresenter-host

# 3. 更新 docker-compose.yml
cd /home/zhongwenliang2024/PPTAgent/fronted
# 将 pptagent_default 改为 pptagent-shared-network

# 4. 启动服务
docker-compose up -d --build
```

### 方法 2: 使用 Host 网络（最简单）

```bash
# 1. 修改 docker-compose.yml 中的 backend 服务
services:
  backend:
    network_mode: "host"
    environment:
      - PPTAGENT_DOCKER_URL=http://localhost:7861

# 2. 启动服务
docker-compose up -d --build
```

### 方法 3: 直接使用现有网络

```bash
# 1. 查找 deeppresenter-host 的网络
docker inspect deeppresenter-host | grep -A 5 "Networks"

# 2. 假设网络名为 pptagent_default，更新 docker-compose.yml
networks:
  pptagent_default:
    external: true

# 3. 启动服务
docker-compose up -d --build
```

## 🧪 测试集成

```bash
# 1. 检查后端日志
docker-compose logs -f backend

# 应该看到:
# "Docker PPTAgent service is available"
# 或
# "Using docker mode for PPT generation"

# 2. 测试 API
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于人工智能的演示文稿",
    "sample_count": 1
  }'

# 3. 访问前端
open http://localhost:3000
```

## 📝 配置选项

### 环境变量

在 `docker-compose.yml` 中配置：

```yaml
environment:
  # PPTAgent Docker 服务地址
  - PPTAGENT_DOCKER_URL=http://deeppresenter-host:7861

  # 集成模式: auto (推荐), docker, local
  - PPTAGENT_MODE=auto

  # 工作空间
  - PPTAGENT_WORKSPACE=/workspace
```

### 集成模式说明

- **auto** (推荐): 自动选择最佳可用模式
  - 优先使用 Docker 服务
  - Docker 不可用时使用本地模块
  - 都不可用时使用后备方案

- **docker**: 强制使用 Docker 服务
  - 如果 Docker 服务不可用会失败

- **local**: 强制使用本地 Python 模块
  - 需要本地安装 PPTAgent

## 🔍 故障排查

### 问题: 无法连接到 deeppresenter-host

```bash
# 测试网络连通性
docker exec pptagent-backend ping deeppresenter-host

# 如果失败，检查网络配置
docker network ls
docker network inspect pptagent-shared-network
```

### 问题: Docker 服务不可用

系统会自动降级到本地模式或后备方案，查看日志：

```bash
docker-compose logs backend | grep -i "pptagent\|docker"
```

## 📚 完整文档

详细文档请参考: [PPTAGENT_DOCKER_INTEGRATION.md](PPTAGENT_DOCKER_INTEGRATION.md)

---

**提示**: 如果遇到问题，系统会自动使用后备方案生成 Markdown 大纲，不会影响基本功能。
