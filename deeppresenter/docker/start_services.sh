#!/bin/bash
# 启动脚本：运行 DeepPresenter API 服务

set -e

# 设置 umask 确保文件权限
umask 000

# 同步 Python 依赖到挂载的项目目录
echo "Syncing Python dependencies..."
cd /usr/src/pptagent/deeppresenter
uv sync --quiet || echo "Warning: uv sync failed, continuing anyway..."

# 安装 Playwright 浏览器（如果尚未安装）
echo "Installing Playwright browsers..."
playwright install chromium --with-deps || true

echo "Starting DeepPresenter API server on port 4397..."
python -m deeppresenter.api_server 0.0.0.0 4397
