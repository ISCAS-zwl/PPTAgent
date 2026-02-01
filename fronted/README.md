# PPTAgent 前端和后台管理系统

基于 plan.md 方案实现的 AI 任务管理平台，模仿 Manus 交互体验，支持任务异步后台执行、多样本并行采样以及独立 Artifact 渲染。

## 项目结构

```
fronted/
├── frontend/              # Next.js 前端应用
│   ├── app/              # Next.js App Router
│   ├── components/       # React 组件
│   ├── store/           # Zustand 状态管理
│   ├── types/           # TypeScript 类型
│   ├── lib/             # 工具函数
│   └── package.json
├── backend/              # FastAPI 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务服务
│   │   └── tasks/       # 任务处理
│   ├── requirements.txt
│   └── start.sh
├── docker-compose.yml    # Docker 编排
└── README.md            # 本文件
```

## 技术栈

### 前端
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS** - 样式框架
- **Framer Motion** - 动画效果
- **Zustand** - 状态管理
- **Lucide React** - 图标库
- **React Markdown** - Markdown 渲染
- **React Syntax Highlighter** - 代码高亮

### 后端
- **FastAPI** - Python Web 框架
- **WebSocket** - 实时通信
- **Redis** - 状态缓存
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器

## 核心功能

### ✅ Feature 1: 后台运行与状态管理
- 用户发起请求后无需等待，可关闭页面或切换任务
- 后端持续处理，通过 WebSocket 实时推送状态
- Redis 缓存任务状态，支持断线重连

### ✅ Feature 2: 多样本并行采样
- 同一个 Prompt 触发多个并发生成过程
- 使用 asyncio.gather 并行处理
- UI 上并行展示多个生成窗口
- 流式推送每个样本的生成内容

### ✅ Feature 3: Artifact 展示
- 独立面板渲染生成的代码、HTML 或数据图表
- 沙箱 iframe 安全渲染 HTML/JS
- 支持 Markdown、代码高亮显示
- 双栏布局：左侧聊天流，右侧动态渲染区

### ✅ Feature 4: PPTAgent 集成
- 集成现有 PPTAgent 功能
- 支持文档分析和 PPT 生成
- PPTEval 质量评估
- 模板和样式自定义

## 快速开始

### 方式 1: Docker Compose（推荐）

```bash
# 启动所有服务
cd /home/zhongwenliang2024/PPTAgent/fronted
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问：
- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 方式 2: 手动启动

#### 启动 Redis

```bash
redis-server
```

#### 启动后端

```bash
cd backend
pip install -r requirements.txt
./start.sh
# 或
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 启动前端

```bash
cd frontend
npm install
npm run dev
```

## 环境配置

### 后端环境变量 (backend/.env)

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

### 前端环境变量 (frontend/.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

## API 文档

### 创建任务

```bash
curl -X POST http://localhost:8000/api/task/create \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "创建一个关于人工智能的演示文稿",
    "sample_count": 2,
    "options": {
      "template": "modern",
      "style": "professional"
    }
  }'
```

### 获取任务详情

```bash
curl http://localhost:8000/api/task/{task_id}
```

### WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // 订阅任务更新
  ws.send(JSON.stringify({
    type: 'subscribe',
    task_id: 'your-task-id'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

## 使用指南

### 1. 创建任务

1. 在首页搜索框输入需求描述
2. 选择样本数量（1-4个）
3. 点击"生成"按钮

### 2. 查看进度

- 任务创建后自动显示在任务列表
- 实时显示生成进度和状态
- 底部状态栏显示后台运行的任务

### 3. 查看结果

- 点击任务卡片查看详情
- 右侧面板显示生成的 Artifact
- 支持代码/预览模式切换
- 可下载生成的内容

### 4. 多样本对比

- 创建任务时选择多个样本
- 并行生成多个版本
- 网格布局对比查看
- 选择最佳结果

## 开发指南

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 启动生产服务
npm start
```

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 开发模式（自动重载）
uvicorn app.main:app --reload

# 运行测试
pytest
```

### 添加新功能

#### 前端添加组件

在 `frontend/components/` 创建新组件：

```tsx
"use client";

export default function MyComponent() {
  return <div>My Component</div>;
}
```

#### 后端添加 API

在 `backend/app/api/` 创建新路由：

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/my-feature")

@router.get("/")
async def my_endpoint():
    return {"message": "Hello"}
```

## PPTAgent 集成

后端已集成 PPTAgent 功能，位于 `backend/app/services/pptagent_integration.py`。

### 使用示例

```python
from app.services.pptagent_integration import pptagent_integration

# 生成 PPT
result = await pptagent_integration.generate_ppt(
    prompt="创建一个关于 AI 的演示文稿",
    options={
        "template": "modern",
        "style": "professional"
    }
)

# 分析文档
analysis = await pptagent_integration.analyze_document(
    file_path="/path/to/document.pdf"
)

# 评估 PPT
evaluation = await pptagent_integration.evaluate_ppt(
    file_path="/path/to/presentation.pptx"
)
```

## 故障排除

### Redis 连接失败

```bash
# 检查 Redis 是否运行
redis-cli ping

# 启动 Redis
redis-server
```

### WebSocket 连接断开

- 检查 CORS 配置
- 确认防火墙设置
- 查看浏览器控制台错误

### 前端构建失败

```bash
# 清理缓存
rm -rf .next node_modules
npm install
npm run build
```

### 后端启动失败

```bash
# 检查 Python 版本（需要 3.11+）
python --version

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

## 性能优化

### 前端优化

- 使用 Next.js 图片优化
- 启用增量静态生成
- 代码分割和懒加载
- 使用 React.memo 避免重渲染

### 后端优化

- Redis 连接池
- 异步任务队列
- 并发限制
- 缓存策略

## 部署

### 生产环境部署

```bash
# 使用 Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 或使用 Kubernetes
kubectl apply -f k8s/
```

### 环境变量配置

生产环境需要配置：
- Redis 密码
- CORS 白名单
- API 密钥
- 日志级别

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

参考项目根目录的 LICENSE 文件。

## 联系方式

- 项目地址: https://github.com/your-repo/PPTAgent
- 问题反馈: https://github.com/your-repo/PPTAgent/issues

## 致谢

- 基于 [PPTAgent](https://arxiv.org/abs/2501.03936) 论文实现
- 参考 Manus 的交互设计
- 使用 Next.js、FastAPI 等优秀开源项目
