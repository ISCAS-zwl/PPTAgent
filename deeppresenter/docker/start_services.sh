#!/bin/bash
# 启动脚本：运行 DeepPresenter API 服务

set -e

# 设置 umask 确保文件权限
umask 000

# 安装 Playwright 浏览器（如果尚未安装）
echo "Installing Playwright browsers..."
playwright install chromium --with-deps || true

echo "Starting DeepPresenter API server on port 4397..."
python -m deeppresenter.api_server 0.0.0.0 4397
