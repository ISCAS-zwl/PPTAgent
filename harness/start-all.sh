#!/bin/bash

echo "=========================================="
echo "  PPTAgent 前端和后台管理系统启动脚本"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✓ 检测到 Docker 和 Docker Compose"
    echo ""
    echo "选择启动方式："
    echo "1) 使用 Docker Compose 启动（推荐）"
    echo "2) 手动启动各个服务"
    read -p "请选择 (1/2): " choice

    if [ "$choice" = "1" ]; then
        echo ""
        echo "正在使用 Docker Compose 启动服务..."
        docker-compose up -d
        echo ""
        echo "✓ 服务启动成功！"
        echo ""
        echo "访问地址："
        echo "  - 前端: http://localhost:3000"
        echo "  - 后端 API: http://localhost:8000"
        echo "  - API 文档: http://localhost:8000/docs"
        echo ""
        echo "查看日志: docker-compose logs -f"
        echo "停止服务: docker-compose down"
        exit 0
    fi
fi

# 手动启动
echo ""
echo "手动启动服务..."
echo ""

# 检查 Redis
echo "1. 检查 Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    echo "   启动 Redis..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
        echo "   ✓ Redis 已启动"
    else
        echo "   ✗ Redis 未安装，请先安装 Redis"
        exit 1
    fi
else
    echo "   ✓ Redis 已运行"
fi

# 启动后端
echo ""
echo "2. 启动后端服务..."
cd backend
if [ ! -d "venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "   启动 FastAPI..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✓ 后端已启动 (PID: $BACKEND_PID)"
cd ..

# 启动前端
echo ""
echo "3. 启动前端服务..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   安装依赖..."
    npm install
fi

echo "   启动 Next.js..."
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✓ 前端已启动 (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "=========================================="
echo "✓ 所有服务启动成功！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 前端: http://localhost:3000"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "日志文件："
echo "  - 后端: backend/backend.log"
echo "  - 前端: frontend/frontend.log"
echo ""
echo "停止服务："
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
