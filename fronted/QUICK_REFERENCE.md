# PPTAgent 快速参考指南

## 🚀 快速启动

### 最简单的方式（Docker）
```bash
cd /home/zhongwenliang2024/PPTAgent/fronted
docker-compose up -d
```

### 一键启动脚本
```bash
cd /home/zhongwenliang2024/PPTAgent/fronted
./start-all.sh
```

## 📍 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | 用户界面 |
| 后端 API | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Redis | localhost:6379 | 数据缓存 |

## 🎯 核心功能

### 1. 创建任务
- 在搜索框输入需求
- 选择样本数量（1-4）
- 点击"生成"按钮

### 2. 查看进度
- 任务列表实时更新
- 进度条显示完成度
- 底部状态栏显示后台任务

### 3. 查看结果
- 点击任务卡片
- 右侧显示 Artifact
- 支持下载和全屏查看

## 📝 API 快速参考

### 创建任务
```bash
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于 AI 的演示文稿",
    "sample_count": 2
  }'
```

### 获取任务
```bash
curl http://localhost:8000/api/task/{task_id}
```

### 列出任务
```bash
curl http://localhost:8000/api/tasks
```

## 🔌 WebSocket 消息

### 订阅任务
```json
{
  "type": "subscribe",
  "task_id": "uuid"
}
```

### 接收消息类型
- `status` - 状态更新
- `chunk` - 流式内容
- `progress` - 进度更新
- `complete` - 任务完成
- `error` - 错误信息

## 🛠️ 常用命令

### Docker 命令
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps
```

### 前端命令
```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 生产模式
npm start
```

### 后端命令
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
./start.sh

# 或手动启动
python -m uvicorn app.main:app --reload
```

### Redis 命令
```bash
# 启动 Redis
redis-server

# 检查状态
redis-cli ping

# 查看所有键
redis-cli keys "*"

# 清空数据
redis-cli flushall
```

## 🐛 故障排除

### 问题：Redis 连接失败
```bash
# 检查 Redis
redis-cli ping

# 启动 Redis
redis-server
```

### 问题：端口被占用
```bash
# 查看端口占用
lsof -i :3000
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 问题：前端构建失败
```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

### 问题：后端启动失败
```bash
cd backend
pip install -r requirements.txt --force-reinstall
```

## 📂 项目结构速查

```
fronted/
├── frontend/          # Next.js 前端
│   ├── app/          # 页面和布局
│   ├── components/   # React 组件
│   ├── store/        # 状态管理
│   └── types/        # 类型定义
├── backend/          # FastAPI 后端
│   └── app/
│       ├── api/      # API 路由
│       ├── services/ # 业务逻辑
│       └── tasks/    # 任务处理
└── docker-compose.yml # Docker 配置
```

## 🔧 配置文件

### 后端配置 (backend/.env)
```env
REDIS_HOST=localhost
REDIS_PORT=6379
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
MAX_SAMPLE_COUNT=4
```

### 前端配置 (frontend/.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## 📊 状态码

| 状态 | 说明 |
|------|------|
| idle | 等待中 |
| running | 运行中 |
| collecting | 收集中 |
| completed | 已完成 |
| failed | 失败 |

## 🎨 组件说明

| 组件 | 功能 |
|------|------|
| SearchBox | 搜索框和任务创建 |
| TaskGrid | 任务列表展示 |
| TaskStatusBar | 底部状态栏 |
| ArtifactViewer | 结果查看器 |

## 📚 文档索引

- [README.md](README.md) - 项目总览
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构文档
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [frontend/README.md](frontend/README.md) - 前端文档
- [backend/README.md](backend/README.md) - 后端文档

## 💡 提示

1. **首次启动**: 使用 Docker Compose 最简单
2. **开发调试**: 手动启动可以看到详细日志
3. **生产部署**: 配置环境变量和 HTTPS
4. **性能优化**: 调整 Redis 和并发配置

## 🔗 相关链接

- Next.js 文档: https://nextjs.org/docs
- FastAPI 文档: https://fastapi.tiangolo.com
- Redis 文档: https://redis.io/docs
- Tailwind CSS: https://tailwindcss.com

## ⚡ 性能建议

- 前端: 使用 Next.js 图片优化
- 后端: 配置 Redis 连接池
- WebSocket: 限制消息频率
- 任务: 控制并发数量

## 🔒 安全提示

- 生产环境启用 HTTPS
- 配置 Redis 密码
- 限制 CORS 源
- 添加 API 认证
- 输入验证和清理

---

**快速帮助**: 遇到问题先查看日志文件
- 前端: `frontend/frontend.log`
- 后端: `backend/backend.log`
- Docker: `docker-compose logs`
