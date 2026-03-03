#!/bin/bash

# 启动 Redis (如果未运行)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# 启动 FastAPI 服务
echo "Starting FastAPI server..."
cd "$(dirname "$0")"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
